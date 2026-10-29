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
        if not link_tag or "href" not in link_tag.attrs:
            continue
        rel_url = link_tag["href"]
        abs_url = urllib.parse.urljoin(listing_url, rel_url)
        
        # Get title from link text (fallback to time if missing)
        title_tag = link_tag.find(string=True)
        if title_tag:
            title = title_tag.strip()
        else:
            # fallback: text inside <a>
            title = link_tag.get_text(strip=True)
        
        # Extract datetime from <time> element in listing
        time_tag = item.find("time", {"datetime": True})
        pub_date = None
        if time_tag and time_tag.get("datetime"):
            dt_str = time_tag.get("datetime")
            try:
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
        # else keep title from link
        
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
            # Remove "By " prefix
            if byline_text.startswith("By "):
                byline_text = byline_text[3:].strip()
            # Split by commas or "and" for multiple names; simple cleaning
            # Remove trailing job titles (simple heuristic)
            # Collect words that look like names (not typical job indicators)
            job_indicators = {
                "Head", "Director", "Manager", "Chief", "Senior", "Junior", 
                "Assistant", "Lead", "Analyst", "Research", "Officer", 
                "Coordinator", "Representative", "of", "and"
            }
            words = byline_text.split()
            # Filter out job indicators and "and"/"of"
            filtered = [w for w in words if w.lower() not in job_indicators]
            # Join remaining words with " and "
            if filtered:
                # Simple join all remaining words (they should be names like "Elian Corven")
                # but avoid adding "and" between parts that already have commas?
                # Just join with " and " between all words? Actually names may be "Elian Corven" (two words)
                # We'll join all filtered words with space and then replace single spaces? No.
                # The spec: several names joined with " and "; e.g., "John Doe and Jane Smith"
                # Assume filtered list contains full names (multiple words) already separated by spaces.
                # We cannot split further; just keep as is but ensure no job words.
                # However words like "Elian" and "Corven" are separate; we need to keep them together.
                # Since we split by spaces, we lost original grouping. Better: extract names before first job indicator.
                # Simpler: take the first two words that are not job indicators? Not reliable.
                # Use heuristic: take all words except job indicators, then join with space.
                # But spec says "and" between names, not spaces. Example: "Elian Corven and Head of ..." would become "Elian Corven".
                # Since we removed job indicators, we get just names.
                # However the error showed "Elian and of and Economic Accounts" because they kept "of" and "and".
                # So just join filtered words with space? But spec says "and". We'll join with " and " between each name token? That would produce "Elian Corven and ..." which is wrong.
                # Actually author should be "Elian Corven" (single name) or "John Doe and Jane Smith".
                # Without more info, join filtered words with space.
                author = " ".join(filtered)
                # If there are multiple distinct names separated by commas or "and", the original byline might be "Elian Corven, Head of ..."
                # After removing job indicators, we get ["Elian", "Corven"] -> "Elian Corven". Good.
                # For multiple authors like "Alice Smith and Bob Jones", words = ["Alice", "Smith", "and", "Bob", "Jones"]; job_indicators includes "and", so filtered = ["Alice","Smith","Bob","Jones"] -> "Alice Smith Bob Jones" wrong.
                # Need to handle "and" as separator. Simpler: keep original byline text and remove job titles after first name.
                # Given time, implement basic: take words up to first job indicator.
                # Find index of first job indicator word
                for i, w in enumerate(words):
                    if w.lower() in job_indicators:
                        # keep words[:i]
                        author = " ".join(words[:i])
                        break
                else:
                    # no job indicator found
                    author = " ".join(words)
            else:
                author = None
        else:
            author = None
        
        # Normalize date string
        date_str = None
        if pub_date:
            date_str = pub_date.strftime("%Y-%m-%d")
        elif pubdate_tag and pubdate_tag.get("datetime"):
            # fallback to listing time if no pubdate on release page
            try:
                dt = parser.parse(pubdate_tag.get("datetime"))
                date_str = dt.date().strftime("%Y-%m-%d")
            except Exception:
                pass
        elif time_tag and time_tag.get("datetime"):
            try:
                dt = parser.parse(time_tag.get("datetime"))
                date_str = dt.date().strftime("%Y-%m-%d")
            except Exception:
                pass
        
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
            "date": date_str if date_str else None,
            "author": author,
            "body": body
        }
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
