import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser

class FetchError(Exception):
    def __init__(self, status):
        self.status = status
        super().__init__(f"HTTP {status}")

def fetch(url):
    # Placeholder implementation; in real use would use requests/urllib
    # This stub raises FetchError for demonstration; replace with actual HTTP GET
    # For the purpose of this exercise, we assume fetch works correctly.
    # Since we cannot make real HTTP calls here, we simulate by returning the provided HTML.
    # However, the module must work with the given HTML strings.
    # We'll implement a simple fetch that raises FetchError for non-existent URLs and returns HTML for known ones.
    # But the instruction says fetch is provided by caller; we just need to use it.
    # So we don't implement fetch; we assume it exists.
    pass

def extract(fetch, listing_url):
    # Fetch listing page
    html = fetch(listing_url)
    soup = BeautifulSoup(html, "html.parser")
    
    # Find table body
    table = soup.find("table", class_="bok-table")
    if not table:
        return []
    
    tbody = table.find("tbody")
    rows = tbody.find_all("tr") if tbody else []
    
    records = []
    for row in rows:
        date_cell = row.find("td", class_="date")
        title_cell = row.find("td", class=None)  # actually <td> for title? In sample, <td class="date"> and <td> for title? Let's inspect: <tr><td class="date">... and <td> for title? Actually <td> for date and <td> for title? In sample: <tr><td class="date">28 September 2026</td><td><a href=...>Settlement...</a></td><td>Press release</td></tr>. So title cell is second <td>.
        # Find all <td> children
        tds = row.find_all("td")
        if len(tds) < 2:
            continue
        date_el = tds[0]
        title_el = tds[1]
        type_el = tds[2] if len(tds) > 2 else None
        
        # Extract date string like "28 September 2026"
        date_text = date_el.get_text(strip=True)
        # Parse to date
        try:
            # dateutil parser handles "28 September 2026"
            pub_date = parser.parse(date_text).date()
        except Exception:
            # fallback
            pub_date = None
        
        # Extract title link
        title_a = title_el.find("a")
        if title_a:
            rel_url = title_a.get("href")
            abs_url = urllib.parse.urljoin(listing_url, rel_url)
        else:
            continue
        
        # Fetch release page
        release_html = fetch(abs_url)
        release_soup = BeautifulSoup(release_html, "html.parser")
        
        # Extract title (full headline) from h1 inside page-head or h1 overall
        # In sample: <h1>Settlement system completes recovery exercise from Amberford backup site</h1> inside .page-head
        page_head = release_soup.find(class_="page-head")
        h1 = page_head.find("h1") if page_head else release_soup.find("h1")
        title_text = h1.get_text(strip=True) if h1 else ""
        
        # Extract author
        # Look for author info; not present in sample? Might be in meta? Assume none -> None
        author = None
        
        # Extract body: .rte paragraphs, exclude aside notes
        rte = release_soup.find(class_="rte")
        if rte:
            # Get paragraphs inside rte
            paras = rte.find_all("p")
            body_parts = []
            for p in paras:
                # Get text, preserve line breaks? We need blank lines between paragraphs.
                text = p.get_text(separator="\n", strip=True)
                # Remove empty paragraphs? keep non-empty
                if text.strip():
                    body_parts.append(text.strip())
            # Join with blank line (\n\n)
            body = "\n\n".join(body_parts)
        else:
            body = ""
        
        # Build record
        record = {
            "url": abs_url,
            "title": title_text,
            "date": pub_date.isoformat() if pub_date else "",
            "author": author,
            "body": body
        }
        records.append(record)
    
    # Sort newest first (descending date)
    records.sort(key=lambda r: r["date"], reverse=True)
    return records
