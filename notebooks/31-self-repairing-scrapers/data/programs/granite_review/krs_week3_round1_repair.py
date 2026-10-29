import urllib.parse
import json
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
    all_listing_urls = []

    # Fetch initial listing page
    try:
        html = fetch(listing_url)
    except FetchError as e:
        if e.status >= 400:
            return records
        else:
            raise

    soup = BeautifulSoup(html, "html.parser")

    # Collect all article links from listing rows
    for row in soup.find_all("div", class_="views-row"):
        title_a = row.find("a", class_="field-title")
        date_span = row.find("span", class_="date-display-single")
        if title_a and date_span:
            rel_href = title_a.get("href")
            if rel_href:
                abs_url = urllib.parse.urljoin(listing_url, rel_href)
                if abs_url not in seen_urls:
                    seen_urls.add(abs_url)
                    all_listing_urls.append((abs_url, date_span.get_text(strip=True), title_a.get_text(strip=True)))

    # Follow load-more button to get remaining items via API endpoint
    load_more_btn = soup.find("button", class_="load-more")
    if load_more_btn and load_more_btn.get("data-endpoint"):
        api_endpoint = load_more_btn["data-endpoint"]
        abs_api_url = urllib.parse.urljoin(listing_url, api_endpoint)
        try:
            api_html = fetch(abs_api_url)
            api_data = json.loads(api_html)
            if "items" in api_data:
                for item in api_data["items"]:
                    rel_href = item.get("url", "")
                    if rel_href:
                        abs_url = urllib.parse.urljoin(listing_url, rel_href)
                        if abs_url not in seen_urls:
                            seen_urls.add(abs_url)
                            # Extract date from item if present, else skip date sorting here
                            all_listing_urls.append((abs_url, "", ""))
        except FetchError as e:
            if e.status >= 400:
                pass  # ignore API fetch failure
            else:
                raise
        except Exception:
            pass  # ignore JSON parse issues

    # Sort all collected listing URLs by date descending
    def parse_date(date_str):
        try:
            return parser.parse(date_str, dayfirst=True)
        except Exception:
            return None

    dated_urls = []
    for abs_url, date_str, _ in all_listing_urls:
        date_span = None
        # Find date span in the listing row that corresponds to abs_url
        # Simple approach: reuse date_str from collection if available
        if date_str:
            dt = parse_date(date_str)
            if dt:
                dated_urls.append((dt, abs_url, date_str))
        else:
            # fallback: parse from page again quickly (optional, but safe)
            try:
                html2 = fetch(abs_url)
                soup2 = BeautifulSoup(html2, "html.parser")
                row = soup2.find("div", class_="views-row")
                if row:
                    date_span = row.find("span", class_="date-display-single")
                    if date_span:
                        dt = parse_date(date_span.get_text(strip=True))
                        if dt:
                            dated_urls.append((dt, abs_url, date_span.get_text(strip=True)))
            except FetchError:
                pass

    dated_urls.sort(key=lambda x: x[0], reverse=True)

    # Process each unique release URL
    for _, abs_url, _ in dated_urls:
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

        # Title
        h1 = release_soup.find("h1", class_="page-title")
        title = h1.get_text(strip=True) if h1 else ""

        # Date from field-date
        date_div = release_soup.find("div", class_="field-date")
        date_text = date_div.get_text(strip=True) if date_div else ""
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
            # Simple filter: drop common words that are not names
            stop_words = {"by", "contact", "news", "office", "revenue", "service"}
            filtered = [p for p in parts if p.lower() not in stop_words]
            if filtered:
                # Join with " and " only if multiple names; simple join with " and "
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
                # Clean up multiple newlines/spaces
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

    # Sort records by publication date descending
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
