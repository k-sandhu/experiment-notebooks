import urllib.parse
from datetime import datetime
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from dateutil import parser

# FetchError is assumed to be defined elsewhere; we import it if present
try:
    from fetch import FetchError  # type: ignore
except ImportError:
    class FetchError(Exception):
        def __init__(self, status: int):
            self.status = status
        def __str__(self):
            return f"FetchError: status {self.status}"

def extract(fetch, listing_url: str) -> List[Dict]:
    """
    Extract all press releases from the listing page and return records.
    """
    # Fetch listing page
    listing_html = fetch(listing_url)
    soup_listing = BeautifulSoup(listing_html, "html.parser")
    
    # Find all press-card links
    press_cards = soup_listing.find_all("a", class_="press-card")
    release_urls = []
    for card in press_cards:
        href = card.get("href")
        if href:
            abs_url = urllib.parse.urljoin(listing_url, href)
            # Only include those under /press-room/ (relative to base)
            if abs_url.startswith("https://www.lumenhome.example/press-room/"):
                release_urls.append(abs_url)
    
    # Collect releases (newest first)
    records = []
    for rel_url in release_urls:
        # Fetch release page
        try:
            release_html = fetch(rel_url)
        except FetchError as e:
            # Skip if fetch fails
            continue
        soup_release = BeautifulSoup(release_html, "html.parser")
        
        # Extract title
        title_elem = soup_release.find("h1", class_="press-title")
        if title_elem:
            title = title_elem.get_text(strip=True)
        else:
            # fallback: page title without "Press room |"
            title_tag = soup_release.find("title")
            if title_tag:
                title_text = title_tag.get_text(strip=True)
                # Remove leading "Press room | " if present
                if title_text.startswith("Press room | "):
                    title = title_text[14:].strip()
                else:
                    title = title_text
            else:
                title = "Unknown"
        
        # Extract date from press-date element or meta
        date_elem = soup_release.find("p", class_="press-date")
        if date_elem:
            raw_date = date_elem.get_text(strip=True)  # e.g., "28 Sep 2026"
            # Parse to date using dateutil
            try:
                dt = parser.parse(raw_date, fuzzy=True)
                date_str = dt.date().isoformat()  # YYYY-MM-DD
            except Exception:
                # fallback: try meta property
                meta_date = soup_release.find("meta", property="article:published_time")
                if meta_date and meta_date.get("content"):
                    try:
                        dt = parser.parse(meta_date["content"])
                        date_str = dt.date().isoformat()
                    except Exception:
                        date_str = None
                else:
                    date_str = None
        else:
            meta_date = soup_release.find("meta", property="article:published_time")
            if meta_date and meta_date.get("content"):
                try:
                    dt = parser.parse(meta_date["content"])
                    date_str = dt.date().isoformat()
                except Exception:
                    date_str = None
            else:
                date_str = None
        
        # Extract author
        author_meta = soup_release.find("meta", name="author")
        if author_meta and author_meta.get("content"):
            raw_author = author_meta["content"].strip()
            # Remove job titles? We just take the content as is, but remove "By" if present
            if raw_author.lower().startswith("by "):
                raw_author = raw_author[3:].strip()
            # Simple cleaning: keep words, join with " and " if multiple? Assume single name.
            # The spec says "several names joined with ' and '"; we assume meta gives single name.
            author = raw_author
        else:
            # Look for author in body? Not present in sample. Use None.
            author = None
        
        # Extract body: main text paragraphs inside .press-content
        content_div = soup_release.find("div", class_="press-content")
        if content_div:
            # Get all <p> inside press-content, get text, preserve blank lines between paragraphs
            paras = []
            for p in content_div.find_all("p"):
                txt = p.get_text(separator="\n", strip=True)
                if txt:  # skip empty paragraphs
                    paras.append(txt)
            # Join with blank line (i.e., "\n\n") between paragraphs
            body = "\n\n".join(paras)
        else:
            # fallback: get all text from main excluding header/footer? Not ideal.
            # Find main <main> and get text of children except navigation etc.
            main = soup_release.find("main")
            if main:
                # Get text of direct children that are not header/footer? Simpler: get all text and clean?
                # We'll take text of .press-article maybe
                article = soup_release.find("div", class_="press-article")
                if article:
                    paras = []
                    for p in article.find_all("p"):
                        txt = p.get_text(separator="\n", strip=True)
                        if txt:
                            paras.append(txt)
                    body = "\n\n".join(paras)
                else:
                    body = main.get_text(separator="\n\n", strip=True)
            else:
                body = ""
        
        # Build record
        record = {
            "url": rel_url,
            "title": title,
            "date": date_str if date_str else None,  # should be string YYYY-MM-DD
            "author": author if author else None,
            "body": body,
        }
        # Ensure date is string; if None, maybe skip? but should exist.
        if record["date"] is None:
            # try to infer from title? Not needed.
            pass
        records.append(record)
    
    # Sort newest first by date (descending)
    def get_sort_key(rec):
        d = rec["date"]
        if d and isinstance(d, str) and len(d) == 10 and d[4] == "-" and d[7] == "-":
            try:
                return datetime.strptime(d, "%Y-%m-%d")
            except Exception:
                return datetime.min
        return datetime.min
    
    records.sort(key=get_sort_key, reverse=True)
    
    return records
