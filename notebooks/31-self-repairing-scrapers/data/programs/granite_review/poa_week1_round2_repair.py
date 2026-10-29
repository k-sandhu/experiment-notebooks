import urllib.parse
from datetime import datetime
from dateutil import parser
from bs4 import BeautifulSoup

# FetchError is assumed to be defined elsewhere; we only use fetch as provided

def extract(fetch, listing_url):
    """
    Extract all news release records from the listing page and its pagination.
    Returns a list of dicts, newest first.
    """
    records = []
    seen_urls = set()

    try:
        html = fetch(listing_url)
    except Exception:
        return records

    soup = BeautifulSoup(html, "html.parser")
    archive_divs = soup.find_all(class_="archive")

    for archive_div in archive_divs:
        month_h2 = archive_div.find(class_="month")
        if not month_h2:
            continue
        lis = archive_div.find_all("li", recursive=True)
        for li in lis:
            a = li.find("a", href=True)
            if not a:
                continue
            rel_url = a["href"]
            abs_url = urllib.parse.urljoin(listing_url, rel_url)
            if abs_url in seen_urls:
                continue
            seen_urls.add(abs_url)

            try:
                release_html = fetch(abs_url)
            except Exception:
                continue

            release_soup = BeautifulSoup(release_html, "html.parser")

            # Title from <h1>
            title_tag = release_soup.find("h1")
            title = title_tag.get_text(strip=True) if title_tag else ""

            # Extract date from listing (most reliable)
            day_span = li.find(class_="day")
            day = None
            if day_span:
                day_text = day_span.get_text(strip=True)
                try:
                    day = int(day_text)
                except ValueError:
                    day = None

            month_h2_text = month_h2.get_text(strip=True)
            # month_h2_text format: "September 2026"
            parts = month_h2_text.split()
            if len(parts) >= 2:
                year_part = parts[1]
                try:
                    year = int(year_part)
                except ValueError:
                    year = None
            else:
                year = None

            month_name = parts[0] if len(parts) >= 1 else None
            month = None
            if year and month_name:
                month_map = {
                    "January": 1, "February": 2, "March": 3, "April": 4,
                    "May": 5, "June": 6, "July": 7, "August": 8,
                    "September": 9, "October": 10, "November": 11, "December": 12
                }
                month = month_map.get(month_name, None)

            if day and year and month:
                date_str = f"{year:04d}-{month:02d}-{day:02d}"
            else:
                # Fallback: try <time> or meta date
                date_str = None
                date_tag = release_soup.find("time")
                if date_tag and date_tag.get("datetime"):
                    pub_date_str = date_tag["datetime"]
                    try:
                        dt = parser.parse(pub_date_str)
                        date_str = dt.strftime("%Y-%m-%d")
                    except Exception:
                        pass
                if not date_str:
                    meta_date = release_soup.find("meta", {"name": "date"})
                    if meta_date and meta_date.get("content"):
                        try:
                            dt = parser.parse(meta_date["content"])
                            date_str = dt.strftime("%Y-%m-%d")
                        except Exception:
                            pass

            # Author extraction
            author_tag = release_soup.find(class_="lede-author")
            author_clean = None
            if author_tag:
                author_raw = author_tag.get_text(strip=True)
                # Remove "Written by " prefix
                if author_raw.startswith("Written by "):
                    author_raw = author_raw[11:].strip()
                # Remove trailing job titles? Not required; just remove "By" if present
                if author_raw.lower().startswith("by "):
                    author_raw = author_raw[3:].strip()
                # Clean multiple spaces
                author_raw = author_raw.replace("  ", " ").strip()
                if author_raw:
                    # Simple join with " and " if multiple names? Assume single or "Name and Other" already formatted.
                    author_clean = author_raw

            # Body extraction from .article-text
            body_div = release_soup.find(class_="article-text")
            body_text = ""
            if body_div:
                paras = []
                for p in body_div.find_all("p", recursive=False):
                    txt = p.get_text(separator="\n", strip=True)
                    if txt:
                        paras.append(txt)
                body_text = "\n\n".join(paras)
            else:
                main = release_soup.find("main")
                if main:
                    paras = []
                    for elem in main.find_all(["p", "div"], recursive=False):
                        txt = elem.get_text(separator="\n", strip=True)
                        if txt:
                            paras.append(txt)
                    body_text = "\n\n".join(paras)

            # Validate date format
            date_final = None
            if date_str:
                try:
                    datetime.strptime(date_str, "%Y-%m-%d")
                    date_final = date_str
                except ValueError:
                    pass

            record = {
                "url": abs_url,
                "title": title if title else "",
                "date": date_final if date_final else None,
                "author": author_clean if author_clean else None,
                "body": body_text if body_text else "",
            }
            records.append(record)

    # Sort newest first by date descending
    def sort_key(r):
        if r["date"] and isinstance(r["date"], str):
            try:
                return datetime.strptime(r["date"], "%Y-%m-%d")
            except Exception:
                return datetime.min
        return datetime.min

    records.sort(key=sort_key, reverse=True)
    return records
