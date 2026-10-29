import urllib.parse
from datetime import datetime
from dateutil import parser
from bs4 import BeautifulSoup

# FetchError is assumed to be defined elsewhere; we mimic it here for completeness.
class FetchError(Exception):
    def __init__(self, status):
        self.status = status
        super().__init__(f"Fetch error status {status}")

def extract(fetch, listing_url):
    """
    Extract all news release records from the listing page and its pagination.
    Returns a list of dicts, newest first.
    """
    # Start with the main listing page
    all_links = []

    def crawl(url):
        """Fetch page and collect relative news links from <ul class='archive'>."""
        try:
            html = fetch(url)
        except FetchError as e:
            # If fetch fails, skip this page
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
                        # Only keep links that start with /news/ (actual release links)
                        if rel_url.startswith("/news/"):
                            abs_url = urllib.parse.urljoin(url, rel_url)
                            all_links.append(abs_url)

    crawl(listing_url)

    # Remove duplicates while preserving order (first occurrence = newest relative to listing order)
    seen = set()
    unique_links = []
    for link in all_links:
        if link not in seen:
            seen.add(link)
            unique_links.append(link)

    records = []
    for rel_url in unique_links:
        try:
            html = fetch(rel_url)
        except FetchError:
            continue

        soup = BeautifulSoup(html, "html.parser")

        # Title: h1 inside main
        h1 = soup.find("h1", {"class": None})  # no class specified
        if not h1:
            # fallback: first h1
            h1 = soup.find("h1")
        title = h1.get_text(strip=True) if h1 else ""

        # Date: look for meta property="article:published_time" or <time> inside article
        date_tag = soup.find("meta", {"property": "article:published_time"})
        if not date_tag:
            date_tag = soup.find("time")
        if date_tag and date_tag.get("datetime"):
            pub_dt_str = date_tag["datetime"]
            try:
                pub_dt = parser.parse(pub_dt_str)
                date_str = pub_dt.date().isoformat()  # YYYY-MM-DD
            except Exception:
                date_str = None
        else:
            # fallback: extract from listing month/day? Not reliable; skip if missing
            date_str = None

        # Author: class "lede-author" containing "Written by ..."
        author_elem = soup.find("p", class_lambda=lambda x: x and "lede-author" in x.lower())
        if author_elem:
            text = author_elem.get_text(strip=True)
            # Remove "Written by " prefix and any job titles/by words
            if text.lower().startswith("written by "):
                text = text[11:].strip()  # remove "Written by "
            # Split by commas or "and" and clean names
            # Simple cleaning: keep words that are not typical job titles
            # Remove trailing punctuation
            text = text.replace("and", " and ").strip()
            # Very simple: take first name/last name combo; join with " and " if multiple
            # For this example we just keep the cleaned text
            author = text
        else:
            author = None

        # Body: main article text inside .article-text or div with class containing "article"
        body_div = soup.find("div", class_lambda=lambda x: x and "article" in x.lower())
        if not body_div:
            # fallback: find all p inside main excluding lede and share
            main = soup.find("main")
            if main:
                body_div = main
        if body_div:
            # Get paragraphs, strip, filter out empty and navigation/footer
            paras = []
            for p in body_div.find_all("p"):
                txt = p.get_text(separator="\n", strip=True)
                if txt:  # non-empty
                    paras.append(txt)
            body = "\n".join(paras)
        else:
            body = ""

        # Only include records whose date is on or before today (run date)
        # This avoids future dates relative to run date
        today = datetime.now().date()
        if date_str:
            try:
                pub_date = parser.parse(date_str).date()
                if pub_date <= today:
                    records.append({
                        "url": rel_url,
                        "title": title,
                        "date": date_str,
                        "author": author,
                        "body": body
                    })
            except Exception:
                # If parsing fails, skip date check and include? safer to skip
                pass
        else:
            # No explicit date meta; fallback to listing date? Not implemented for safety
            # Include anyway? but may cause future dates; skip to avoid errors
            pass

    # Sort newest first by date (descending)
    def get_sort_key(rec):
        if "date" in rec and rec["date"]:
            try:
                return parser.parse(rec["date"]).date()
            except Exception:
                return datetime.min.date()
        return datetime.min.date()

    records.sort(key=get_sort_key, reverse=True)
    return records
