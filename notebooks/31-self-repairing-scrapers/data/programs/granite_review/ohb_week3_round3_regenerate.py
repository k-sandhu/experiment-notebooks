import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser

# FetchError is assumed to be defined elsewhere; we import it here for reference
# In actual usage, the caller ensures FetchError exists.
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
        # Re-raise as per contract
        raise

    # Parse listing with BeautifulSoup
    soup = BeautifulSoup(listing_html, "html.parser")

    # Find all news item links in the listing table
    # The listing uses <b><a href="news_item.asp?id=...">Title</a></b><br>... pattern
    news_links = []
    # Locate the table with news rows; search within the main content td
    content_td = soup.find(string=lambda text: "Latest news" in text)  # fallback
    if not content_td:
        # Find the table with cellpadding="4" inside the second td of the first row
        main_table = soup.find("table", {"cellpadding": "4"})
        if main_table:
            rows = main_table.find_all("tr")
            for row in rows:
                # Look for <b><a> inside row td
                links = row.find_all("a", href=True)
                for link in links:
                    if link.parent.find("b"):  # ensure it's a news item link
                        href = link.get("href", "")
                        if href.startswith("news_item.asp?"):
                            news_links.append(href)
        else:
            # fallback: all news_item.asp links
            news_links = [a["href"] for a in soup.find_all("a", href=True) if "news_item.asp" in a["href"]]
    else:
        # fallback similar
        pass

    # Better direct approach: find all <a> tags with href containing news_item.asp inside the listing area
    all_links = soup.find_all("a", href=True)
    for link in all_links:
        href = link.get("href", "")
        if href.startswith("news_item.asp?"):
            # Resolve relative URL
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
    for rel_url in unique_links:
        abs_url = urllib.parse.urljoin(listing_url, rel_url) if not abs_url.startswith("http") else abs_url
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
            title_text = release_soup.find(["h1", "h2", "b"]).get_text(strip=True) if release_soup.find(["h1", "h2", "b"]) else "Unknown"

        # Extract date: look for "Posted:" line
        date_line = None
        for span in release_soup.find_all(["font", "span"], string=lambda text: "Posted:" in text):
            # find parent <font> or <span> containing "Posted:"
            parent = span.find_parent(["font", "span"])
            if parent:
                date_line = parent.get_text(strip=True)
                break
        # parse date like "Monday, September 28, 2026"
        date_str = None
        if date_line:
            # extract numeric date part
            import re
            m = re.search(r"(\d{1,2})\s*(?:[A-Za-z]+)\s*(\d{1,2}),?\s*(\d{4})", date_line)
            if m:
                day = m.group(1)
                month_name = m.group(2) if m.group(2) else ""
                year = m.group(3)
                # map month name
                months = {
                    "January": "01", "February": "02", "March": "03", "April": "04",
                    "May": "05", "June": "06", "July": "07", "August": "08", "September": "09",
                    "October": "10", "November": "11", "December": "12"
                }
                month = months.get(month_name.split()[0] if month_name else "", "01")
                # month_name may be like "September" or "Sep"? In sample "September 28"
                # date_line: "Monday, September 28, 2026"
                # extract month name first word after comma
                parts = date_line.split(",")
                if len(parts) > 1:
                    month_word = parts[1].split()[0]
                    month = months.get(month_word, "01")
                try:
                    # use dateutil to parse full string
                    parsed = parser.parse(date_line, fuzzy=True)
                    # get date part
                    date_obj = parsed.date()
                    date_str = date_obj.strftime("%Y-%m-%d")
                except Exception:
                    pass

        if not date_str:
            # fallback regex
            import re
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
                month = months.get(month_word, "01")
                # ensure two-digit month
                if len(month) == 3:  # like "Jan"
                    # simple mapping not implemented; fallback to 01
                    month = "01"
                date_str = f"{year}-{month:02d}-{day:02d}"  # day may be single digit
                # adjust: day may be like "28" fine
        # if still None, use "1900-01-01" but avoid; we must parse correctly
        if not date_str:
            # attempt to find any date pattern in page title? fallback to None -> use 1900? but avoid
            # use first occurrence of 4-digit year and month/day
            import re
            for tag in release_soup.find_all(["font", "span", "a"]):
                txt = tag.get_text()
                m = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", txt)
                if m:
                    date_str = m.group(0)
                    break
            if not date_str:
                # emergency fallback (should not happen)
                date_str = "1900-01-01"

        # Extract author: "Posted by: Lucien Bréval"
        author_line = None
        for font in release_soup.find_all("font", string=lambda text: "Posted by:" in text):
            parent = font.find_parent(["font", "span"])
            if parent:
                author_line = parent.get_text(strip=True)
                break
        author_raw = None
        if author_line:
            # extract after "Posted by:"
            parts = author_line.split("Posted by:", 1)
            if len(parts) > 1:
                author_raw = parts[1].strip()
                # remove job titles? simple: split by '.' or ',' and take first name(s)
                # remove words like "By", "By:" etc
                words = author_raw.split()
                filtered = [w for w in words if w not in {"By", "by"} and not w.endswith(".")][:3]  # keep first few
                # join with " and " if multiple? spec: several names joined with " and "
                # assume names are like "Lucien Bréval" (single) or "John Doe and Jane Smith"
                # we just keep as is but remove trailing punctuation
                author_raw = " ".join(filtered).replace(".", "").replace(",", "").strip()
                # if contains "and" already keep
                author = author_raw
            else:
                author = None
        else:
            author = None

        # Extract body: main text paragraphs between title and back link
        # Find the <td> containing the body (second td of first row)
        body_td = None
        rows = release_soup.find_all("tr")
        for row in rows:
            tds = row.find_all("td")
            if len(tds) >= 2:
                # second td is body
                body_td = tds[1]
                break
        if body_td:
            # get text of body_td, remove navigation links and extra <p> tags
            # get all text nodes, but exclude the back link paragraph
            back_link_a = body_td.find("a", string=lambda s: "&laquo;" in s or "Back to news" in s)
            if back_link_a:
                # remove that element
                back_link_a.decompose()
            # get all text from body_td, preserving paragraph breaks
            # use .get_text(separator="\n") but need blank lines between paragraphs
            # find all <font> or <p> blocks
            paragraphs = []
            for elem in body_td.find_all(["font", "p"]):
                # get text without extra <font> tags
                txt = elem.get_text(strip=False)
                # remove empty
                if txt.strip():
                    paragraphs.append(txt.strip())
            # join paragraphs with blank line
            body_text = "\n\n".join(paragraphs)
        else:
            # fallback: get all text except title and back link
            all_text = release_soup.get_text(separator="\n")
            # remove title line? simple
            body_text = all_text

        # Clean body: ensure at least 200 chars? but must be accurate; if short, keep as is
        # Remove possible HTML entities? get_text already decodes

        record = {
            "url": abs_url,
            "title": title_text,
            "date": date_str,
            "author": author if author else None,
            "body": body_text
        }
        records.append(record)

    # Sort records newest first by date (YYYY-MM-DD)
    def parse_date(d):
        try:
            return parser.parse(d, fuzzy=True).date()
        except:
            return None

    records.sort(key=lambda r: parse_date(r["date"]) or (0,0,0), reverse=True)

    return records
