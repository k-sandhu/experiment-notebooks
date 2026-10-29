import urllib.parse
from datetime import datetime
from dateutil import parser
from bs4 import BeautifulSoup

class FetchError(Exception):
    def __init__(self, status):
        self.status = status
        super().__init__(f"Fetch error status {status}")

def extract(fetch, listing_url):
    all_links = []

    def crawl(url):
        try:
            html = fetch(url)
        except FetchError:
            return
        soup = BeautifulSoup(html, "html.parser")
        archive_divs = soup.find_all("div", class_="archive")
        for div in archive_divs:
            uls = div.find_all("ul")
            for ul in uls:
                for li in ul.find_all("li"):
                    a = li.find("a", href=True)
                    if a and a.get("href"):
                        rel_url = a["href"]
                        if rel_url.startswith("/news/"):
                            abs_url = urllib.parse.urljoin(url, rel_url)
                            all_links.append(abs_url)

    crawl(listing_url)

    seen = set()
    unique_links = []
    for link in all_links:
        if link not in seen:
            seen.add(link)
            unique_links.append(link)

    records = []
    for abs_url in unique_links:
        try:
            html = fetch(abs_url)
        except FetchError:
            continue

        soup = BeautifulSoup(html, "html.parser")

        h1 = soup.find("h1")
        title = h1.get_text(strip=True) if h1 else ""

        # Extract date from <time> or meta article:published_time
        date_tag = soup.find("meta", {"property": "article:published_time"})
        if not date_tag:
            date_tag = soup.find("time")
        date_str = None
        if date_tag:
            dt_attr = date_tag.get("datetime") or date_tag.get("date")
            if dt_attr:
                try:
                    pub_dt = parser.parse(dt_attr)
                    date_str = pub_dt.date().isoformat()
                except Exception:
                    pass

        # Fallback: extract from listing month/day inside same archive div
        if not date_str:
            archive_divs = soup.find_all("div", class_="archive")
            for div in archive_divs:
                month_h2 = div.find("h2", class_="month")
                if month_h2:
                    # Find ul under this div
                    uls = div.find_all("ul")
                    for ul in uls:
                        for li in ul.find_all("li"):
                            day_span = li.find("span", class_="day")
                            if day_span and day_span.get_text().isdigit():
                                day = int(day_span.get_text().strip())
                                # Get month name from h2
                                month_text = month_h2.get_text().strip()
                                # month_text like "October 2026" or "September 2026"
                                parts = month_text.split()
                                if len(parts) >= 2:
                                    month_word = parts[0]
                                    year_word = parts[1]
                                    month_map = {
                                        "January": 1, "February": 2, "March": 3, "April": 4,
                                        "May": 5, "June": 6, "July": 7, "August": 8,
                                        "September": 9, "October": 10, "November": 11, "December": 12
                                    }
                                    if month_word in month_map and year_word.isdigit():
                                        year = int(year_word)
                                        month = month_map[month_word]
                                        try:
                                            date_obj = datetime(year, month, day)
                                            date_str = date_obj.date().isoformat()
                                            break
                                        except ValueError:
                                            pass
                        if date_str:
                            break
                if date_str:
                    break

        # Author extraction
        author_elem = soup.find("p", class_lambda=lambda x: x and "lede-author" in x.lower())
        author = None
        if author_elem:
            text = author_elem.get_text(strip=True)
            # Remove "Written by " prefix (case insensitive)
            lower_text = text.lower()
            if lower_text.startswith("written by "):
                text = text[11:].strip()  # remove "Written by "
            # Clean trailing punctuation
            text = text.rstrip(".")
            # Extract names: split by commas or "and"
            parts = [p.strip() for p in text.split(",")]
            names = []
            for part in parts:
                subparts = [p.strip() for p in part.split("and")]
                names.extend(subparts)
            # Filter out empty and common job title indicators
            job_indicators = {"writes", "by", "author", "reporter", "staff"}
            filtered = [n for n in names if n and n.lower() not in job_indicators and n.lower() != "by"]
            if filtered:
                author = " and ".join(filtered)

        # Body extraction
        body = ""
        # Prefer div with class containing "article"
        body_div = soup.find("div", class_lambda=lambda x: x and "article" in x.lower())
        if not body_div:
            main = soup.find("main")
            if main:
                body_div = main
        if body_div:
            paras = []
            for p in body_div.find_all("p"):
                txt = p.get_text(separator="\n", strip=True)
                if txt:
                    paras.append(txt)
            body = "\n".join(paras)
        else:
            # fallback: collect all p inside main excluding lede and share
            main = soup.find("main")
            if main:
                paras = []
                for p in main.find_all("p"):
                    cls = p.get("class", [])
                    if any(kw in cls.lower() for kw in ["lede-author", "share"]):
                        continue
                    txt = p.get_text(separator="\n", strip=True)
                    if txt:
                        paras.append(txt)
                body = "\n".join(paras) if paras else ""

        # Only include if date_str is not None
        if date_str:
            records.append({
                "url": abs_url,
                "title": title,
                "date": date_str,
                "author": author,
                "body": body
            })

    # Sort newest first by date descending
    def get_sort_key(rec):
        date_str = rec.get("date")
        if not date_str:
            return datetime.min.date()
        try:
            pub_date = parser.parse(date_str).date()
            return pub_date
        except Exception:
            return datetime.min.date()

    records.sort(key=get_sort_key, reverse=True)
    return records
