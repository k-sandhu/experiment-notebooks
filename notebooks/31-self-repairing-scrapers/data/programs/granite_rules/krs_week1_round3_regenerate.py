import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser

class FetchError(Exception):
    def __init__(self, status):
        self.status = status
        super().__init__(f"FetchError: {status}")

def extract(fetch, listing_url):
    # Fetch listing page
    listing_html = fetch(listing_url)
    soup = BeautifulSoup(listing_html, "html.parser")
    
    # Find all news items on listing page (including pagination)
    releases = []
    
    # Collect pagination links
    pagination_links = []
    pager = soup.find("nav", class_="pager")
    if pager:
        for a in pager.find_all("a", href=True):
            href = a["href"]
            if href.startswith("/newsroom?page="):
                page_num = int(href.split("=")[1])
                pagination_links.append((page_num, href))
    
    # Process current page items
    current_page_soup = soup
    all_release_links = []
    
    # Extract links from current page views-row items
    for row in current_page_soup.find_all("div", class_="views-row"):
        link_tag = row.find("a", class_="field-title")
        if link_tag and link_tag.get("href"):
            href = link_tag["href"]
            abs_url = urllib.parse.urljoin(listing_url.rstrip("/") + "/", href.lstrip("/"))
            all_release_links.append(abs_url)
    
    # Process pagination pages
    for page_num, _ in pagination_links:
        if page_num == 1:
            continue  # already processed
        page_url = f"/newsroom?page={page_num}"
        page_abs = urllib.parse.urljoin(listing_url.rstrip("/") + "/", page_url)
        try:
            page_html = fetch(page_abs)
            page_soup = BeautifulSoup(page_html, "html.parser")
            for row in page_soup.find_all("div", class_="views-row"):
                link_tag = row.find("a", class_="field-title")
                if link_tag and link_tag.get("href"):
                    href = link_tag["href"]
                    abs_url = urllib.parse.urljoin(listing_url.rstrip("/") + "/", href.lstrip("/"))
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
    
    # Fetch each release page and extract data
    records = []
    for rel_url in unique_links:
        try:
            rel_html = fetch(rel_url)
            rel_soup = BeautifulSoup(rel_html, "html.parser")
            
            # Title
            title_tag = rel_soup.find("h1", class_="page-title")
            if title_tag:
                title = title_tag.get_text(strip=True)
            else:
                # fallback to link text
                link_tag = rel_soup.find("a", href=rel_url.lstrip("/"))
                if link_tag:
                    title = link_tag.get_text(strip=True)
                else:
                    title = "Unknown"
            
            # Date
            date_div = rel_soup.find("div", class_="field-date")
            date_text = None
            if date_div:
                date_text = date_div.get_text(strip=True)
                # Extract date like "18/09/2026"
                parts = date_text.split()
                if len(parts) >= 1:
                    date_str = parts[0]
                    # Convert dd/mm/yyyy to yyyy-mm-dd
                    try:
                        dt = parser.parse(date_str)
                        date_iso = dt.strftime("%Y-%m-%d")
                        date_text = date_iso
                    except Exception:
                        pass  # keep original if parse fails
            if not date_text:
                # fallback: look for date in link path like /2026/...
                path_parts = rel_url.split("/")
                if len(path_parts) >= 3:
                    year_part = path_parts[1]
                    if year_part.isdigit() and len(year_part) == 4:
                        date_text = f"{year_part}-01-01"  # approximate, but listing shows month/day
                        # better: extract month/day from link name? not reliable
            date = date_text if date_text else "1970-01-01"
            
            # Author
            author = None
            # Look for author field; sample page doesn't show explicit author, may be missing
            # So default None
            author = None
            
            # Body
            body_div = rel_soup.find("div", class_="field-body")
            body_text = ""
            if body_div:
                # Get all text from paragraphs inside, preserve blank lines between paragraphs
                paragraphs = []
                for p in body_div.find_all("p"):
                    txt = p.get_text(separator="\n", strip=True)
                    if txt:
                        paragraphs.append(txt)
                # Join with blank line between paragraphs
                body_text = "\n\n".join(paragraphs)
            else:
                # fallback: get text from main content excluding header/footer
                main = rel_soup.find("main")
                if main:
                    # remove header and footer? simpler: get all text and clean
                    # but requirement: no nav, cookie notices etc. We'll extract from field-body only
                    pass
            
            # Build record
            rec = {
                "url": rel_url,
                "title": title,
                "date": date_text if date_text and len(date_text) >= 10 and "-" in date_text else "1970-01-01",
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
