import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser

# Assume FetchError is defined elsewhere; we only use fetch as provided

def extract(fetch, listing_url):
    # Fetch listing page
    listing_html = fetch(listing_url)
    soup = BeautifulSoup(listing_html, "html.parser")
    
    # Find all news items in the main content area
    items = []
    # Look for .views-row elements that contain .field-title <a> links
    rows = soup.find_all("div", class_="views-row")
    for row in rows:
        title_a = row.find("a", class_="field-title")
        if not title_a:
            continue
        href = title_a.get("href")
        if not href:
            continue
        abs_url = urllib.parse.urljoin(listing_url, href)
        # Extract relative path without leading slash? urljoin handles
        # Get date span
        date_span = row.find("span", class_="date-display-single")
        date_text = date_span.get_text(strip=True) if date_span else None
        # Parse date like "14/10/2026" -> "2026-10-14"
        if date_text:
            try:
                # dateutil parser handles "14/10/2026"
                dt = parser.parse(date_text)
                date_str = dt.strftime("%Y-%m-%d")
            except Exception:
                # fallback simple split
                parts = date_text.split("/")
                if len(parts) == 3:
                    day, month, year = parts
                    date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                else:
                    continue
        else:
            continue
        
        # Fetch release page
        release_html = fetch(abs_url)
        release_soup = BeautifulSoup(release_html, "html.parser")
        
        # Title from release page h1.page-title
        title_elem = release_soup.find("h1", class_="page-title")
        title = title_elem.get_text(strip=True) if title_elem else ""
        
        # Date from field-date
        date_elem = release_soup.find("div", class_="field-date")
        date_text_release = date_elem.get_text(strip=True) if date_elem else ""
        # Extract date like "Date: 18/09/2026"
        if date_text_release.startswith("Date: "):
            date_val = date_text_release[6:].strip()
            try:
                dt_release = parser.parse(date_val)
                date_str_release = dt_release.strftime("%Y-%m-%d")
            except Exception:
                # fallback split
                parts = date_val.split("/")
                if len(parts) == 3:
                    day, month, year = parts
                    date_str_release = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                else:
                    date_str_release = date_str  # reuse listing date
        else:
            date_str_release = date_str
        
        # Author: look for author field? Not present in sample. Assume none.
        author = None
        
        # Body from field-body
        body_elem = release_soup.find("div", class_="field-body")
        if body_elem:
            # Get text of all paragraphs inside, preserving blank lines
            paragraphs = []
            for p in body_elem.find_all("p"):
                txt = p.get_text(separator="\n", strip=True)
                if txt:
                    paragraphs.append(txt)
            body_text = "\n".join(paragraphs)
        else:
            # fallback whole main text
            main = release_soup.find("main")
            if main:
                # get text of all children paragraphs? simple get text with <br> as newline
                text = main.get_text(separator="\n", strip=True)
                body_text = text
            else:
                body_text = ""
        
        # Build record
        record = {
            "url": abs_url,
            "title": title,
            "date": date_str_release,
            "author": author,
            "body": body_text
        }
        items.append(record)
    
    # Load more via API endpoint if exists
    load_more_btn = soup.find("button", class_="load-more")
    if load_more_btn and load_more_btn.get("data-endpoint"):
        endpoint = load_more_btn["data-endpoint"]
        # fetch JSON
        api_html = fetch(endpoint)  # fetch returns str; assume JSON text
        # parse JSON via eval? use dateutil? but only std lib + bs4 + dateutil
        # dateutil doesn't parse JSON; we need json module (standard)
        import json
        try:
            api_data = json.loads(api_html)
            items_api = api_data.get("items", [])
            for item in items_api:
                # item likely has href and maybe date? use href to construct abs url
                href = item.get("href")
                if href:
                    abs_url = urllib.parse.urljoin(listing_url, href)
                    # fetch release page
                    release_html = fetch(abs_url)
                    release_soup = BeautifulSoup(release_html, "html.parser")
                    title_elem = release_soup.find("h1", class_="page-title")
                    title = title_elem.get_text(strip=True) if title_elem else ""
                    date_elem = release_soup.find("div", class_="field-date")
                    date_text_release = date_elem.get_text(strip=True) if date_elem else ""
                    if date_text_release.startswith("Date: "):
                        date_val = date_text_release[6:].strip()
                        try:
                            dt_release = parser.parse(date_val)
                            date_str_release = dt_release.strftime("%Y-%m-%d")
                        except Exception:
                            # fallback
                            parts = date_val.split("/")
                            if len(parts) == 3:
                                day, month, year = parts
                                date_str_release = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                            else:
                                date_str_release = date_str  # not defined; skip
                    else:
                        date_str_release = None
                    # body
                    body_elem = release_soup.find("div", class_="field-body")
                    if body_elem:
                        paragraphs = []
                        for p in body_elem.find_all("p"):
                            txt = p.get_text(separator="\n", strip=True)
                            if txt:
                                paragraphs.append(txt)
                        body_text = "\n".join(paragraphs)
                    else:
                        body_text = ""
                    record = {
                        "url": abs_url,
                        "title": title,
                        "date": date_str_release if date_str_release else None,
                        "author": None,
                        "body": body_text
                    }
                    items.append(record)
        except Exception:
            pass
    
    # Sort newest first by date
    def get_date_key(rec):
        d = rec["date"]
        if d and d != "None":
            try:
                dt = parser.parse(d)
                return dt
            except Exception:
                return None
        return None
    
    items.sort(key=lambda rec: get_date_key(rec), reverse=True)
    
    # Filter out records with missing date
    records = [rec for rec in items if rec["date"] and rec["date"] != "None"]
    return records
