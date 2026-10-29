import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser

# FetchError is assumed to be defined elsewhere; we only use it via fetch

def extract(fetch, listing_url):
    # Fetch listing page
    listing_html = fetch(listing_url)
    soup_listing = BeautifulSoup(listing_html, "html.parser")
    
    # Find all media-item divs
    media_items = soup_listing.find_all("div", class_="media-item")
    records = []
    
    for item in media_items:
        # Check if it has itemprop="NewsArticle"
        if not item.get("itemprop", "").startswith("NewsArticle"):
            continue
        
        # Extract href from the <a> tag inside the media-item
        link_tag = item.find("a", itemprop="url")
        if not link_tag or "href" not in link_tag.attrs:
            continue
        rel_url = link_tag["href"]
        abs_url = urllib.parse.urljoin(listing_url, rel_url)
        
        # Fetch the release page
        try:
            release_html = fetch(abs_url)
        except Exception:  # FetchError may be raised by fetch
            continue
        soup_release = BeautifulSoup(release_html, "html.parser")
        
        # Title: from h1 itemprop="headline"
        title_tag = soup_release.find("h1", itemprop="headline")
        if title_tag:
            title = title_tag.get_text(strip=True)
        else:
            # fallback: find <a> with itemprop="headline" inside media-item? but for release page use h1
            # In sample, h1 is used
            title = ""
            if not title:
                # try to get from <a> inside media-item? not needed
                pass
        
        # Date: from meta itemprop="datePublished"
        date_meta = soup_release.find("meta", itemprop="datePublished")
        date = None
        if date_meta and date_meta.get("content"):
            try:
                dt = parser.parse(date_meta["content"])
                date = dt.strftime("%Y-%m-%d")
            except Exception:
                pass
        
        # Author: from byline with itemprop="author"
        author = None
        byline = soup_release.find("div", class_="byline")
        if byline:
            # find all itemprop="Person" name spans
            person_tags = byline.find_all("span", itemprop="Person")
            author_names = []
            for pt in person_tags:
                name_tag = pt.find("span", itemprop="name")
                if name_tag:
                    name = name_tag.get_text(strip=True)
                    # Remove trailing punctuation like period? keep as is
                    author_names.append(name)
            if author_names:
                # Join with " and " if multiple
                if len(author_names) == 1:
                    author = author_names[0]
                else:
                    author = " and ".join(author_names)
        
        # Body: from itemprop="articleBody" div
        body = ""
        body_div = soup_release.find("div", itemprop="articleBody")
        if body_div:
            paragraphs = []
            for p in body_div.find_all("p"):
                txt = p.get_text(separator="\n", strip=True)
                if txt:  # skip empty paragraphs
                    paragraphs.append(txt)
            body = "\n\n".join(paragraphs)
        else:
            # fallback: get article element and extract paragraphs
            article = soup_release.find("article", itemscope=True, itemtype="https://schema.org/NewsArticle")
            if article:
                paragraphs = []
                for p in article.find_all("p"):
                    # skip paragraphs inside byline or member-cta
                    parent = p.parent
                    skip = False
                    while parent:
                        if parent.name == "div" and "byline" in parent.get("class", []):
                            skip = True
                            break
                        if parent.name == "section" and "member-cta" in parent.get("class", []):
                            skip = True
                            break
                        parent = parent.parent
                    if not skip:
                        txt = p.get_text(separator="\n", strip=True)
                        if txt:
                            paragraphs.append(txt)
                body = "\n\n".join(paragraphs)
        
        records.append({
            "url": abs_url,
            "title": title,
            "date": date if date else None,
            "author": author,
            "body": body
        })
    
    # Sort newest first by date (descending). Only sort valid dates; None dates go last.
    def get_date_key(rec):
        d = rec["date"]
        if isinstance(d, str) and len(d) == 10 and d[4] == '-' and d[7] == '-':
            return d
        return ""  # will sort after valid dates
    
    records.sort(key=lambda r: get_date_key(r), reverse=True)
    
    return records
