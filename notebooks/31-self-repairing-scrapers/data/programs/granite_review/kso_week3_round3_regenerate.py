import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser
from typing import List, Dict, Optional

# Assume FetchError is defined elsewhere; we only use fetch as provided

def extract(fetch, listing_url: str) -> List[Dict]:
    """
    Extract all news releases from the Kestria Statistics Office releases listing.
    Returns a list of dicts with keys: url, title, date, author, body, newest first.
    """
    # Fetch listing page
    listing_html = fetch(listing_url)
    soup_listing = BeautifulSoup(listing_html, "html.parser")
    
    # Find all card elements that contain release links
    cards = soup_listing.find_all("div", class_="card")
    records = []
    
    for card in cards:
        # Extract link href
        title_a = card.find("a", class_="card__title")
        if not title_a or not title_a.get("href"):
            continue
        rel_url = title_a["href"]
        abs_url = urllib.parse.urljoin(listing_url, rel_url)
        
        # Fetch release page
        try:
            release_html = fetch(abs_url)
        except Exception:  # FetchError may be raised by fetch
            continue
        soup_release = BeautifulSoup(release_html, "html.parser")
        
        # Extract title (h1 inside article header)
        h1 = soup_release.find("h1")
        title = h1.get_text(strip=True) if h1 else ""
        
        # Extract date from content__meta span.content__date
        meta_div = soup_release.find("div", class_="content__meta")
        date_span = meta_div.find("span", class_="content__date") if meta_div else None
        date_text = date_span.get_text(strip=True) if date_span else ""
        
        # Parse date: expected format like "22 September 2026"
        try:
            date_parsed = parser.parse(date_text)
            date_str = date_parsed.strftime("%Y-%m-%d")
        except Exception:
            # fallback: try to extract numeric date if format differs
            # but based on sample, use parser
            date_str = ""
        
        # Extract author: span.content__author, ignore role
        author_span = meta_div.find("span", class_="content__author") if meta_div else None
        if author_span:
            # Get text, e.g., "Elian Corven"
            raw_author = author_span.get_text(strip=True)
            # Remove any trailing role text? role is in separate span, not same
            # So raw_author should be just author name
            author = raw_author
        else:
            author = None
        
        # Extract body: section.content__body paragraphs
        body_section = soup_release.find("section", class_="content__body")
        body_paragraphs = []
        if body_section:
            # Get all paragraphs
            paras = body_section.find_all("p")
            for p in paras:
                # Get text, preserve line breaks? We'll join with '\n\n'
                text = p.get_text(separator="\n", strip=True)
                if text:
                    body_paragraphs.append(text.strip())
            body = "\n\n".join(body_paragraphs)
        else:
            # fallback: get text from article body? but spec says main text
            body = ""
        
        record = {
            "url": abs_url,
            "title": title,
            "date": date_str,
            "author": author if author else None,
            "body": body
        }
        records.append(record)
    
    # Sort newest first by date (descending)
    # Use date_str for sorting; ensure valid dates
    def sort_key(r):
        d = r["date"]
        try:
            return parser.parse(d)
        except Exception:
            return parser.parse("1900-01-01")
    
    records.sort(key=sort_key, reverse=True)
    return records
