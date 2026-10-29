import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser
from typing import List, Dict

class FetchError(Exception):
    def __init__(self, status: int):
        self.status = status
        super().__init__(f"HTTP {status}")

def extract(fetch, listing_url: str) -> List[Dict]:
    """
    Extract all press releases from the listing page.
    Returns list of dicts with keys: url, title, date, author, body.
    Newest first.
    """
    listing_html = fetch(listing_url)
    soup = BeautifulSoup(listing_html, "html.parser")
    
    table = soup.find("table", class_="bok-table")
    if not table:
        return []
    
    rows = table.find_all("tr", recursive=False)
    records = []
    
    for row in rows:
        # Find date cell and title <a>
        date_cell = row.find(class_="date")
        title_a = row.find("a", href=True)
        if not date_cell or not title_a:
            continue
        
        date_text = date_cell.get_text(strip=True)
        try:
            dt = parser.parse(date_text)
            date_str = dt.strftime("%Y-%m-%d")
        except Exception:
            continue
        
        rel_url = title_a["href"]
        abs_url = urllib.parse.urljoin(listing_url, rel_url)
        
        # Fetch release page
        try:
            release_html = fetch(abs_url)
        except FetchError:
            continue
        release_soup = BeautifulSoup(release_html, "html.parser")
        
        # Title from <h1> inside page-head
        h1 = release_soup.find("h1")
        title = h1.get_text(strip=True) if h1 else title_a.get_text(strip=True)
        
        # Date from meta class="meta"
        meta = release_soup.find(class_="meta")
        date_meta_text = meta.get_text(strip=True) if meta else date_text
        try:
            dt2 = parser.parse(date_meta_text)
            pub_date = dt2.strftime("%Y-%m-%d")
        except Exception:
            pub_date = date_str
        
        # Author: look for author info; sample page has none
        author = None
        # Some releases might have author in page-head? Not present in sample.
        # Search for common patterns like "by" etc., but spec says None when no person credited.
        # Simple: None
        
        # Body from .rte class
        rte = release_soup.find(class_="rte")
        if rte:
            paras = []
            for p in rte.find_all("p"):
                txt = p.get_text(separator="\n", strip=False)
                # Keep empty paragraphs? strip=False keeps whitespace
                paras.append(txt)
            body_text = "\n".join(paras)
        else:
            # Fallback: main content without notes
            main = release_soup.find(id="main")
            if main:
                for aside in main.find_all(class_="notes"):
                    aside.decompose()
                body_text = main.get_text(separator="\n", strip=False)
                # Ensure blank lines between paragraphs: split by double newline?
                # Keep as is; spec wants blank lines separating paragraphs.
                # Simple join with \n after stripping trailing/leading newlines
                lines = [line for line in body_text.split("\n") if line == "" or line.strip()]
                # Preserve empty lines that separate paragraphs
                # We'll keep original newlines; strip only leading/trailing
                body_text = "\n".join(lines).strip()
            else:
                body_text = ""
        
        # Clean body: ensure single newline between paragraphs, no extra leading/trailing newlines
        body_text = body_text.strip()
        
        record = {
            "url": abs_url,
            "title": title,
            "date": pub_date,
            "author": author,
            "body": body_text
        }
        records.append(record)
    
    # Sort newest first by date string (YYYY-MM-DD) descending
    records.sort(key=lambda r: r["date"], reverse=True)
    return records
