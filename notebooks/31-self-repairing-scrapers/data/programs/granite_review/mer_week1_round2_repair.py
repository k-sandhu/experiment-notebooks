import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser
from typing import List, Dict

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
    try:
        listing_html = fetch(listing_url)
    except Exception:
        raise

    feed_url = urllib.parse.urljoin(listing_url, '/press/feed.xml')
    feed_html = None
    try:
        feed_html = fetch(feed_url)
    except Exception:
        pass

    records = []

    def parse_release(rel_url: str, rel_html: str):
        soup = BeautifulSoup(rel_html, "html.parser")
        article = soup.find('article', class_='pr')
        if not article:
            return None

        h1 = article.find('h1')
        title_text = h1.get_text(separator=' ', strip=True) if h1 else ""

        meta_div = article.find('div', class_='pr-meta')
        date_text = None
        if meta_div:
            spans = meta_div.find_all('span')
            for span in spans:
                txt = span.get_text(strip=True)
                if txt and any(c.isdigit() for c in txt):
                    date_text = txt
                    break

        author_text = None
        if meta_div:
            analyst_span = meta_div.find('span', class_='analyst')
            if analyst_span:
                txt = analyst_span.get_text(strip=True)
                lower_txt = txt.lower()
                if lower_txt.startswith('written by '):
                    txt = txt[11:].strip()
                txt = txt.rstrip('.').strip()
                if txt:
                    # Normalize "and" to lower case? keep as is
                    author_text = txt

        body_div = article.find('div', class_='pr-body')
        body_parts = []
        if body_div:
            paragraphs = body_div.find_all('p')
            for p in paragraphs:
                txt = p.get_text(separator=' ', strip=True)
                if txt:
                    body_parts.append(txt)
        body_text = '\n\n'.join(body_parts).strip() if body_parts else ""

        date_str = None
        if date_text:
            try:
                parsed = parser.parse(date_text, fuzzy=True)
                date_str = parsed.strftime('%Y-%m-%d')
            except Exception:
                pass

        # Clean author: ensure single " and " separator, lower case "and"? spec says "and"
        if author_text:
            # Remove possible trailing commas/periods already done
            # Join multiple names if present? meta only contains one name.
            author_text = author_text.strip()
        else:
            author_text = None

        return {
            "url": rel_url,
            "title": title_text,
            "date": date_str,
            "author": author_text,
            "body": body_text
        }

    if feed_html:
        feed_soup = BeautifulSoup(feed_html, "xml")
        for item in feed_soup.find_all('item'):
            link_tag = item.find('link')
            if not link_tag or not link_tag.get('href'):
                continue
            link_href = link_tag.get('href')
            # links in feed are absolute already
            abs_link = link_href
            try:
                rel_html = fetch(abs_link)
            except Exception:
                continue
            record = parse_release(abs_link, rel_html)
            if record:
                records.append(record)

    # No fallback needed; feed provides all releases
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
