import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser

class FetchError(Exception):
    def __init__(self, status):
        self.status = status
        super().__init__(f"HTTP {status}")

def extract(fetch, listing_url):
    html = fetch(listing_url)
    soup = BeautifulSoup(html, "html.parser")
    
    table = soup.find("table", class_="bok-table")
    if not table:
        return []
    
    tbody = table.find("tbody")
    rows = tbody.find_all("tr") if tbody else []
    
    records = []
    for row in rows:
        tds = row.find_all("td")
        if len(tds) < 2:
            continue
        
        date_el = tds[0]
        title_el = tds[1]
        
        date_text = date_el.get_text(strip=True)
        try:
            pub_date = parser.parse(date_text).date()
        except Exception:
            continue
        
        title_a = title_el.find("a")
        if not title_a:
            continue
        rel_url = title_a.get("href")
        abs_url = urllib.parse.urljoin(listing_url, rel_url)
        
        try:
            release_html = fetch(abs_url)
        except FetchError:
            continue
        
        release_soup = BeautifulSoup(release_html, "html.parser")
        
        page_head = release_soup.find(class_="page-head")
        h1 = page_head.find("h1") if page_head else release_soup.find("h1")
        title_text = h1.get_text(strip=True) if h1 else ""
        
        author = None
        # Look for author in meta or author tag; sample has none
        # Simple heuristic: find meta with name="author" or author meta
        meta_author = release_soup.find("meta", {"name": "author"})
        if meta_author and meta_author.get("content"):
            author = meta_author["content"].strip()
        # Also look for <span class="author"> etc. Not present; keep None
        
        rte = release_soup.find(class_="rte")
        body_parts = []
        if rte:
            paras = rte.find_all("p")
            for p in paras:
                text = p.get_text(separator="\n", strip=True)
                if text.strip():
                    body_parts.append(text.strip())
        body = "\n\n".join(body_parts)
        
        record = {
            "url": abs_url,
            "title": title_text,
            "date": pub_date.isoformat(),
            "author": author,
            "body": body
        }
        records.append(record)
    
    # Sort newest first
    records.sort(key=lambda r: r["date"], reverse=True)
    return records
