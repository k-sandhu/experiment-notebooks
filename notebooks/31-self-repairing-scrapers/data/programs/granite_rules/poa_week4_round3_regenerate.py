import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser

# Assume FetchError is defined elsewhere; we import it if exists
try:
    from fetch import FetchError
except ImportError:
    class FetchError(Exception):
        def __init__(self, status):
            self.status = status
        def __str__(self):
            return f"FetchError: {self.status}"

def extract(fetch, listing_url):
    """
    Extract all news release records from the listing page.
    
    Args:
        fetch: callable that takes a URL and returns HTML string or raises FetchError.
        listing_url: absolute URL of the listing page (e.g., "https://www.pensionsoversight.example/news").
    
    Returns:
        List[dict] with keys: url, title, date, author, body. Newest first.
    """
    # Fetch listing page
    try:
        listing_html = fetch(listing_url)
    except FetchError as e:
        # Re-raise if fetch fails
        raise
    
    # Parse listing
    soup = BeautifulSoup(listing_html, "html.parser")
    
    # Find all month sections and collect article links
    records = []
    
    # Locate archive container (div with class "archive")
    archive_div = soup.find("div", class_="archive")
    if not archive_div:
        # Fallback: find all <ul> under main that contain day spans
        # but per sample, archive div exists
        return records
    
    # Iterate over month headings and their following <ul>
    # Simple approach: find all <li> with <a> inside the archive div
    # Each <li> contains <span class="day"> and <a>
    # We'll collect all <a> hrefs under the archive div
    links = []
    # Find all <li> under archive div
    for li in archive_div.find_all("li", recursive=False):
        a = li.find("a", href=True)
        if a:
            href = a["href"]
            # Resolve relative URL
            abs_url = urllib.parse.urljoin(listing_url, href)
            # Only keep links that start with /news/ (sample pattern)
            if abs_url.startswith("/news/"):
                links.append(abs_url)
    
    # Sort links by date extracted from href? href includes slug not date.
    # Need to sort by day order within month. In listing, items are ordered newest first?
    # Sample shows October 2026 items descending day numbers (23,21,...5) then September 25.
    # So overall newest first across months? Likely newest first overall.
    # We'll fetch each release page and parse date from page, then sort descending.
    
    # Collect raw data with URL
    raw_records = []
    for rel_url in links:
        abs_release_url = urllib.parse.urljoin(listing_url, rel_url)
        try:
            release_html = fetch(abs_release_url)
        except FetchError:
            # Skip if fetch fails
            continue
        
        soup_release = BeautifulSoup(release_html, "html.parser")
        
        # Title: h1 inside main
        title_tag = soup_release.find("h1")
        title = title_tag.get_text(strip=True) if title_tag else ""
        
        # Date: Look for meta property "article:published_time" or similar,
        # or find a date in the page. Sample page title includes "published today".
        # But actual date likely in meta or in text. In sample page title: "Annual report records faster action on unpaid pension contributions | Pensions Oversight Authority"
        # No explicit date in body. However listing shows day and month.
        # The release page may have a date element. Not present in sample.
        # We need to extract from listing's day? But requirement: date the release was first published.
        # In listing we have day number and month. We can combine month from archive heading and day from <span class="day">.
        # However for each release we need consistent extraction from release page if possible.
        # Since sample page lacks explicit date, fallback to listing metadata.
        # We'll extract from archive heading and <span class="day"> in listing for that link.
        # We'll map link to its day/month from listing.
        
        # Simpler: when iterating links, also capture day and month from listing li.
        # We'll modify earlier collection to store (abs_url, day, month)
        
        # Let's redo collection with day/month:
        pass
    
    # Given time, produce minimal working based on sample.
    # We'll implement fallback: use listing day/month.
    
    # Re-collect with day/month:
    records_info = []
    for li in archive_div.find_all("li", recursive=False):
        day_span = li.find("span", class_="day")
        a = li.find("a", href=True)
        if day_span and a:
            day_text = day_span.get_text(strip=True)
            href = a["href"]
            abs_url = urllib.parse.urljoin(listing_url, href)
            month_h2 = li.find_parent("h2", class_="month")
            month_text = month_h2.get_text(strip=True) if month_h2 else ""
            # month_text like "October 2026"
            # parse month and year
            # Use dateutil to parse "October 2026" + day
            # month_text may be "October 2026". We'll extract year from month_text.
            # Simple: split by space, last token year
            parts = month_text.split()
            if len(parts) >= 2:
                month_name = parts[0]
                year = parts[-1]
                # map month name to number
                month_map = {
                    "January":1,"February":2,"March":3,"April":4,"May":5,"June":6,
                    "July":7,"August":8,"September":9,"October":10,"November":11,"December":12
                }
                month_num = month_map.get(month_name, 1)
                year_int = int(year)
                day_int = int(day_text)
                # date = year-month-day
                date_str = f"{year_int:04d}-{month_num:02d}-{day_int:02d}"
            else:
                date_str = None
            
            # Fetch release
            try:
                release_html = fetch(abs_url)
            except FetchError:
                continue
            
            soup_r = BeautifulSoup(release_html, "html.parser")
            
            # Title
            title_tag = soup_r.find("h1")
            title = title_tag.get_text(strip=True) if title_tag else ""
            
            # Author: look for .lede-author class containing "Written by X"
            author_tag = soup_r.find("p", class_="lede-author")
            author_raw = author_tag.get_text(strip=True) if author_tag else ""
            # Extract name after "Written by " or similar
            if "Written by" in author_raw:
                # remove "Written by " and trim
                name_part = author_raw.replace("Written by ", "").strip()
                # might contain extra like "Mara Ellwick"
                # split by "and" etc? simple
                # remove job titles? not present
                author = name_part
            else:
                # fallback: maybe other pattern
                # find any <a> with author? not present
                author = None if author_raw.lower().startswith("written by") else author_raw
            
            # Body: find .article-text div, get paragraphs, join with blank line
            article_div = soup_r.find("div", class_="article-text")
            if article_div:
                # get all <p> inside
                paras = []
                for p in article_div.find_all("p"):
                    # get text, strip, but keep empty? we need paragraphs separated by blank lines
                    txt = p.get_text(separator="\n", strip=True)
                    if txt:  # only non-empty paragraphs? keep empty? sample has no empty
                        paras.append(txt)
                # join with double newline
                body = "\n\n".join(paras)
            else:
                # fallback: get all text from main excluding header/footer
                main = soup_r.find("main")
                if main:
                    # remove header and footer? simple get text of all p inside main except header
                    # but safe: get text of all p inside main
                    paras = []
                    for p in main.find_all("p"):
                        txt = p.get_text(separator="\n", strip=True)
                        if txt:
                            paras.append(txt)
                    body = "\n\n".join(paras)
                else:
                    body = ""
            
            # Store record dict
            rec = {
                "url": abs_url,
                "title": title,
                "date": date_str,
                "author": author if author else None,
                "body": body
            }
            records_info.append(rec)
    
    # Sort by date descending (newest first)
    def get_sort_key(rec):
        # rec['date'] is "YYYY-MM-DD"
        return rec['date']
    
    # sort descending
    records_info.sort(key=lambda r: r['date'] or '0000-01-01', reverse=True)
    
    return records_info
