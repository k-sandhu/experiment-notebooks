import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser
from typing import List, Dict, Optional

# FetchError is assumed to be defined elsewhere; we do not redefine it.

def extract(fetch, listing_url: str):
    """
    Extract all press release records from the Meridian Ratings press listing.
    
    Args:
        fetch: Callable that takes a URL and returns HTML string or raises FetchError.
        listing_url: Absolute URL of the press listing page (e.g., "https://www.meridianratings.example/press/").
    
    Returns:
        List[Dict] with keys: url, title, date, author, body. Sorted newest first.
    """
    # Fetch the listing page (may contain loading placeholder)
    try:
        listing_html = fetch(listing_url)
    except Exception:
        # Propagate any fetch error as required
        raise

    # Also fetch the RSS feed which lists all releases
    feed_url = urllib.parse.urljoin(listing_url, '/press/feed.xml')
    try:
        feed_html = fetch(feed_url)
    except Exception:
        # If feed fetch fails, fall back to scanning listing page for links
        feed_html = None

    records = []

    # Helper to parse a release page
    def parse_release(rel_url: str, rel_html: str):
        soup = BeautifulSoup(rel_html, "html.parser")
        article = soup.find('article', class_='pr')
        if not article:
            return None

        # Title from <h1> inside article
        h1 = article.find('h1')
        title_text = h1.get_text(separator=' ', strip=True) if h1 else ""

        # Date from .pr-meta span (e.g., "29 September 2026")
        meta_div = article.find('div', class_='pr-meta')
        date_text = None
        if meta_div:
            # Find the first <span> that looks like a date (contains digits)
            spans = meta_div.find_all('span')
            for span in spans:
                txt = span.get_text(strip=True)
                if txt and any(c.isdigit() for c in txt):
                    date_text = txt
                    break

        # Author from .pr-meta .analyst span (e.g., "Written by Tomas Belwick")
        author_text = None
        if meta_div:
            analyst_span = meta_div.find('span', class_='analyst')
            if analyst_span:
                txt = analyst_span.get_text(strip=True)
                # Remove leading "Written by " (case-insensitive)
                lower_txt = txt.lower()
                if lower_txt.startswith('written by '):
                    txt = txt[11:].strip()  # len("Written by ") = 11
                # Keep possible "and" separated names; just clean trailing punctuation
                txt = txt.rstrip('.').strip()
                if txt:
                    author_text = txt

        # Body from .pr-body div paragraphs
        body_div = article.find('div', class_='pr-body')
        body_parts = []
        if body_div:
            paragraphs = body_div.find_all('p')
            for p in paragraphs:
                txt = p.get_text(separator=' ', strip=True)
                if txt:
                    body_parts.append(txt)
        body_text = '\n\n'.join(body_parts).strip() if body_parts else ""

        # Parse date to YYYY-MM-DD
        date_str = None
        if date_text:
            try:
                parsed = parser.parse(date_text, fuzzy=True)
                date_str = parsed.strftime('%Y-%m-%d')
            except Exception:
                pass

        # Normalize author: ensure no "and" lower-case etc.; just return cleaned string or None
        if author_text:
            # Remove possible trailing commas/periods
            author_text = author_text.replace(',', '').replace('.', '').strip()
            # If author text contains "and" already keep as is; spec says join with " and "
            # No extra processing needed.
            pass
        else:
            author_text = None

        return {
            "url": rel_url,
            "title": title_text,
            "date": date_str,
            "author": author_text,
            "body": body_text
        }

    # Process feed if available
    if feed_html:
        feed_soup = BeautifulSoup(feed_html, "xml")
        # RSS entries are <item>
        for item in feed_soup.find_all('item'):
            link_tag = item.find('link')
            if not link_tag or not link_tag.get('href'):
                continue
            link_href = link_tag.get('href')
            abs_link = urllib.parse.urljoin(listing_url, link_href) if not abs_link.startswith('http') else link_href
            # Fetch release page
            try:
                rel_html = fetch(abs_link)
            except Exception:
                continue
            record = parse_release(abs_link, rel_html)
            if record:
                records.append(record)

    # Fallback: if feed missing or empty, try to extract links from listing page
    if not feed_html or len(records) == 0:
        soup = BeautifulSoup(listing_html, "html.parser")
        # Look for <a> tags that point to press releases (contain '/press/' and a date segment)
        for link in soup.find_all('a', href=True):
            href = link['href']
            abs_url = urllib.parse.urljoin(listing_url, href)
            # Simple filter: path starts with /press/ and has at least year/month/day pattern
            parts = abs_url.split('/')
            if len(parts) >= 4 and parts[1] == 'www.meridianratings.example' and parts[2] == 'press':
                year_part = parts[3]
                if year_part.isdigit() and len(year_part) == 4:
                    # Fetch and parse
                    try:
                        rel_html = fetch(abs_url)
                    except Exception:
                        continue
                    record = parse_release(abs_url, rel_html)
                    if record:
                        records.append(record)

    # Sort by date descending; records without date go to end
    def sort_key(r):
        d = r['date']
        if d and len(d) == 10 and d[4] == '-' and d[7] == '-':
            try:
                return parser.parse(d, fuzzy=True)
            except Exception:
                return parser.parse('1900-01-01', fuzzy=True)
        return parser.parse('1900-01-01', fuzzy=True)

    records.sort(key=sort_key, reverse=True)
    return records
