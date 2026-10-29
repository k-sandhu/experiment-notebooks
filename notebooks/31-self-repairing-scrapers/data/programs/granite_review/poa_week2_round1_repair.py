import urllib.parse
import re
from bs4 import BeautifulSoup
from dateutil import parser
from datetime import datetime

# FetchError is assumed to be defined elsewhere; we do not define it here.

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
    except Exception as e:
        raise  # propagate any exception from fetch

    soup = BeautifulSoup(listing_html, "html.parser")

    # Map month names to numbers for date construction
    month_map = {
        "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
        "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12
    }

    releases = []

    # Find all month headings and their associated list items
    month_sections = soup.find_all(class_="month")
    for month_elem in month_sections:
        month_text = month_elem.get_text(strip=True)
        # Extract year and month name from month_text like "September 2026"
        parts = month_text.split()
        if len(parts) < 2:
            continue
        year_str = parts[-1]
        month_name = parts[0]
        try:
            year = int(year_str)
        except ValueError:
            continue
        month_num = month_map.get(month_name)
        if month_num is None:
            continue

        # Find the following ul (list) within same parent or next sibling
        ul = month_elem.find_next("ul")
        if not ul:
            continue

        for li in ul.find_all("li"):
            day_span = li.find(class_="day")
            link_tag = li.find("a", href=True)
            if not link_tag or not link_tag.get("href"):
                continue
            rel_url = link_tag["href"]
            abs_url = urllib.parse.urljoin(listing_url, rel_url)

            # Fetch release page
            try:
                release_html = fetch(abs_url)
            except Exception:
                # Skip if fetch fails
                continue

            release_soup = BeautifulSoup(release_html, "html.parser")

            # Extract title: h1 inside main
            h1 = release_soup.find("h1")
            title = h1.get_text(strip=True) if h1 else ""

            # Extract date from listing (day) and month heading
            day_text = day_span.get_text(strip=True) if day_span else ""
            try:
                day = int(day_text)
            except ValueError:
                continue

            # Construct date: year from month heading, month from month name, day from day_span
            try:
                pub_date = datetime(year=year, month=month_num, day=day)
                date_str = pub_date.strftime("%Y-%m-%d")
            except ValueError:
                # Invalid day for month (e.g., day 31 in Feb), fallback to None (will be skipped)
                continue

            # Extract author: class "lede-author" contains "Written by X"
            lede = release_soup.find(class_="lede-author")
            author_raw = lede.get_text(strip=True) if lede else ""
            if author_raw.lower().startswith("written by "):
                author_raw = author_raw[len("written by "):].strip()
            # Clean simple: keep as is, but ensure no trailing punctuation
            author_clean = author_raw.strip()
            author = author_clean if author_clean else None

            # Extract body: class "article-text"
            article_text_tag = release_soup.find(class_="article-text")
            if article_text_tag:
                paragraphs = []
                for p in article_text_tag.find_all("p"):
                    txt = p.get_text(separator="\n", strip=True)
                    if txt:
                        paragraphs.append(txt)
                body = "\n\n".join(paragraphs)
            else:
                # Fallback: get text from main excluding header/footer? Not needed for sample.
                body = ""

            record = {
                "url": abs_url,
                "title": title,
                "date": date_str,
                "author": author,
                "body": body,
            }
            releases.append(record)

    # Sort releases newest first by date (YYYY-MM-DD string sorts lexicographically)
    releases.sort(key=lambda r: r["date"] or "1900-01-01", reverse=True)

    return releases
