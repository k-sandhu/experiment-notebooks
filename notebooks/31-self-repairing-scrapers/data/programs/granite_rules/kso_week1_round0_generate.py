import urllib.parse
from datetime import datetime
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
    
    # Find all news items in the listing
    news_items = soup.find_all("li", class_="news-item")
    records = []
    
    for item in news_items:
        # Extract link
        link_tag = item.find("a", class_="news-link")
        if not link_tag:
            continue
        rel_url = link_tag["href"]
        abs_url = urllib.parse.urljoin(listing_url, rel_url)
        
        # Get title from link text
        title_tag = link_tag.find(string=True)
        if not title_tag:
            title = ""
        else:
            title = title_tag.strip()
        
        # Extract datetime from <time> element
        time_tag = item.find("time", {"datetime": True})
        pub_date = None
        if time_tag and time_tag.get("datetime"):
            dt_str = time_tag.get("datetime")
            try:
                # Parse datetime string like "2026-09-22T14:30:00+01:00"
                dt = parser.parse(dt_str)
                pub_date = dt.date()
            except Exception:
                pass
        
        # Fetch release page
        release_html = fetch(abs_url)
        release_soup = BeautifulSoup(release_html, "html.parser")
        
        # Extract title from <h1 class="release-title">
        title_elem = release_soup.find("h1", class_="release-title")
        if title_elem:
            title = title_elem.get_text(strip=True)
        else:
            # Fallback to link text if needed
            title = title_tag.strip() if title_tag else ""
        
        # Extract publication date from <time class="pubdate">
        pubdate_tag = release_soup.find("time", class_="pubdate")
        if pubdate_tag and pubdate_tag.get("datetime"):
            dt_str = pubdate_tag.get("datetime")
            try:
                dt = parser.parse(dt_str)
                pub_date = dt.date()
            except Exception:
                pass
        
        # Extract author from <p class="byline">
        byline_tag = release_soup.find("p", class_="byline")
        author = None
        if byline_tag:
            byline_text = byline_tag.get_text(strip=True)
            # Remove "By " prefix and any trailing titles like "Head of ..."
            if byline_text.startswith("By "):
                byline_text = byline_text[3:].strip()
            # Split by commas or "and" for multiple names; simple cleaning
            # Remove common phrases like "Head of ..."
            words = byline_text.split()
            # Keep only words that are likely names (simple heuristic: not typical job titles)
            # Remove known job title words (very basic)
            job_indicators = {"Head", "Director", "Manager", "Chief", "Senior", "Junior", "Assistant", "Lead", "Analyst", "Research", "Officer", "Coordinator", "Representative"}
            names = [w for w in words if w not in job_indicators and w.lower() not in {"by"}]
            # Join with " and " if multiple names
            if names:
                # Simple name list: take first two words as name? Assume format "First Last" or "First Last, Title" already stripped.
                # Keep all remaining words that look like names (simple)
                # Remove trailing commas or periods
                cleaned = []
                for w in names:
                    if w.endswith(',') or w.endswith('.'):
                        continue
                    cleaned.append(w)
                if cleaned:
                    author = " and ".join(cleaned[:2])  # take first two names as example; adjust if needed
                    # Actually join all cleaned names with " and " before last
                    if len(cleaned) > 1:
                        author = " and ".join(cleaned[:-1]) + " " + cleaned[-1]
                    else:
                        author = cleaned[0]
                else:
                    author = None
            else:
                author = None
        
        # Extract body from <div class="release-body">
        body_div = release_soup.find("div", class_="release-body")
        body_text_parts = []
        if body_div:
            # Get all <p> inside release-body
            paras = body_div.find_all("p")
            for p in paras:
                txt = p.get_text(separator="\n", strip=True)
                if txt:
                    body_text_parts.append(txt.strip())
            # Join with blank line separator
            body = "\n\n".join(body_text_parts)
        else:
            # Fallback: get text from article excluding header/footer
            article = release_soup.find("article", class_="release")
            if article:
                # Get text of all <p> inside article
                paras = article.find_all("p")
                body_text_parts = [p.get_text(strip=True) for p in paras if p.get_text(strip=True)]
                body = "\n\n".join(body_text_parts)
            else:
                body = ""
        
        # Normalize date string
        date_str = None
        if pub_date:
            date_str = pub_date.strftime("%Y-%m-%d")
        elif pub_date is None and time_tag:
            # fallback to listing time if no pubdate on release page
            try:
                dt = parser.parse(time_tag.get("datetime"))
                date_str = dt.date().strftime("%Y-%m-%d")
            except Exception:
                pass
        
        # Build record
        record = {
            "url": abs_url,
            "title": title,
            "date": date_str if date_str else None,
            "author": author,
            "body": body
        }
        # Only include if date is not None
        if record["date"]:
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
