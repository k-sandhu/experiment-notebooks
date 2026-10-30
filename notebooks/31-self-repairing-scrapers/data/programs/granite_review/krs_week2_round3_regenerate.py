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
    current_page = listing_url
    seen_urls = set()

    while True:
        try:
            html = fetch(current_page)
        except FetchError as e:
            if e.status >= 400:
                break
            else:
                continue

        soup = BeautifulSoup(html, "html.parser")

        # Find all news article links on this listing page
        article_links = []
        for row in soup.find_all("div", class_="views-row"):
            title_a = row.find("a", class_="field-title")
            if title_a and title_a.get("href"):
                href = title_a["href"]
                abs_url = urllib.parse.urljoin(listing_url, href)
                if abs_url not in seen_urls:
                    article_links.append(abs_url)
                    seen_urls.add(abs_url)

        # Sort links by date (newest first) based on date-display-single
        def get_date_text(row):
            date_span = row.find("span", class_="date-display-single")
            if date_span:
                return date_span.get_text(strip=True)
            return None

        def parse_date(date_str):
            try:
                # Handle format like "08/10/2026" (dd/mm/yyyy)
                return parser.parse(date_str, dayfirst=True)
            except Exception:
                return None

        dated_links = []
        for row in soup.find_all("div", class_="views-row"):
            date_span = row.find("span", class_="date-display-single")
            title_a = row.find("a", class_="field-title")
            if date_span and title_a:
                date_str = date_span.get_text(strip=True)
                dt = parse_date(date_str)
                if dt:
                    dated_links.append((dt, title_a["href"], date_span))

        # Sort by date descending
        dated_links.sort(key=lambda x: x[0], reverse=True)

        # Process only dated links to avoid duplicates
        for dt, rel_href, _ in dated_links:
            abs_url = urllib.parse.urljoin(listing_url, rel_href)
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
            # Extract "Date: 18/09/2026" -> "18/09/2026"
            match = None
            if date_text.startswith("Date:"):
                date_str = date_text.split(":", 1)[1].strip()
            else:
                date_str = date_text.strip()

            # Parse date safely
            try:
                dt_pub = parser.parse(date_str, dayfirst=True)
                pub_date = dt_pub.date().isoformat()
            except Exception:
                # Fallback: use first date from listing row if possible
                pub_date = None

            # Author
            author_div = release_soup.find("meta", {"name": "author"})
            author = None
            if author_div and author_div.get("content"):
                raw_author = author_div["content"].strip()
                # Remove job titles and "By" etc. simple cleanup
                parts = [p.strip() for p in raw_author.split(" ") if p.strip()]
                # Keep only names (very simple: drop words like "By", "Contact", etc.)
                filtered = [p for p in parts if p not in {"By", "Contact", "News"}]
                if filtered:
                    author = " and ".join(filtered)
            # If no meta author, check for author in header? Not present in sample
            # So author remains None

            # Body
            body_div = release_soup.find("div", class_="field-body")
            body_text = ""
            if body_div:
                # Get paragraphs and list items as text, preserve blank lines between paragraphs
                paragraphs = []
                for elem in body_div.find_all(["p", "ul", "li"]):
                    # For list items, join with space and treat as paragraph
                    if elem.name in ("p", "li"):
                        text = elem.get_text(separator="\n", strip=True)
                        # Normalize multiple spaces/newlines
                        text = "\n".join([line.strip() for line in text.splitlines() if line.strip()])
                        paragraphs.append(text)
                # Join paragraphs with blank line
                body_text = "\n\n".join(paragraphs)

            # Build record
            record = {
                "url": abs_url,
                "title": title,
                "date": pub_date if pub_date else "",  # ISO string or empty if parse failed
                "author": author,
                "body": body_text,
            }
            records.append(record)

        # Pagination: get next page link
        pager = soup.find("nav", class_="pager")
        if not pager:
            break

        next_link = None
        for a in pager.find_all("a", href=True):
            href = a["href"]
            if "page=2" in href or a.get("rel") and "next" in a["rel"].lower():
                next_link = urllib.parse.urljoin(listing_url, href)
                break

        if next_link and next_link not in seen_urls:
            current_page = next_link
        else:
            break

    # Sort records by publication date descending (newest first)
    def get_rec_date(rec):
        d = rec["date"]
        if isinstance(d, str) and len(d) == 10 and d[4] == "-" and d[7] == "-":
            try:
                parser.parse(d)
                return datetime.fromisoformat(d)
            except Exception:
                return datetime.min
        return datetime.min

    records.sort(key=get_rec_date, reverse=True)

    return records
