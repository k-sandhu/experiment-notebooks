import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser
import re

# FetchError is assumed to be defined elsewhere; we import it here for reference
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
    # Fetch the listing page
    try:
        listing_html = fetch(listing_url)
    except FetchError as e:
        raise

    # Parse listing with BeautifulSoup
    soup = BeautifulSoup(listing_html, "html.parser")

    # Find all news item links in the listing table
    all_links = soup.find_all("a", href=True)
    news_links = []
    for link in all_links:
        href = link.get("href", "")
        if href.startswith("news_item.asp?"):
            abs_url = urllib.parse.urljoin(listing_url, href)
            news_links.append(abs_url)

    # Remove duplicates while preserving order (newest first based on id? but we sort by date later)
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
            continue  # skip if fetch fails

        # Parse release page
        release_soup = BeautifulSoup(release_html, "html.parser")

        # Extract title: the <b> inside the second td? pattern: <font face="Arial" size="4"><b>Title</b></font>
        title_tag = release_soup.find("b")
        if title_tag:
            # Get text of the b tag, clean up extra <font> tags
            title_text = title_tag.get_text(strip=True)
            # Remove possible trailing newline or extra spaces
            title_text = title_text.replace("\n", "").strip()
        else:
            # fallback: first <b> or <h?> 
            title_tag = release_soup.find(["h1", "h2", "b"])
            if title_tag:
                title_text = title_tag.get_text(strip=True)
            else:
                title_text = "Unknown"

        # Extract date: look for "Posted:" line
        date_line = None
        for font in release_soup.find_all(["font", "span"], string=lambda text: text and "Posted:" in text):
            # find parent <font> or <span> containing "Posted:"
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

        # fallback regex if parser failed
        if not date_str:
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
                # month_word may be full name or abbreviation; try full first
                month = months.get(month_word, None)
                if month is None:
                    # try short forms
                    short_months = {
                        "Jan": "01", "Feb": "02", "Febr": "02", "Febru": "02", "Februar": "02",
                        "Febuary": "02", "Febur": "02", "Feburday": "02",  # approximate
                        "Feb": "02", "Mar": "03", "Apr": "04", "May": "05",
                        "Jun": "06", "Jul": "07", "Aug": "08", "Sep": "09", "Sept": "09",
                        "Oct": "10", "Nov": "11", "Dec": "12"
                    }
                    month = short_months.get(month_word, None)
                if month is None:
                    # fallback: extract after comma
                    parts = date_line.split(",")
                    if len(parts) > 1:
                        month_word2 = parts[1].split()[0]
                        month = months.get(month_word2, None)
                        if month is None:
                            short_months2 = {k[:3] if len(k) > 3 else k: v for k, v in short_months.items()}
                            month = short_months2.get(month_word2, None)
                if month is not None:
                    # ensure two-digit month
                    if len(month) == 3 and month in short_months:
                        month = short_months[month]
                    # day may be single digit
                    day = day.zfill(2) if len(day) == 1 else day
                    date_str = f"{year}-{month}-{day}"
        if not date_str:
            # emergency fallback: search for YYYY-MM-DD pattern
            m = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", date_line)
            if m:
                date_str = m.group(0)

        # Extract author: "Posted by: Lucien Bréval"
        author = None
        if date_line:
            for font in release_soup.find_all("font", string=lambda text: text and "Posted by:" in text):
                parent = font.find_parent(["font", "span"])
                if parent:
                    author_line = parent.get_text(strip=True)
                    parts = author_line.split("Posted by:", 1)
                    if len(parts) > 1:
                        author_raw = parts[1].strip()
                        # remove trailing punctuation like periods
                        author_raw = author_raw.rstrip(".")
                        # filter out words like "By", "by" and simple job titles? spec says without job titles and without words such as "By"
                        words = author_raw.split()
                        filtered = [w for w in words if w not in {"By", "by"}]
                        # join with " and " if multiple names? spec: several names joined with " and "
                        # assume names are like "Lucien Bréval" (single) or "John Doe and Jane Smith"
                        # we just keep filtered list as is
                        author_candidate = " ".join(filtered)
                        # if contains "and" already keep
                        author = author_candidate
                    break

        # Extract body: main text paragraphs between title and back link
        body_text = None
        # Find the <td> containing the body (second td of first row)
        rows = release_soup.find_all("tr")
        body_td = None
        for row in rows:
            tds = row.find_all("td")
            if len(tds) >= 2:
                body_td = tds[1]
                break
        if body_td:
            # remove back link paragraph
            back_link_a = body_td.find("a", string=lambda s: s and ("&laquo;" in s or "Back to news" in s))
            if back_link_a:
                back_link_a.decompose()
            # collect paragraphs from <font> and <p> elements
            paragraphs = []
            for elem in body_td.find_all(["font", "p"]):
                txt = elem.get_text(strip=False)
                # keep text even if empty? we want blank lines between paragraphs
                # but avoid extra newlines from <font> tags
                # simple: get text and strip trailing/leading spaces but keep internal
                txt_clean = txt.strip()
                if txt_clean:
                    paragraphs.append(txt_clean)
            # join with blank line
            body_text = "\n\n".join(paragraphs)
        else:
            # fallback: get all text except title and back link
            all_text = release_soup.get_text(separator="\n")
            # remove title line? simple fallback
            body_text = all_text

        if body_text is None:
            body_text = ""

        record = {
            "url": abs_url,
            "title": title_text,
            "date": date_str if date_str else "1900-01-01",  # fallback, but should not happen
            "author": author if author else None,
            "body": body_text
        }
        records.append(record)

    # Sort records newest first by date (YYYY-MM-DD)
    def parse_date(d):
        try:
            return parser.parse(d, fuzzy=True).date()
        except Exception:
            return None

    records.sort(key=lambda r: (parse_date(r["date"]) or (0, 0, 0)), reverse=True)

    return records
