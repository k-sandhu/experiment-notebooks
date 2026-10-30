import urllib.parse
from datetime import date
from dateutil import parser
from bs4 import BeautifulSoup

# FetchError is assumed to be defined elsewhere; we only use fetch as provided

def extract(fetch, listing_url):
    """
    Extract all news release records from the listing page and its pagination.
    Returns a list of dicts, newest first, for all releases currently on the listing.
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

            # Date extraction from release page first
            date_tag = release_soup.find("time")
            date_str = None
            if date_tag and date_tag.get("datetime"):
                pub_date_str = date_tag["datetime"]
                try:
                    dt = parser.parse(pub_date_str)
                    date_str = dt.strftime("%Y-%m-%d")
                except Exception:
                    pass
            else:
                meta_date = release_soup.find("meta", {"name": "date"})
                if meta_date and meta_date.get("content"):
                    try:
                        dt = parser.parse(meta_date["content"])
                        date_str = dt.strftime("%Y-%m-%d")
                    except Exception:
                        pass

            # Fallback to listing day/month/year if no page date
            if date_str is None:
                day_span = li.find(class_="day")
                if day_span:
                    day_text = day_span.get_text(strip=True)
                    try:
                        day = int(day_text)
                    except ValueError:
                        day = None
                else:
                    day = None

                month_h2_text = month_h2.get_text(strip=True)
                parts = month_h2_text.split()
                year = None
                month = None
                if len(parts) >= 2:
                    year_part = parts[1]
                    try:
                        year = int(year_part)
                    except ValueError:
                        year = None
                if len(parts) >= 1:
                    month_name = parts[0]
                    month_map = {
                        "January": 1, "February": 2, "March": 3, "April": 4,
                        "May": 5, "June": 6, "July": 7, "August": 8,
                        "September": 9, "October": 10, "November": 11, "December": 12
                    }
                    month = month_map.get(month_name, 1)
                if day and year and month:
                    date_str = f"{year:04d}-{month:02d}-{day:02d}"

            # Use date_str if available, otherwise skip (cannot verify)
            if date_str:
                # Validate format
                try:
                    datetime_obj = parser.parse(date_str)
                    # No filtering by today; include all releases
                    record = {
                        "url": abs_url,
                        "title": title if title else "",
                        "date": date_str,
                        "author": author_clean if author_clean else None,
                        "body": body_text if body_text else "",
                    }
                    records.append(record)
                except Exception:
                    # If parsing fails, skip record
                    pass

    # Sort newest first by date descending
    def sort_key(r):
        if r["date"]:
            try:
                return parser.parse(r["date"]).date()
            except Exception:
                return date.min
        return date.min

    records.sort(key=sort_key, reverse=True)
    return records
