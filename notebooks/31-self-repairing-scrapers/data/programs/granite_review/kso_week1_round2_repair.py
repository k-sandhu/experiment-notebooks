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
    
    # Find all news items in the listing
    news_items = soup.find_all("li", class_="news-item")
    records = []
    
    for item in news_items:
        # Extract link
        link_tag = item.find("a", class_="news-link")
        if not link_tag or "href" not in link_tag.attrs:
            continue
        rel_url = link_tag["href"]
        abs_url = urllib.parse.urljoin(listing_url, rel_url)
        
        # Get title from link text (fallback to time if missing)
        title_tag = link_tag.find(string=True)
        if title_tag:
            title = title_tag.strip()
        else:
            title = link_tag.get_text(strip=True)
        
        # Extract datetime from <time> element in listing (used for sorting later)
        time_tag = item.find("time", {"datetime": True})
        listing_dt = None
        if time_tag and time_tag.get("datetime"):
            dt_str = time_tag.get("datetime")
            try:
                dt = parser.parse(dt_str)
                listing_dt = dt.date()
            except Exception:
                pass
        
        # Fetch release page
        release_html = fetch(abs_url)
        release_soup = BeautifulSoup(release_html, "html.parser")
        
        # Extract title from <h1 class="release-title">
        title_elem = release_soup.find("h1", class_="release-title")
        if title_elem:
            title = title_elem.get_text(strip=True)
        # else keep title from link
        
        # Extract publication date from <time class="pubdate">
        pubdate_tag = release_soup.find("time", class_="pubdate")
        pub_date = None
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
            # Remove leading "By " (case-insensitive)
            if byline_text.lower().startswith("by "):
                byline_text = byline_text[3:].strip()
            # Define job title indicators (simple set)
            job_indicators = {
                "head", "director", "manager", "chief", "senior", "junior",
                "assistant", "lead", "analyst", "research", "officer",
                "coordinator", "representative", "of", "and", "the"
            }
            words = byline_text.split()
            # Find first word that is a job indicator (case-insensitive)
            first_job_idx = None
            for i, w in enumerate(words):
                if w.lower() in job_indicators:
                    first_job_idx = i
                    break
            if first_job_idx is None:
                # No job indicator found, take all words
                author = " ".join(words)
            else:
                # Take words before the first job indicator
                name_words = words[:first_job_idx]
                # Filter out empty strings
                name_words = [w for w in name_words if w]
                # Join with spaces (names may be multiple words like "Elian Corven")
                author = " ".join(name_words)
                # If there are multiple distinct names separated by commas or "and" before the job indicator,
                # the simple split approach works because commas/and are not job indicators? 
                # Example "Elian Corven, Head of ..." -> words = ["Elian", "Corven,", "Head"] -> first_job_idx at "Head", name_words = ["Elian", "Corven,"] -> need to clean punctuation.
                # Clean trailing commas from name words
                cleaned = []
                for w in name_words:
                    # Remove trailing commas/periods
                    w = w.rstrip(",.")
                    cleaned.append(w)
                author = " ".join(cleaned)
        else:
            author = None
        
        # Normalize date string
        date_str = None
        if pub_date:
            date_str = pub_date.strftime("%Y-%m-%d")
        elif listing_dt:
            date_str = listing_dt.strftime("%Y-%m-%d")
        
        # Extract body from <div class="release-body">
        body_div = release_soup.find("div", class_="release-body")
        body_text_parts = []
        if body_div:
            paras = body_div.find_all("p")
            for p in paras:
                txt = p.get_text(separator="\n", strip=True)
                if txt:
                    body_text_parts.append(txt.strip())
            body = "\n\n".join(body_text_parts)
        else:
            # Fallback: get text from article excluding header/footer
            article = release_soup.find("article", class_="release")
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
            "date": date_str,  # may be None if no date found
            "author": author,
            "body": body
        }
        if record["date"]:
            records.append(record)
    
    # Sort newest first by date from listing time (most reliable)
    def get_date(rec):
        d = rec["date"]
        if d and isinstance(d, str):
            try:
                # dateutil can parse "YYYY-MM-DD"
                return parser.parse(d).date()
            except Exception:
                return date.min
        return date.min
    
    records.sort(key=get_date, reverse=True)
    return records
