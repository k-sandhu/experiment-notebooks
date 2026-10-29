import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser

# FetchError is assumed to be defined elsewhere; we only use fetch
def extract(fetch, listing_url):
    # Fetch listing page
    listing_html = fetch(listing_url)
    soup = BeautifulSoup(listing_html, "html.parser")
    
    # Find all news-row list items
    news_rows = soup.find_all("li", class_="news-row")
    records = []
    
    for row in news_rows:
        # Get link
        link_tag = row.find("a", href=True)
        if not link_tag:
            continue
        rel_url = link_tag["href"]
        abs_url = urllib.parse.urljoin(listing_url, rel_url)
        
        # Fetch release page
        release_html = fetch(abs_url)
        release_soup = BeautifulSoup(release_html, "html.parser")
        
        # Title: h1 inside news-header or first strong? Use h1 within news-header
        header = release_soup.find("div", class_="news-header")
        title_elem = None
        if header:
            title_elem = header.find(["h1", "h2", "h3"])
        if not title_elem:
            # fallback to first heading
            title_elem = release_soup.find(["h1", "h2", "h3"])
        if title_elem:
            title = title_elem.get_text(strip=True)
        else:
            # fallback to link text
            title = link_tag.get_text(strip=True)
        
        # Date: time element with datetime attribute
        time_elem = release_soup.find("time", {"datetime": True})
        date_str = None
        if time_elem:
            dt = time_elem["datetime"]
            # dt format like "2026-09-30T15:15:00Z"
            try:
                date_obj = parser.parse(dt)
                date_str = date_obj.strftime("%Y-%m-%d")
            except Exception:
                pass
        # fallback: parse from title? Not needed
        
        # Author: .news-byline -> "By Mara Fenwick" -> extract name after "By "
        byline_elem = release_soup.find("p", class_="news-byline")
        author_raw = None
        if byline_elem:
            author_raw = byline_elem.get_text(strip=True)
        # Remove "By " prefix and any job titles? simple: split after "By "
        if author_raw and author_raw.startswith("By "):
            author_raw = author_raw[3:].strip()
        # Remove trailing job titles? Not required precise; just keep name(s)
        # If multiple names with "and"? Assume simple.
        # Clean: remove words like "By", "and"? We'll keep as is but remove "By " prefix.
        # Also remove trailing punctuation? We'll keep.
        # If no byline, author = None
        if author_raw:
            # Remove possible trailing commas or periods? simple strip
            author = author_raw.strip()
        else:
            author = None
        
        # Body: .news-body paragraphs
        body_div = release_soup.find("div", class_="news-body")
        body_paragraphs = []
        if body_div:
            # get all p inside body_div
            paras = body_div.find_all("p")
            for p in paras:
                # get text, preserve line breaks? separate by blank line
                text = p.get_text(separator="\n", strip=True)
                if text:  # skip empty
                    body_paragraphs.append(text.strip())
        body_text = "\n\n".join(body_paragraphs) if body_paragraphs else ""
        
        # Build record
        record = {
            "url": abs_url,
            "title": title,
            "date": date_str if date_str else None,  # but must be string; fallback? maybe parse from time title? We'll use date_str else None not allowed? spec says date as YYYY-MM-DD; if missing maybe None? Assume present.
            "author": author if author else None,
            "body": body_text
        }
        # Ensure date is string; if None, maybe extract from time title? fallback: parse from time element without datetime? Use time element's title? Not reliable. We'll keep date_str.
        if record["date"] is None:
            # try parse from time element's title attribute
            time_elem = release_soup.find("time")
            if time_elem and time_elem.get("title"):
                try:
                    dt = parser.parse(time_elem["title"])
                    record["date"] = dt.strftime("%Y-%m-%d")
                except Exception:
                    pass
        
        records.append(record)
    
    # Sort newest first: date descending
    def get_date_key(rec):
        d = rec["date"]
        if d and isinstance(d, str) and len(d) == 10 and d.count("-") == 2:
            try:
                return parser.parse(d)
            except Exception:
                return parser.parse("1900-01-01")
        return parser.parse("1900-01-01")
    
    records.sort(key=get_date_key, reverse=True)
    
    return records
