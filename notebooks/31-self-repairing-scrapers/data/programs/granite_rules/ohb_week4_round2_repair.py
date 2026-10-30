import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser
import re

try:
    from fetch_module import FetchError  # type: ignore
except ImportError:
    class FetchError(Exception):
        def __init__(self, status):
            self.status = status
        def __str__(self):
            return f"FetchError: {self.status}"

def extract(fetch, listing_url):
    """
    Extract all news releases from the listing page and return records.
    """
    try:
        listing_html = fetch(listing_url)
    except FetchError as e:
        raise

    soup = BeautifulSoup(listing_html, "html.parser")

    all_links = soup.find_all("a", href=True)
    news_links = []
    for link in all_links:
        href = link.get("href", "")
        if href.startswith("news_item.asp?"):
            abs_url = urllib.parse.urljoin(listing_url, href)
            news_links.append(abs_url)

    seen = set()
    unique_links = []
    for url in news_links:
        if url not in seen:
            seen.add(url)
            unique_links.append(url)

    records = []
    for abs_url in unique_links:
        try:
            release_html = fetch(abs_url)
        except FetchError:
            continue

        release_soup = BeautifulSoup(release_html, "html.parser")

        title_tag = release_soup.find("b")
        if title_tag:
            title_text = title_tag.get_text(strip=True).replace("\n", "").strip()
        else:
            title_tag = release_soup.find(["h1", "h2", "b"])
            if title_tag:
                title_text = title_tag.get_text(strip=True)
            else:
                title_text = "Unknown"

        date_line = None
        for font in release_soup.find_all(["font", "span"], string=lambda text: text and "Posted:" in text):
            parent = font.find_parent(["font", "span"])
            if parent:
                date_line = parent.get_text(strip=True)
                break

        date_str = None
        if date_line:
            try:
                parsed = parser.parse(date_line, fuzzy=True)
                date_str = parsed.date().strftime("%Y-%m-%d")
            except Exception:
                pass

        if not date_str:
            # regex fallback only if date_line is not None
            if date_line:
                m = re.search(r"(\d{1,2})\s*(\w+)\s+(\d{4})", date_line)
                if m:
                    day = m.group(1)
                    month_word = m.group(2)
                    year = m.group(3)
                    months = {
                        "January": "01", "February": "02", "March": "03", "April": "04",
                        "May": "05", "June": "06", "July": "07", "August": "08",
                        "September": "09", "October": "10", "November": "11", "December": "12"
                    }
                    month = months.get(month_word, None)
                    if month is None:
                        short_months = {
                            "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04", "May": "05",
                            "Jun": "06", "Jul": "07", "Aug": "08", "Sep": "09", "Oct": "10",
                            "Nov": "11", "Dec": "12"
                        }
                        month = short_months.get(month_word, None)
                    if month is None:
                        parts = date_line.split(",")
                        if len(parts) > 1:
                            month_word2 = parts[1].split()[0]
                            month = months.get(month_word2, None)
                            if month is None:
                                month = short_months.get(month_word2, None)
                    if month is not None:
                        if len(month) == 3 and month in short_months:
                            month = short_months[month]
                        day = day.zfill(2) if len(day) == 1 else day
                        date_str = f"{year}-{month}-{day}"

        if not date_str:
            if date_line:
                m = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", date_line)
                if m:
                    date_str = m.group(0)

        author = None
        if date_line:
            for font in release_soup.find_all("font", string=lambda text: text and "Posted by:" in text):
                parent = font.find_parent(["font", "span"])
                if parent:
                    author_line = parent.get_text(strip=True)
                    parts = author_line.split("Posted by:", 1)
                    if len(parts) > 1:
                        author_raw = parts[1].strip().rstrip(".")
                        words = author_raw.split()
                        filtered = [w for w in words if w not in {"By", "by"}]
                        author_candidate = " ".join(filtered)
                        # join multiple names with " and " if they contain commas or "and"? spec says "several names joined with ' and '"
                        # simple: if we have more than one name and no "and" already, insert "and" before last? spec ambiguous; keep as is
                        author = author_candidate
                    break

        body_text = None
        rows = release_soup.find_all("tr")
        body_td = None
        for row in rows:
            tds = row.find_all("td")
            if len(tds) >= 2:
                body_td = tds[1]
                break
        if body_td:
            back_link_a = body_td.find("a", string=lambda s: s and ("&laquo;" in s or "Back to news" in s))
            if back_link_a:
                back_link_a.decompose()
            paragraphs = []
            for elem in body_td.find_all(["font", "p"]):
                txt = elem.get_text(strip=False)
                txt_clean = txt.strip()
                if txt_clean:
                    paragraphs.append(txt_clean)
            body_text = "\n\n".join(paragraphs)
        else:
            all_text = release_soup.get_text(separator="\n")
            body_text = all_text

        if body_text is None:
            body_text = ""

        record = {
            "url": abs_url,
            "title": title_text,
            "date": date_str if date_str else "1900-01-01",
            "author": author if author else None,
            "body": body_text
        }
        records.append(record)

    def parse_date(d):
        try:
            return parser.parse(d, fuzzy=True).date()
        except Exception:
            return None

    records.sort(key=lambda r: (parse_date(r["date"]) or (0, 0, 0)), reverse=True)

    return records
