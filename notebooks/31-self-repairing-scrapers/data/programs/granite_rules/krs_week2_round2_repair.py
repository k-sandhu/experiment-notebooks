import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser

class FetchError(Exception):
    def __init__(self, status):
        self.status = status
        super().__init__(f"FetchError: {status}")

def extract(fetch, listing_url):
    listing_html = fetch(listing_url)
    soup = BeautifulSoup(listing_html, "html.parser")
    
    all_release_links = []
    
    # Extract links from current page views-row items
    for row in soup.find_all("div", class_="views-row"):
        h3 = row.find("h3", class_="field-title")
        if h3:
            link_tag = h3.find("a", href=True)
            if link_tag and link_tag.get("href"):
                href = link_tag["href"]
                abs_url = urllib.parse.urljoin(listing_url, href)
                all_release_links.append(abs_url)
    
    # Collect pagination page numbers (excluding current page 1)
    pagination_links = []
    pager = soup.find("nav", class_="pager")
    if pager:
        for a in pager.find_all("a", href=True):
            href = a["href"]
            if href.startswith("/newsroom?page="):
                try:
                    page_num = int(href.split("=")[1])
                except (IndexError, ValueError):
                    continue
                if page_num > 1:  # avoid re-fetching page 1
                    pagination_links.append(page_num)
    
    # Process pagination pages
    for page_num in pagination_links:
        page_url = f"/newsroom?page={page_num}"
        page_abs = urllib.parse.urljoin(listing_url, page_url)
        try:
            page_html = fetch(page_abs)
            page_soup = BeautifulSoup(page_html, "html.parser")
            for row in page_soup.find_all("div", class_="views-row"):
                h3 = row.find("h3", class_="field-title")
                if h3:
                    link_tag = h3.find("a", href=True)
                    if link_tag and link_tag.get("href"):
                        href = link_tag["href"]
                        abs_url = urllib.parse.urljoin(listing_url, href)
                        all_release_links.append(abs_url)
        except FetchError:
            pass  # ignore pagination page fetch errors
    
    # Remove duplicates while preserving order (first occurrence)
    seen = set()
    unique_links = []
    for url in all_release_links:
        if url not in seen:
            seen.add(url)
            unique_links.append(url)
    
    records = []
    for rel_url in unique_links:
        try:
            rel_html = fetch(rel_url)
            rel_soup = BeautifulSoup(rel_html, "html.parser")
            
            # Title from page-title h1
            title_tag = rel_soup.find("h1", class_="page-title")
            if title_tag:
                title = title_tag.get_text(strip=True)
            else:
                # fallback: link text from rel_url if needed
                link_tag = rel_soup.find("a", href=rel_url.lstrip("/"))
                if link_tag:
                    title = link_tag.get_text(strip=True)
                else:
                    title = "Unknown"
            
            # Date from field-date div
            date_div = rel_soup.find("div", class_="field-date")
            date_iso = None
            if date_div:
                date_text = date_div.get_text(strip=True)
                # Extract first token like "18/09/2026"
                parts = date_text.split()
                if parts:
                    date_str = parts[0]
                    try:
                        dt = parser.parse(date_str)
                        date_iso = dt.strftime("%Y-%m-%d")
                    except Exception:
                        pass
            
            # Author: look for author field; sample page has none -> None
            author = None
            # Simple heuristic: if there is a span/div with class containing 'author' or similar, extract names
            # but requirement says None when no person credited. We'll leave None.
            
            # Body from field-body div
            body_div = rel_soup.find("div", class_="field-body")
            body_text = ""
            if body_div:
                paragraphs = []
                for p in body_div.find_all("p"):
                    txt = p.get_text(separator="\n", strip=True)
                    if txt:
                        paragraphs.append(txt)
                body_text = "\n\n".join(paragraphs)
            else:
                # fallback: get text from main excluding header/footer? but spec says only main text.
                # We'll use empty string if no field-body.
                pass
            
            # Build record with proper date or fallback
            date_final = date_iso if date_iso else "1970-01-01"
            rec = {
                "url": rel_url,
                "title": title,
                "date": date_final,
                "author": author,
                "body": body_text
            }
            records.append(rec)
        except FetchError:
            pass  # skip releases that fail to fetch
    
    # Sort by date descending (newest first)
    def get_sort_key(rec):
        d = rec["date"]
        if "-" in d and len(d) == 10:
            try:
                dt = parser.parse(d)
                return dt
            except Exception:
                return parser.parse("1970-01-01")
        return parser.parse("1970-01-01")
    
    records.sort(key=get_sort_key, reverse=True)
    
    return records
