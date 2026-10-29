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
        
        # Extract title: full headline as plain text
        h1 = release_soup.find("h1")
        if h1:
            title_tag = h1.find(string=True)
            title = title_tag.strip() if title_tag else ""
        else:
            # fallback: get from <a> in teaser? but spec says full headline on release page
            # use h2 from teaser? No, must be from release page
            title = ""
        
        # Extract date: "Published" <dd>
        meta_dl = release_soup.find("dl", class_="meta")
        pub_date = None
        if meta_dl:
            pub_dt = meta_dl.find("dt", string=lambda t: t and t.lower().startswith("published"))
            if pub_dt:
                pub_dd = pub_dt.find_next_sibling("dd")
                if pub_dd:
                    date_text = pub_dd.get_text(strip=True)
                    try:
                        # parse "30 September 2026"
                        pub_date = parser.parse(date_text).date().isoformat()
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
                    # Remove job titles or "By" etc. Simple: split by commas/and and take first words not obviously dates
                    # We'll just take the raw text if it doesn't look like a date (contains digits and month)
                    # Heuristic: if contains month name and day? but author could be "Selin Arvane" fine.
                    # We'll keep raw but ensure not empty
                    if raw_author and not any(word.lower() in ["by", "and"] for word in raw_author.split()):
                        # simple split by commas and "and"
                        parts = []
                        for part in raw_author.replace("and", ",").split(","):
                            part = part.strip()
                            if part:
                                # remove trailing punctuation
                                part = part.rstrip(".")
                                parts.append(part)
                        author_names = parts
        
        # Combine author names with " and "
        author = None
        if author_names:
            # filter out empty or obvious non-names (like dates)
            filtered = []
            for name in author_names:
                # skip if name matches date pattern (simple check)
                if len(name) > 10 and any(c.isdigit() for c in name):
                    # might be date, skip
                    continue
                filtered.append(name)
            if filtered:
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
            # fallback: get all paragraphs in main? but spec says main text only
            # get all <p> inside main excluding contact paragraph? contact class "contact"
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
        # Ensure date is string YYYY-MM-DD or None
        if record["date"] is None:
            record["date"] = None
        
        records.append(record)
    
    # Sort newest first by date; None dates go last
    def sort_key(rec):
        date_val = rec["date"]
        if date_val is None:
            return (0, "")  # will be placed after dated ones? we want newest first, so None should be last
        try:
            # date is already ISO string
            return (1, date_val)
        except:
            return (0, "")
    
    # Sort descending by date
    records.sort(key=lambda r: (r["date"] is None, r["date"] or ""), reverse=True)
    # Actually need descending date; simplest: filter dated, sort by date descending
    dated = [r for r in records if r["date"] is not None]
    dated.sort(key=lambda r: r["date"], reverse=True)
    undated = [r for r in records if r["date"] is None]
    records = dated + undated
    
    return records
