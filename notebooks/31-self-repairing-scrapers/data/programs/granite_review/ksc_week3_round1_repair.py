import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser
from typing import List, Dict

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
            # Get the first text node inside h1 (ignoring possible nested tags)
            title_text = h1.get_text(separator="\n", strip=True)
            title = title_text.strip()
        else:
            title = ""
        
        # Extract date: "First published" <dd>
        pub_date = None
        meta_dl = release_soup.find("dl", class_="meta")
        if meta_dl:
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
        author = None
        if meta_dl:
            auth_dt = meta_dl.find("dt", string=lambda t: t and t.lower().startswith("author"))
            if auth_dt:
                auth_dd = auth_dt.find_next_sibling("dd")
                if auth_dd:
                    raw_author = auth_dd.get_text(strip=True)
                    # Simple cleaning: split by commas and "and", keep non-empty parts
                    parts = []
                    # Replace "and" with "," for uniform splitting
                    cleaned = raw_author.replace(" and ", ",")
                    for part in cleaned.split(","):
                        part = part.strip()
                        if part:
                            # Remove trailing punctuation like period
                            if part.endswith("."):
                                part = part[:-1]
                            parts.append(part)
                    # Filter out obvious non-names (e.g., reference numbers like "KSC-2026-829")
                    # Keep only parts that look like names (no digits or month names)
                    filtered = []
                    for part in parts:
                        # Simple heuristic: if part contains only letters and spaces, keep
                        if all(c.isalpha() or c.isspace() for c in part):
                            filtered.append(part)
                    if filtered:
                        author = " and ".join(filtered)
        
        # Extract body: .body div paragraphs, separated by blank lines (\n\n)
        body = ""
        body_div = release_soup.find("div", class_="body")
        if body_div:
            ps = body_div.find_all("p")
            body_parts = []
            for p in ps:
                text = p.get_text(strip=True)
                if text:
                    body_parts.append(text)
            # Join paragraphs with a blank line (\n\n) as required
            body = "\n\n".join(body_parts)
        else:
            # fallback: get all <p> inside main excluding contact paragraph
            main = release_soup.find("main")
            if main:
                ps = main.find_all("p")
                body_parts = []
                for p in ps:
                    if p.get("class") and "contact" in p.get("class", []):
                        continue
                    text = p.get_text(strip=True)
                    if text:
                        body_parts.append(text)
                body = "\n\n".join(body_parts)
        
        record = {
            "url": abs_url,
            "title": title if title else "",
            "date": pub_date if pub_date else None,
            "author": author if author else None,
            "body": body if body else "",
        }
        records.append(record)
    
    # Sort: dated records newest first, undated last
    dated = [r for r in records if r["date"] is not None]
    undated = [r for r in records if r["date"] is None]
    
    # Sort dated by date descending (YYYY-MM-DD string works lexicographically)
    dated.sort(key=lambda r: r["date"], reverse=True)
    
    records = dated + undated
    
    return records
