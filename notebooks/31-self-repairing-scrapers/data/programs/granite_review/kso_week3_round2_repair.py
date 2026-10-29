import urllib.parse
from datetime import date
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from dateutil import parser

# FetchError is assumed to be defined elsewhere; we import it if available
try:
    from fetch import FetchError
except ImportError:
    class FetchError(Exception):
        def __init__(self, status: int):
            self.status = status
        def __str__(self):
            return f"FetchError: {self.status}"

def extract(fetch, listing_url: str) -> List[Dict]:
    """
    Extract all news release records from the Kestria Statistics Office releases listing.
    Returns a list of dicts, newest first, each containing:
    - url: absolute URL of the release page
    - title: full headline as plain text
    - date: publication date as "YYYY-MM-DD"
    - author: names joined with " and ", without titles/jargon, or None
    - body: full main text as plain text (paragraphs separated by blank lines)
    """
    # Fetch listing page
    listing_html = fetch(listing_url)
    soup = BeautifulSoup(listing_html, "html.parser")
    
    # Find all cards in the listing
    cards = soup.find_all("div", class_="card")
    records = []
    
    for card in cards:
        # Extract link
        link_tag = card.find("a", href=True)
        if not link_tag:
            continue
        rel_url = link_tag["href"]
        abs_url = urllib.parse.urljoin(listing_url, rel_url)
        
        # Get title from h3 > a text
        title_tag = card.find("h3", class_="card__title")
        if title_tag and title_tag.find("a"):
            title = title_tag.find("a").get_text(strip=True)
        else:
            # fallback
            title = link_tag.get_text(strip=True)
        
        # Extract date from card__date (format DD/MM/YYYY)
        listing_dt = None
        date_tag = card.find("span", class_="card__date")
        if date_tag:
            date_text = date_tag.get_text(strip=True)
            try:
                dt = parser.parse(date_text, dayfirst=True)
                listing_dt = dt.date()
            except Exception:
                pass
        
        # Fetch release page
        release_html = fetch(abs_url)
        release_soup = BeautifulSoup(release_html, "html.parser")
        
        # Extract title from <h1>
        title_elem = release_soup.find("h1")
        if title_elem:
            title = title_elem.get_text(strip=True)
        
        # Extract publication date from <span class="content__date">
        pub_date = None
        meta_div = release_soup.find("div", class_="content__meta")
        if meta_div:
            date_span = meta_div.find("span", class="content__date")
            if date_span:
                date_text = date_span.get_text(strip=True)  # "22 September 2026"
                try:
                    dt = parser.parse(date_text)
                    pub_date = dt.date()
                except Exception:
                    pass
        
        # Extract author from <span class="content__author">
        author = None
        author_span = meta_div.find("span", class="content__author") if meta_div else None
        if author_span:
            raw_author = author_span.get_text(strip=True)  # "Elian Corven"
            parts = raw_author.split("·")
            author_part = parts[0].strip().rstrip(",.")
            # Clean trailing punctuation
            author_part = author_part.rstrip(".")
            author = author_part
        
        # Normalize date string
        date_str = None
        if pub_date:
            date_str = pub_date.strftime("%Y-%m-%d")
        elif listing_dt:
            date_str = listing_dt.strftime("%Y-%m-%d")
        
        # Extract body from <section class="content__body">
        body_section = release_soup.find("section", class_="content__body")
        body_text_parts = []
        if body_section:
            paras = body_section.find_all("p")
            for p in paras:
                txt = p.get_text(separator="\n", strip=False)
                if txt.strip():
                    body_text_parts.append(txt.strip())
            body = "\n\n".join(body_text_parts)
        else:
            article = release_soup.find("article", class_="content")
            if article:
                paras = article.find_all("p")
                body_text_parts = [p.get_text(strip=True) for p in paras if p.get_text(strip=True)]
                body = "\n\n".join(body_text_parts)
            else:
                body = ""
        
        # Build record (only if date present)
        record = {
            "url": abs_url,
            "title": title,
            "date": date_str,
            "author": author,
            "body": body
        }
        if record["date"]:
            records.append(record)
    
    # Sort newest first by pub_date from release page (most reliable)
    def get_date(rec):
        d = rec["date"]
        if d and isinstance(d, str):
            try:
                return parser.parse(d).date()
            except Exception:
                return date.min
        return date.min
    
    records.sort(key=get_date, reverse=True)
    return records
