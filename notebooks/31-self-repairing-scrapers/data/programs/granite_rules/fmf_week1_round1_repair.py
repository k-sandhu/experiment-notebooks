import urllib.parse
from datetime import datetime
from dateutil import parser
from bs4 import BeautifulSoup

# FetchError is assumed to be defined elsewhere; we only reference it.

def extract(fetch, listing_url):
    """
    Extract all news releases from the listing page and return records.
    
    Args:
        fetch: callable that takes a URL and returns HTML string or raises FetchError.
        listing_url: absolute URL of the listing page.
    
    Returns:
        List[dict] with keys: url, title, date, author, body. Newest first.
    """
    # Fetch listing page
    listing_html = fetch(listing_url)
    soup_listing = BeautifulSoup(listing_html, "html.parser")
    
    # Find all media-item elements that contain NewsArticle schema
    media_items = soup_listing.find_all("div", class_="media-item")
    records = []
    
    for item in media_items:
        # Extract relative href from the <a> tag inside the media-item
        link_tag = item.find("a", itemprop="url")
        if not link_tag:
            continue
        rel_url = link_tag.get("href")
        if not rel_url:
            continue
        abs_url = urllib.parse.urljoin(listing_url, rel_url)
        
        # Get headline from <span itemprop="headline">
        headline_tag = item.find("span", itemprop="headline")
        if headline_tag:
            title = headline_tag.get_text(strip=True)
        else:
            # fallback: link text
            title = link_tag.get_text(strip=True)
        
        # Extract datePublished meta
        date_meta = item.find("meta", itemprop="datePublished")
        date_str = None
        if date_meta and date_meta.get("content"):
            pub_content = date_meta["content"]
            try:
                dt = parser.parse(pub_content)
                date_str = dt.date().isoformat()  # YYYY-MM-DD
            except Exception:
                # fallback: extract YYYY-MM-DD pattern
                import re
                match = re.search(r"\d{4}-\d{2}-\d{2}", pub_content)
                if match:
                    date_str = match.group()
        
        # Extract author from listing byline if present
        author = None
        byline_div = item.find("div", class_="byline")
        if byline_div:
            # Look for itemprop="author" Person inside
            author_meta = byline_div.find("span", itemprop="Person")
            if author_meta:
                name_tag = author_meta.find("span", itemprop="name")
                if name_tag:
                    name = name_tag.get_text(strip=True)
                    # Remove possible "·" separator and "Media centre ·" prefix
                    if "·" in name:
                        parts = name.split("·")
                        name = parts[-1].strip()
                    author = name
        
        # Fetch release page
        try:
            release_html = fetch(abs_url)
        except Exception:
            # skip if fetch fails
            continue
        soup_release = BeautifulSoup(release_html, "html.parser")
        
        # Extract title from <h1 itemprop="headline"> (overwrites listing title if needed)
        h1 = soup_release.find("h1", itemprop="headline")
        if h1:
            title = h1.get_text(strip=True)
        
        # Extract datePublished from release page meta (more reliable)
        release_date_meta = soup_release.find("meta", itemprop="datePublished")
        if not date_str and release_date_meta and release_date_meta.get("content"):
            pub_content = release_date_meta["content"]
            try:
                dt = parser.parse(pub_content)
                date_str = dt.date().isoformat()
            except Exception:
                pass
        
        # Extract author from release page byline if not already set
        if not author:
            byline_div = soup_release.find("div", class_="byline")
            if byline_div:
                author_meta = byline_div.find("span", itemprop="Person")
                if author_meta:
                    name_tag = author_meta.find("span", itemprop="name")
                    if name_tag:
                        name = name_tag.get_text(strip=True)
                        if "·" in name:
                            parts = name.split("·")
                            name = parts[-1].strip()
                        author = name
        
        # Extract body from itemprop="articleBody"
        body_tag = soup_release.find("div", itemprop="articleBody")
        body_text = ""
        if body_tag:
            paragraphs = body_tag.find_all("p")
            for p in paragraphs:
                txt = p.get_text(separator="\n", strip=True)
                if txt:
                    body_text += txt + "\n\n"
            if body_text.endswith("\n\n"):
                body_text = body_text[:-2]
        else:
            # fallback: find all <p> inside article
            article = soup_release.find("article", itemprop="NewsArticle")
            if article:
                paras = article.find_all("p")
                for p in paras:
                    txt = p.get_text(separator="\n", strip=True)
                    if txt:
                        body_text += txt + "\n\n"
                if body_text.endswith("\n\n"):
                    body_text = body_text[:-2]
        
        # Normalize date string to YYYY-MM-DD
        final_date = None
        if date_str:
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
                final_date = date_str
            except ValueError:
                try:
                    dt = parser.parse(date_str)
                    final_date = dt.date().isoformat()
                except Exception:
                    pass
        
        # If still no date, try release meta again
        if not final_date and release_date_meta and release_date_meta.get("content"):
            pub_content = release_date_meta["content"]
            try:
                dt = parser.parse(pub_content)
                final_date = dt.date().isoformat()
            except Exception:
                pass
        
        # If still no date, fallback to listing date_str (already parsed)
        if not final_date:
            final_date = date_str
        
        # Build record
        record = {
            "url": abs_url,
            "title": title,
            "date": final_date,
            "author": author if author else None,
            "body": body_text if body_text else "",
        }
        records.append(record)
    
    # Sort newest first by date
    def get_sort_key(rec):
        date_str = rec["date"]
        if not date_str:
            return ""
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except Exception:
            return ""
    
    records.sort(key=get_sort_key, reverse=True)
    return records
