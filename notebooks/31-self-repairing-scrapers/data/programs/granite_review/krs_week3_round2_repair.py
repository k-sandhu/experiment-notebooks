import urllib.parse
from datetime import datetime
from dateutil import parser
from bs4 import BeautifulSoup

class FetchError(Exception):
    def __init__(self, status):
        self.status = status
        super().__init__(f"FetchError: HTTP {status}")

def extract(fetch, listing_url):
    records = []
    seen_urls = set()
    all_listing_urls = []  # list of (abs_url, pub_date_dt, date_str_raw)

    try:
        html = fetch(listing_url)
    except FetchError as e:
        if e.status >= 400:
            return records
        else:
            raise

    soup = BeautifulSoup(html, "html.parser")

    # Collect listing rows
    for row in soup.find_all("div", class_="views-row"):
        title_a = row.find("a", class_="field-title")
        date_span = row.find("span", class_="date-display-single")
        if title_a and date_span:
            rel_href = title_a.get("href")
            if rel_href:
                abs_url = urllib.parse.urljoin(listing_url, rel_href)
                if abs_url not in seen_urls:
                    seen_urls.add(abs_url)
                    date_str_raw = date_span.get_text(strip=True)
                    try:
                        dt = parser.parse(date_str_raw, dayfirst=True)
                        all_listing_urls.append((abs_url, dt, date_str_raw))
                    except Exception:
                        # fallback: store without datetime for later parsing
                        all_listing_urls.append((abs_url, None, date_str_raw))

    # Follow load-more button to get remaining items via API endpoint
    load_more_btn = soup.find("button", class_="load-more")
    if load_more_btn and load_more_btn.get("data-endpoint"):
        api_endpoint = load_more_btn["data-endpoint"]
        abs_api_url = urllib.parse.urljoin(listing_url, api_endpoint)
        try:
            api_html = fetch(abs_api_url)
            api_data = __import__("json").loads(api_html)
            if "items" in api_data:
                for item in api_data["items"]:
                    rel_href = item.get("url", "")
                    if rel_href:
                        abs_url = urllib.parse.urljoin(listing_url, rel_href)
                        if abs_url not in seen_urls:
                            seen_urls.add(abs_url)
                            date_str_raw = item.get("date", "")
                            try:
                                dt = parser.parse(date_str_raw, dayfirst=True)
                                all_listing_urls.append((abs_url, dt, date_str_raw))
                            except Exception:
                                all_listing_urls.append((abs_url, None, date_str_raw))
        except FetchError as e:
            if e.status >= 400:
                pass
            else:
                raise
        except Exception:
            pass

    # Sort all collected listing URLs by publication date descending
    dated_urls = []
    for abs_url, dt, date_str_raw in all_listing_urls:
        if dt is not None:
            dated_urls.append((dt, abs_url))
        else:
            # fallback parsing from page
            try:
                release_html = fetch(abs_url)
                soup2 = BeautifulSoup(release_html, "html.parser")
                row = soup2.find("div", class_="views-row")
                if row:
                    date_span = row.find("span", class_="date-display-single")
                    if date_span:
                        date_str_raw2 = date_span.get_text(strip=True)
                        dt2 = parser.parse(date_str_raw2, dayfirst=True)
                        dated_urls.append((dt2, abs_url))
            except FetchError:
                pass

    # Combine both lists and sort
    all_sorted = []
    for dt, abs_url in dated_urls:
        all_sorted.append((dt, abs_url))
    for abs_url, dt, _ in all_listing_urls:
        if dt is None:
            # already handled in fallback above; avoid duplicate
            continue
        all_sorted.append((dt, abs_url))

    all_sorted.sort(key=lambda x: x[0], reverse=True)

    # Process each unique release URL in order
    for dt, abs_url in all_sorted:
        if abs_url in seen_urls:
            continue
        seen_urls.add(abs_url)

        try:
            release_html = fetch(abs_url)
        except FetchError as e:
            if e.status >= 400:
                continue
            else:
                continue

        release_soup = BeautifulSoup(release_html, "html.parser")

        # Title from page title or page-title
        h1 = release_soup.find("h1", class_="page-title")
        title_elem = h1 if h1 else release_soup.find("title")
        title = title_elem.get_text(strip=True) if title_elem else ""

        # Date from field-date
        date_div = release_soup.find("div", class_="field-date")
        date_text = ""
        if date_div:
            date_text = date_div.get_text(strip=True)
        date_str = ""
        if date_text.startswith("Date:"):
            date_str = date_text.split(":", 1)[1].strip()
        else:
            date_str = date_text.strip()

        try:
            dt_pub = parser.parse(date_str, dayfirst=True)
            pub_date = dt_pub.date().isoformat()
        except Exception:
            pub_date = ""

        # Author
        author = None
        meta_author = release_soup.find("meta", {"name": "author"})
        if meta_author and meta_author.get("content"):
            raw_author = meta_author["content"].strip()
            parts = [p.strip() for p in raw_author.split() if p.strip()]
            stop_words = {"by", "contact", "news", "office", "revenue", "service"}
            filtered = [p for p in parts if p.lower() not in stop_words]
            if filtered:
                if len(filtered) == 1:
                    author = filtered[0]
                else:
                    author = " and ".join(filtered)

        # Body
        body_div = release_soup.find("div", class_="field-body")
        body_text = ""
        if body_div:
            paragraphs = []
            for elem in body_div.find_all(["p", "li"]):
                text = elem.get_text(separator="\n", strip=True)
                lines = [line.strip() for line in text.splitlines() if line.strip()]
                paragraphs.append("\n".join(lines))
            body_text = "\n\n".join(paragraphs)

        record = {
            "url": abs_url,
            "title": title,
            "date": pub_date,
            "author": author,
            "body": body_text,
        }
        records.append(record)

    # Sort records by publication date descending (already in order from listing, but ensure)
    def rec_date_key(rec):
        d = rec["date"]
        if isinstance(d, str) and len(d) == 10 and d[4] == "-" and d[7] == "-":
            try:
                return datetime.fromisoformat(d)
            except Exception:
                return datetime.min
        return datetime.min

    records.sort(key=rec_date_key, reverse=True)
    return records
