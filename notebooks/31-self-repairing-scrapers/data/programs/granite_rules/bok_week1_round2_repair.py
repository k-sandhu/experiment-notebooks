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
    
    # Get all <tr> inside <tbody> to avoid header row
    tbody = table.find("tbody")
    if tbody:
        rows = tbody.find_all("tr", recursive=False)
    else:
        # fallback: all rows except header if no tbody
        rows = table.find_all("tr", recursive=False)
    
    records = []
    
    for row in rows:
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
        
        try:
            release_html = fetch(abs_url)
        except FetchError:
            continue
        release_soup = BeautifulSoup(release_html, "html.parser")
        
        # Title from <h1> inside page-head or fallback
        h1 = release_soup.find("h1")
        if h1:
            title = h1.get_text(strip=True)
        else:
            title = title_a.get_text(strip=True)
        
        # Date from meta class="meta" (e.g., "Published on 28 September 2026")
        meta = release_soup.find(class_="meta")
        pub_date = date_str  # fallback to listing date if meta parsing fails
        if meta:
            date_meta_text = meta.get_text(strip=True)
            # Extract date pattern like "Published on 28 September 2026"
            # Use parser which handles natural language
            try:
                dt2 = parser.parse(date_meta_text)
                pub_date = dt2.strftime("%Y-%m-%d")
            except Exception:
                pass
        
        # Author: look for author info; sample page has none -> None
        author = None
        # Some releases might list author in page-head? Not present in sample.
        # Search for patterns like "by" etc., but spec says None when no person credited.
        # Simple: None
        
        # Body from .rte class; fallback to main without notes
        rte = release_soup.find(class_="rte")
        if rte:
            paras = []
            for p in rte.find_all("p"):
                txt = p.get_text(separator="\n", strip=False)
                paras.append(txt)
            body_text = "\n".join(paras)
        else:
            main = release_soup.find(id="main")
            if main:
                # Remove notes aside
                for aside in main.find_all(class_="notes"):
                    aside.decompose()
                body_text = main.get_text(separator="\n", strip=False)
            else:
                body_text = ""
        
        # Clean body: strip leading/trailing whitespace but keep internal blank lines
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
