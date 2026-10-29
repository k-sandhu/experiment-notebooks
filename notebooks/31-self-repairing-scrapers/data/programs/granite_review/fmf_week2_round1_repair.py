import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser

# FetchError is assumed to be defined elsewhere; we only reference it

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
        
        # Extract href from the <a> tag inside
        link_tag = item.find("a", itemprop="url")
        if not link_tag or "href" not in link_tag.attrs:
            continue
        rel_url = link_tag["href"]
        abs_url = urllib.parse.urljoin(listing_url, rel_url)
        
        # Get title from span with itemprop="headline"
        title_tag = item.find("span", itemprop="headline")
        if not title_tag:
            continue
        title = title_tag.get_text(strip=True)
        
        # Get datePublished from meta itemprop="datePublished"
        date_meta = item.find("meta", itemprop="datePublished")
        if not date_meta or not date_meta.get("content"):
            continue
        date_str = date_meta["content"]
        try:
            dt = parser.parse(date_str)
            date = dt.date().isoformat()  # "YYYY-MM-DD"
        except Exception:
            continue
        
        # Fetch release page
        try:
            release_html = fetch(abs_url)
        except Exception:
            continue
        soup_release = BeautifulSoup(release_html, "html.parser")
        
        # Extract author from byline with itemprop="author"
        author_names = []
        # Find article with itemprop="NewsArticle"
        article = soup_release.find("article", itemprop="NewsArticle")
        if article:
            # Collect all author names from itemprop="author" Person elements
            for author_elem in article.find_all(itemprop="author"):
                name_tag = author_elem.find(itemprop="name")
                if name_tag:
                    raw_name = name_tag.get_text(strip=True)
                    # Filter out generic text like "Media centre"
                    if raw_name != "Media centre":
                        # Simple filter: if it contains "·" maybe part of byline, but author elem should be clean
                        # Keep raw_name as is
                        author_names.append(raw_name)
        
        # If no author via schema, fallback to byline div
        if not author_names:
            byline_div = soup_release.find("div", class_="byline")
            if byline_div:
                # Look for itemprop="Person" inside byline
                for person_elem in byline_div.find_all(itemprop="Person"):
                    name_tag = person_elem.find(itemprop="name")
                    if name_tag:
                        raw_name = name_tag.get_text(strip=True)
                        if raw_name != "Media centre":
                            author_names.append(raw_name)
        
        # Deduplicate while preserving order (simple list unique)
        seen = set()
        unique_names = []
        for name in author_names:
            if name not in seen:
                seen.add(name)
                unique_names.append(name)
        if unique_names:
            author = " and ".join(unique_names)
        else:
            author = None
        
        # Extract body from itemprop="articleBody"
        body_div = soup_release.find("div", itemprop="articleBody")
        if body_div:
            paragraphs = []
            for p in body_div.find_all("p"):
                text = p.get_text(separator="\n", strip=True)
                if text:  # avoid empty paragraphs
                    paragraphs.append(text)
            body = "\n\n".join(paragraphs)
        else:
            # Fallback: get text from article children excluding header/footer? Not reliable, but try simple
            article_body = soup_release.find("article")
            if article_body:
                # Get all text from article, then clean? Too complex; skip if no articleBody
                body = article_body.get_text(separator="\n\n", strip=False)
            else:
                body = ""
        
        records.append({
            "url": abs_url,
            "title": title,
            "date": date,
            "author": author,
            "body": body
        })
    
    # Sort newest first by date (string YYYY-MM-DD sorts lexicographically)
    records.sort(key=lambda x: x["date"], reverse=True)
    return records
