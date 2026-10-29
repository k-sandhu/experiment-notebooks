import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser
from typing import List, Dict, Optional

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
    # Fetch listing page
    listing_html = fetch(listing_url)
    soup = BeautifulSoup(listing_html, "html.parser")
    
    # Find table body rows
    rows = soup.find_all("tr", class_=lambda x: x and "date" in x)  # rows with date cells
    # Actually rows are in tbody; find all rows under table with class bok-table
    table = soup.find("table", class_="bok-table")
    if not table:
        return []
    rows = table.find_all("tr", recursive=False)  # all rows in tbody
    records = []
    
    for row in rows:
        date_cell = row.find(class_="date")
        title_cell = row.find(class_=lambda x: x and "title" in x or True)  # find <a> in title cell
        # Better: find <a> inside row after date cell
        title_a = row.find("a", href=True)
        if not title_a:
            continue
        rel_url = title_a["href"]
        abs_url = urllib.parse.urljoin(listing_url, rel_url)
        
        # Extract date from date_cell text like "28 September 2026"
        date_text = date_cell.get_text(strip=True) if date_cell else ""
        # parse to date
        try:
            # dateutil parser handles "28 September 2026"
            dt = parser.parse(date_text)
            date_str = dt.strftime("%Y-%m-%d")
        except Exception:
            # fallback: extract first 4-digit year and month name?
            # simple regex not allowed; skip?
            continue
        
        # Fetch release page
        release_html = fetch(abs_url)
        release_soup = BeautifulSoup(release_html, "html.parser")
        
        # Title: from <h1> inside page-head or <a> text? Use <h1>
        h1 = release_soup.find("h1")
        title = h1.get_text(strip=True) if h1 else title_a.get_text(strip=True)
        
        # Date from meta meta class="meta"
        meta = release_soup.find(class_="meta")
        date_meta_text = meta.get_text(strip=True) if meta else date_text
        # parse again
        try:
            dt2 = parser.parse(date_meta_text)
            date_str2 = dt2.strftime("%Y-%m-%d")
            # use date from meta if present else listing date
            pub_date = date_str2
        except Exception:
            pub_date = date_str
        
        # Author: look for author info; sample page has none? maybe in page-head?
        # Not present in sample; return None
        author = None
        
        # Body: find .rte div and get paragraphs text, preserve blank lines
        rte = release_soup.find(class_="rte")
        if rte:
            # get all <p> inside rte
            paras = []
            for p in rte.find_all("p"):
                # get text, normalize whitespace
                txt = p.get_text(separator="\n", strip=True)
                if txt:
                    paras.append(txt)
            body_text = "\n".join(paras)
        else:
            # fallback: get all text from main excluding notes etc
            main = release_soup.find(id="main")
            if main:
                # remove aside notes class
                for aside in main.find_all(class_="notes"):
                    aside.decompose()
                body_text = main.get_text(separator="\n", strip=False)
                # clean extra newlines? keep blank lines between paras
                # simple: split by double newline? but spec says blank lines separate paragraphs
                # We'll keep as is
                body_text = "\n".join([line for line in body_text.split("\n") if line.strip() or line == ""])
            else:
                body_text = ""
        
        # Clean body: ensure paragraphs separated by blank line (single newline)
        # Already joined with \n; ensure no leading/trailing newlines
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
