import urllib.parse
import json
from bs4 import BeautifulSoup
from dateutil import parser

# FetchError is assumed to be defined elsewhere; we only use fetch as provided

def extract(fetch, listing_url):
    listing_html = fetch(listing_url)
    soup = BeautifulSoup(listing_html, "html.parser")
    
    items = []
    
    # Find all news items in the main content area from pagination rows
    rows = soup.find_all("div", class_="views-row")
    for row in rows:
        title_a = row.find("a", class_="field-title")
        if not title_a:
            continue
        href = title_a.get("href")
        if not href:
            continue
        abs_url = urllib.parse.urljoin(listing_url, href)
        
        date_span = row.find("span", class_="date-display-single")
        date_text = date_span.get_text(strip=True) if date_span else None
        if not date_text:
            continue
        
        # Parse listing date (e.g., "14/10/2026")
        try:
            dt = parser.parse(date_text)
            listing_date_str = dt.strftime("%Y-%m-%d")
        except Exception:
            # fallback split
            parts = date_text.split("/")
            if len(parts) == 3:
                day, month, year = parts
                listing_date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            else:
                continue
        
        # Fetch release page
        release_html = fetch(abs_url)
        release_soup = BeautifulSoup(release_html, "html.parser")
        
        # Title from release page h1.page-title
        title_elem = release_soup.find("h1", class_="page-title")
        title = title_elem.get_text(strip=True) if title_elem else ""
        
        # Date from field-date on release page
        date_elem = release_soup.find("div", class_="field-date")
        date_text_release = date_elem.get_text(strip=True) if date_elem else ""
        date_str_release = None
        if date_text_release.startswith("Date: "):
            date_val = date_text_release[6:].strip()
            try:
                dt_release = parser.parse(date_val)
                date_str_release = dt_release.strftime("%Y-%m-%d")
            except Exception:
                parts = date_val.split("/")
                if len(parts) == 3:
                    day, month, year = parts
                    date_str_release = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        # Author: look for author field? Not present in sample. Assume none.
        author = None
        
        # Body from field-body
        body_elem = release_soup.find("div", class_="field-body")
        body_text = ""
        if body_elem:
            paragraphs = []
            for p in body_elem.find_all("p"):
                txt = p.get_text(separator="\n", strip=True)
                if txt:
                    paragraphs.append(txt)
            body_text = "\n".join(paragraphs)
        else:
            # fallback whole main text (simple)
            main = release_soup.find("main")
            if main:
                paras = []
                for p in main.find_all("p"):
                    txt = p.get_text(separator="\n", strip=True)
                    if txt:
                        paras.append(txt)
                body_text = "\n".join(paras)
        
        record = {
            "url": abs_url,
            "title": title,
            "date": date_str_release if date_str_release else listing_date_str,
            "author": author,
            "body": body_text
        }
        items.append(record)
    
    # Load more via API endpoint if exists
    load_more_btn = soup.find("button", class_="load-more")
    if load_more_btn and load_more_btn.get("data-endpoint"):
        endpoint = load_more_btn["data-endpoint"]
        # Ensure absolute URL
        if not endpoint.startswith(("http://", "https://")):
            endpoint = urllib.parse.urljoin(listing_url, endpoint)
        api_html = fetch(endpoint)
        try:
            api_data = json.loads(api_html)
            items_api = api_data.get("items", [])
            for item in items_api:
                href = item.get("url") or item.get("href")
                if href:
                    abs_url = urllib.parse.urljoin(listing_url, href)
                    # Check if already fetched from rows (simple exact match)
                    already_fetched = any(rec["url"] == abs_url for rec in items)
                    if not already_fetched:
                        release_html = fetch(abs_url)
                        release_soup = BeautifulSoup(release_html, "html.parser")
                        
                        title_elem = release_soup.find("h1", class_="page-title")
                        title = title_elem.get_text(strip=True) if title_elem else ""
                        
                        date_elem = release_soup.find("div", class_="field-date")
                        date_text_release = date_elem.get_text(strip=True) if date_elem else ""
                        date_str_release = None
                        if date_text_release.startswith("Date: "):
                            date_val = date_text_release[6:].strip()
                            try:
                                dt_release = parser.parse(date_val)
                                date_str_release = dt_release.strftime("%Y-%m-%d")
                            except Exception:
                                parts = date_val.split("/")
                                if len(parts) == 3:
                                    day, month, year = parts
                                    date_str_release = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                        
                        body_elem = release_soup.find("div", class_="field-body")
                        body_text = ""
                        if body_elem:
                            paragraphs = []
                            for p in body_elem.find_all("p"):
                                txt = p.get_text(separator="\n", strip=True)
                                if txt:
                                    paragraphs.append(txt)
                            body_text = "\n".join(paragraphs)
                        else:
                            main = release_soup.find("main")
                            if main:
                                paras = []
                                for p in main.find_all("p"):
                                    txt = p.get_text(separator="\n", strip=True)
                                    if txt:
                                        paras.append(txt)
                                body_text = "\n".join(paras)
                        
                        author = None  # no author field observed
                        record = {
                            "url": abs_url,
                            "title": title,
                            "date": date_str_release if date_str_release else None,
                            "author": author,
                            "body": body_text
                        }
                        items.append(record)
        except Exception:
            # ignore API errors
            pass
    
    # Sort newest first by release date (prefer release date over listing date)
    def get_date_key(rec):
        d = rec["date"]
        if d and d != "None" and d != "":
            try:
                dt = parser.parse(d)
                return dt
            except Exception:
                return None
        return None
    
    items.sort(key=lambda rec: get_date_key(rec), reverse=True)
    
    # Filter out records with missing date (should not happen)
    records = [rec for rec in items if rec["date"] and rec["date"] not in (None, "None", "")]
    return records
