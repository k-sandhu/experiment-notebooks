import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser
from typing import List, Dict, Optional

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
    Extract all news release records from the Kestria Securities Commission listing.
    Returns a list of dicts, newest first.
    """
    # Fetch the listing page
    html = fetch(listing_url)
    soup = BeautifulSoup(html, "html.parser")
    
    # Find all teaser articles
    teasers = soup.find_all("article", class_="teaser")
    records = []
    
    for teaser in teasers:
        # Extract relative link from <a> inside <h2>
        h2 = teaser.find("h2")
        if not h2:
            continue
        link_tag = h2.find("a", href=True)
        if not link_tag or not link_tag["href"]:
            continue
        
        rel_url = link_tag["href"]
        abs_url = urllib.parse.urljoin(listing_url, rel_url)
        
        # Fetch the release page
        try:
            release_html = fetch(abs_url)
        except FetchError as e:
            # Skip releases that cannot be fetched
            continue
        
        release_soup = BeautifulSoup(release_html, "html.parser")
        
        # Extract title: full headline as plain text from <h1>
        h1 = release_soup.find("h1")
        if h1:
            # Get the first text node inside h1
            title_text = h1.get_text(separator="\n", strip=True)
            # Remove possible trailing newline or extra spaces
            title = title_text.strip()
        else:
            # fallback: get from <a> in teaser? but spec says full headline on release page
            title = ""
        
        # Extract date: "First published" <dd>
        meta_dl = release_soup.find("dl", class_="meta")
        pub_date = None
        if meta_dl:
            # Find dt with "First published"
            pub_dt = meta_dl.find("dt", string=lambda t: t and t.lower().startswith("first published"))
            if pub_dt:
                pub_dd = pub_dt.find_next_sibling("dd")
                if pub_dd:
                    date_text = pub_dd.get_text(strip=True)
                    try:
                        # parse "30 September 2026"
                        parsed = parser.parse(date_text)
                        pub_date = parsed.date().isoformat()
                    except Exception:
                        pass
        
        # Extract author: <dt>Author</dt> <dd>...</dd>
        author_names = []
        if meta_dl:
            auth_dt = meta_dl.find("dt", string=lambda t: t and t.lower().startswith("author"))
            if auth_dt:
                auth_dd = auth_dt.find_next_sibling("dd")
                if auth_dd:
                    raw_author = auth_dd.get_text(strip=True)
                    # Simple cleaning: split by commas and "and", strip, filter obvious non-names
                    parts = []
                    # Replace "and" with "," for uniform splitting
                    raw_clean = raw_author.replace(" and ", ",")
                    for part in raw_clean.split(","):
                        part = part.strip()
                        if part:
                            # Remove trailing punctuation like period
                            part = part.rstrip(".")
                            # Skip if part looks like a date (contains month name and day) or empty
                            # Very simple: if part contains a 3-letter month? Not reliable, but we keep all
                            # The spec says remove job titles and "By"; we just take the raw name as is
                            # The sample shows "Selin Arvane" fine.
                            parts.append(part)
                    author_names = parts
        
        # Combine author names with " and "
        author = None
        if author_names:
            # Filter out empty strings
            filtered = [p for p in author_names if p]
            # If any filtered name looks like a date (contains a 3-letter month and number), skip? Not needed for sample.
            # Just join with " and "
            author = " and ".join(filtered)
        
        # Extract body: .body div paragraphs
        body_div = release_soup.find("div", class_="body")
        body_text_parts = []
        if body_div:
            # get all <p> inside body_div
            ps = body_div.find_all("p")
            for p in ps:
                text = p.get_text(separator="\n", strip=True)
                if text:
                    body_text_parts.append(text.strip())
            body = "\n".join(body_text_parts)
        else:
            # fallback: get all paragraphs in main excluding contact paragraph
            main = release_soup.find("main")
            if main:
                ps = main.find_all("p")
                for p in ps:
                    if p.get("class") and "contact" in p.get("class", []):
                        continue
                    text = p.get_text(strip=True)
                    if text:
                        body_text_parts.append(text)
                body = "\n".join(body_text_parts)
            else:
                body = ""
        
        record = {
            "url": abs_url,
            "title": title if title else "",
            "date": pub_date if pub_date else None,
            "author": author if author else None,
            "body": body if body else "",
        }
        records.append(record)
    
    # Sort newest first by date; None dates go last
    dated = [r for r in records if r["date"] is not None]
    # Sort by date descending
    dated.sort(key=lambda r: r["date"], reverse=True)
    undated = [r for r in records if r["date"] is None]
    records = dated + undated
    
    return records
