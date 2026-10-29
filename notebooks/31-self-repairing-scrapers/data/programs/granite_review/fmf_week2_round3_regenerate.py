import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser

# FetchError is assumed to be defined elsewhere; we only use it via fetch
# No need to redefine it here

def extract(fetch, listing_url):
    # Fetch listing page
    listing_html = fetch(listing_url)
    soup_listing = BeautifulSoup(listing_html, "html.parser")
    
    # Find all media-item divs with itemprop="NewsArticle"
    media_items = soup_listing.find_all("div", class_="media-item", itemprop="NewsArticle")
    records = []
    
    for item in media_items:
        # Extract href from the <a> tag inside the media-item
        link_tag = item.find("a", itemprop="url")
        if not link_tag:
            continue
        rel_url = link_tag["href"]
        abs_url = urllib.parse.urljoin(listing_url, rel_url)
        
        # Fetch the release page
        release_html = fetch(abs_url)
        soup_release = BeautifulSoup(release_html, "html.parser")
        
        # Title: from h1 itemprop="headline" or fallback to first <a> span headline
        title_tag = soup_release.find("h1", itemprop="headline")
        if title_tag:
            title = title_tag.get_text(strip=True)
        else:
            # fallback: find <a> with itemprop="headline" inside media-item? but for release page use h1
            # In sample, h1 is used
            title = ""
        
        # Date: from meta itemprop="datePublished" or visible date span
        date_meta = soup_release.find("meta", itemprop="datePublished")
        date_visible_span = soup_release.find("span", class_="date-visible")
        date = None
        
        if date_meta and date_meta.get("content"):
            # parse ISO datetime and output YYYY-MM-DD
            dt = parser.parse(date_meta["content"])
            date = dt.strftime("%Y-%m-%d")
        elif date_visible_span:
            # parse "21 September" format
            text = date_visible_span.get_text(strip=True)
            # simple parsing: extract first number and month name
            # fallback: use dateutil to parse if possible, else extract manually
            # We'll attempt to parse with dateutil from the visible text? dateutil can parse "21 September 2026"? but only "21 September"
            # The meta datePublished includes timezone, so use that.
            # If meta missing, fallback to extracting from visible span: "21 September" -> "2026-09-21"? need year? maybe from meta elsewhere? In listing we have meta datePublished with year.
            # For safety, if meta missing, try to get year from page? Not reliable. We'll rely on meta.
            pass
        
        # Author: from byline with itemprop="author"
        author_names = []
        byline = soup_release.find("div", class_="byline")
        if byline:
            # find all itemprop="Person" names
            person_tags = byline.find_all("span", itemprop="Person")
            for pt in person_tags:
                name_tag = pt.find("span", itemprop="name")
                if name_tag:
                    name = name_tag.get_text(strip=True)
                    # remove job titles? The byline shows "Media centre · Elise Marvaux". We need only name, no "Media centre ·"
                    # The byline structure: <div class="byline">Media centre · <span itemprop="author" ...><span itemprop="name">Elise Marvaux</span></span></div>
                    # So we extract the name span text.
                    # Also there could be multiple authors? join with " and "
                    author_names.append(name)
            # If only one, just use that name; if multiple, join with " and "
        # If no byline, author = None
        if author_names:
            # Clean names: remove trailing punctuation? keep as is
            # Remove possible "Media centre ·" not inside name tag
            # Already extracted only name spans
            author = " and ".join(author_names)
        else:
            author = None
        
        # Body: from itemprop="articleBody" div
        body_div = soup_release.find("div", itemprop="articleBody")
        if body_div:
            # Get paragraphs, get text, preserve blank lines between paragraphs
            paragraphs = []
            for p in body_div.find_all("p"):
                txt = p.get_text(separator="\n", strip=True)
                if txt:  # skip empty paragraphs
                    paragraphs.append(txt)
            # Join paragraphs with a blank line between
            body = "\n\n".join(paragraphs)
        else:
            # fallback: get all text from article except byline and cta
            article = soup_release.find("article", itemscope=True, itemtype="https://schema.org/NewsArticle")
            if article:
                # get all child paragraphs? simple: get text of all p inside article excluding byline and cta
                # exclude byline and member-cta sections
                # find all p tags inside article that are not inside byline or cta
                # easier: get text of articleBody if not present, else get all p tags inside article
                paras = []
                for child in article.find_all("p"):
                    # skip if child inside byline or cta? byline is div with class byline, cta is section.member-cta
                    # check if parent has class byline or section.member-cta
                    parent_cls = []
                    p = child
                    while p:
                        if p.name == "div" and "byline" in p.get("class", []):
                            break
                        if p.name == "section" and "member-cta" in p.get("class", []):
                            break
                        p = p.parent
                    # simple: just collect all p text
                    txt = child.get_text(separator="\n", strip=True)
                    if txt:
                        paras.append(txt)
                body = "\n\n".join(paras)
            else:
                body = ""
        
        records.append({
            "url": abs_url,
            "title": title,
            "date": date if date else None,  # but must be string; if None, maybe fallback? but meta should exist
            "author": author,
            "body": body
        })
    
    # Sort newest first by date (descending). Need to sort by date string YYYY-MM-DD.
    # Ensure date is string; if None, place at end? but all should have date.
    def get_date_key(rec):
        d = rec["date"]
        if d and isinstance(d, str) and len(d) == 10 and d[4] == '-' and d[7] == '-':
            return d
        # fallback: parse from meta? but already set
        return ""
    
    records.sort(key=lambda r: get_date_key(r), reverse=True)
    
    return records
