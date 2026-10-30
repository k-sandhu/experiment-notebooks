import urllib.parse
from datetime import datetime
from typing import List, Dict
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
    listing_html = fetch(listing_url)
    soup = BeautifulSoup(listing_html, "html.parser")
    
    # Find all cards in the listing
    cards = soup.find_all("div", class_="card")
    records = []
    
    for card in cards:
        # Extract link from .card__title <a>
        title_a = card.find("h3", class_="card__title")
        if not title_a:
            continue
        link_tag = title_a.find("a", href=True)
        if not link_tag or "href" not in link_tag.attrs:
            continue
        rel_url = link_tag["href"]
        abs_url = urllib.parse.urljoin(listing_url, rel_url)
        
        # Get title from link text
        link_text = link_tag.get_text(strip=True)
        
        # Fetch release page
        release_html = fetch(abs_url)
        release_soup = BeautifulSoup(release_html, "html.parser")
        
        # Extract title from <h1>
        title_elem = release_soup.find("h1")
        if title_elem:
            title = title_elem.get_text(strip=True)
        else:
            title = link_text
        
        # Extract publication date from <span class="content__date"> or <time>
        date_elem = release_soup.find("span", class_="content__date")
        pubdate_tag = release_soup.find("time", class_="content__date")  # not time tag; actually span
        # Actually date is inside <span class="content__date"> with text like "22 September 2026"
        # Use span with class content__date
        if date_elem:
            date_text = date_elem.get_text(strip=True)  # "22 September 2026"
            try:
                # dateutil can parse "22 September 2026"
                dt = parser.parse(date_text)
                pub_date = dt.date()
            except Exception:
                pub_date = None
        else:
            pub_date = None
        
        # Fallback to time element if exists
        if pub_date is None:
            time_tag = release_soup.find("time", {"datetime": True})
            if time_tag and time_tag.get("datetime"):
                try:
                    dt = parser.parse(time_tag["datetime"])
                    pub_date = dt.date()
                except Exception:
                    pass
        
        # Extract author from <span class="content__author">
        author_span = release_soup.find("span", class_="content__author")
        author = None
        if author_span:
            raw_author = author_span.get_text(strip=True)  # e.g., "Elian Corven"
            # There might be extra like "Elian Corven · Head of Economic Accounts"
            # Split by "·" or "·" and take first part
            parts = raw_author.split("·")
            author_text = parts[0].strip()
            # Remove trailing job role if present (simple: split by space and drop words that are titles)
            # We'll just take the first word(s) that are not obviously a title? But spec says without job titles.
            # The author credit is just the name; the role appears after "·". So author_text should be name only.
            # However sometimes author may be "John Doe and Jane Smith"? Not in sample.
            # We'll keep author_text as is (name only). No "By" etc.
            # Filter out words that are titles? Not needed if we split by "·".
            # Remove possible trailing punctuation.
            author = author_text
        
        # Normalize date string
        date_str = None
        if pub_date:
            date_str = pub_date.strftime("%Y-%m-%d")
        
        # Extract body from <section class="content__body">
        body_section = release_soup.find("section", class_="content__body")
        body_text_parts = []
        if body_section:
            paras = body_section.find_all("p")
            for p in paras:
                txt = p.get_text(separator="\n", strip=True)
                if txt:
                    body_text_parts.append(txt.strip())
            body = "\n\n".join(body_text_parts)
        else:
            # fallback: get text from article excluding header/footer
            article = release_soup.find("article", class_="content")
            if article:
                paras = article.find_all("p")
                body_text_parts = [p.get_text(strip=True) for p in paras if p.get_text(strip=True)]
                body = "\n\n".join(body_text_parts)
            else:
                body = ""
        
        # Build record
        record = {
            "url": abs_url,
            "title": title,
            "date": date_str if date_str else None,
            "author": author if author else None,
            "body": body
        }
        records.append(record)
    
    # Sort newest first by date
    def get_date(rec):
        d = rec["date"]
        if d and isinstance(d, str):
            try:
                return parser.parse(d).date()
            except Exception:
                return datetime.min.date()
        return datetime.min.date()
    
    records.sort(key=get_date, reverse=True)
    return records
