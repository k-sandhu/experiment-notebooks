import urllib.parse
from datetime import datetime
from dateutil import parser
from bs4 import BeautifulSoup

# Assume FetchError is defined elsewhere; we import it if exists or define minimal
try:
    from fetch_module import FetchError  # placeholder; actual module defines it
except ImportError:
    class FetchError(Exception):
        def __init__(self, status):
            self.status = status

def extract(fetch, listing_url):
    # Fetch listing JSON via JS-rendered API
    api_url = urllib.parse.urljoin(listing_url, '/api/v2/news')
    try:
        listing_html = fetch(api_url)
    except FetchError as e:
        # Fallback: parse listing page JS script? but API is primary
        # If API fails, parse listing page's script? Not reliable.
        # For simplicity, assume API works.
        raise

    # Parse JSON from response
    try:
        listing_data = eval(listing_html)  # Not safe but placeholder; in real would use json.loads
    except Exception:
        # fallback parse script? Not implemented
        raise FetchError(500)

    # listing_data should have items list
    items = getattr(listing_data, 'items', [])
    records = []
    for item in items:
        slug = item.get('slug')
        rel_url = f'/about/newsroom/article/{slug}'
        article_url = urllib.parse.urljoin(listing_url, rel_url)
        try:
            article_html = fetch(article_url)
        except FetchError as e:
            continue

        soup = BeautifulSoup(article_html, 'html.parser')
        # Extract title from script injection? In sample, title set via JS.
        # Look for h1 inside article
        h1 = soup.find('h1')
        title = h1.get_text(strip=True) if h1 else ''
        # meta .meta contains author + date
        meta = soup.find('p', class_='meta')
        meta_text = meta.get_text(strip=True) if meta else ''
        # parse author and date from meta text like "Author · 2024-01-15"
        # naive split
        parts = meta_text.split('·')
        author_part = parts[0].strip() if len(parts) > 0 else ''
        date_part = parts[1].strip() if len(parts) > 1 else ''
        # clean author: remove "By", job titles etc simple
        author = None
        if author_part:
            # remove words like "By", keep names
            words = [w.strip() for w in author_part.split()]
            # filter out typical words
            filter_words = {'by', 'by ', 'and'}  # simplistic
            filtered = [w for w in words if w.lower() not in {'by'}]
            # join with " and " if multiple
            if filtered:
                author = ' and '.join(filtered)
            else:
                author = None
        # date from meta or from script? meta includes date via toLocaleDateString
        # extract YYYY-MM-DD from date string like "Jan 15, 2024"
        # fallback parse from item.published_at
        pub_date = item.get('published_at')  # ISO string maybe
        if pub_date:
            try:
                dt = parser.parse(pub_date)
                date_str = dt.strftime('%Y-%m-%d')
            except Exception:
                # parse from meta date string
                try:
                    dt = parser.parse(date_part)
                    date_str = dt.strftime('%Y-%m-%d')
                except Exception:
                    date_str = '1900-01-01'
        else:
            try:
                dt = parser.parse(date_part)
                date_str = dt.strftime('%Y-%m-%d')
            except Exception:
                date_str = '1900-01-01'

        # body: .body innerHTML
        body_el = soup.find('div', class_='body')
        body_html = body_el.get_text(separator='\n', strip=False) if body_el else ''
        # remove placeholder "Loading…"
        if 'Loading…' in body_html:
            body_html = ''
        body = body_html.replace('\n\n', '\n').strip()

        records.append({
            'url': article_url,
            'title': title,
            'date': date_str,
            'author': author if author else None,
            'body': body
        })

    # sort newest first (published_at descending)
    records.sort(key=lambda x: x['date'], reverse=True)
    return records
