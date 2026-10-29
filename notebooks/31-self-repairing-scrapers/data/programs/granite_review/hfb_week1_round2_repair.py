import urllib.parse
import json
from datetime import datetime
from dateutil import parser
from bs4 import BeautifulSoup

class FetchError(Exception):
    def __init__(self, status):
        self.status = status

def extract(fetch, listing_url):
    api_url = urllib.parse.urljoin(listing_url, '/api/v2/news')
    try:
        listing_html = fetch(api_url)
    except FetchError as e:
        raise FetchError(500)

    try:
        listing_data = json.loads(listing_html)
    except json.JSONDecodeError:
        raise FetchError(500)

    items = getattr(listing_data, 'items', [])
    if not isinstance(items, list):
        raise FetchError(500)

    records = []
    for item in items:
        slug = item.get('slug')
        rel_url = f'/about/newsroom/article/{slug}'
        article_url = urllib.parse.urljoin(listing_url, rel_url)

        try:
            article_html = fetch(article_url)
        except FetchError:
            continue

        # Get article metadata via API
        article_id = item.get('id')
        api_article_url = urllib.parse.urljoin(listing_url, f'/api/v2/news/{article_id}')
        try:
            article_api_html = fetch(api_article_url)
            article_data = json.loads(article_api_html)
        except FetchError:
            # Fallback to scraping if API fails
            article_data = None

        # Extract title
        if article_data and 'title' in article_data:
            title = article_data['title']
        else:
            soup = BeautifulSoup(article_html, 'html.parser')
            h1 = soup.find('h1')
            title = h1.get_text(strip=True) if h1 else ''

        # Extract author
        if article_data and 'author' in article_data and 'display_name' in article_data['author']:
            author_display = article_data['author']['display_name']
            # Remove team/job titles if present (simple heuristic)
            # Keep only the display_name part; spec says without job titles
            # display_name seems clean (e.g., "Devran Holt")
            author = author_display
        else:
            meta = soup.find('p', class_='meta')
            meta_text = meta.get_text(strip=True) if meta else ''
            # meta_text format: "AuthorName · YYYY-MM-DD"
            parts = meta_text.split('·')
            author_part = parts[0].strip() if len(parts) > 0 else ''
            # Filter out stop words like "By", "by", etc.
            stop_words = {'by', 'by ', 'and', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'as', 'by:'}
            orig_words = author_part.split()
            filtered_orig = [w for w in orig_words if w.lower() not in stop_words]
            author = ' and '.join(filtered_orig) if filtered_orig else None

        # Extract date
        pub_ms = item.get('published_at')
        if isinstance(pub_ms, (int, float)):
            dt = datetime.fromtimestamp(pub_ms / 1000.0)
            date_str = dt.strftime('%Y-%m-%d')
        else:
            # fallback parse from meta date string
            try:
                date_part = parts[1].strip() if len(parts) > 1 else ''
                dt = parser.parse(date_part)
                date_str = dt.strftime('%Y-%m-%d')
            except Exception:
                # try parse pub_ms if string
                try:
                    dt = parser.parse(pub_ms)
                    date_str = dt.strftime('%Y-%m-%d')
                except Exception:
                    date_str = '1900-01-01'

        # Extract body
        if article_data and 'body_html' in article_data:
            body_html = article_data['body_html']
            body_soup = BeautifulSoup(body_html, 'html.parser')
            # Remove script/style tags
            for tag in body_soup(['script', 'style']):
                tag.decompose()
            body_text = body_soup.get_text(separator='\n', strip=False)
            # Clean possible "Loading…" placeholder
            if 'Loading…' in body_text:
                body_text = body_text.replace('Loading…', '')
            body = body_text.replace('\n\n', '\n').strip()
        else:
            soup = BeautifulSoup(article_html, 'html.parser')
            body_el = soup.find('div', class_='body')
            if body_el and body_el.get_text(strip=False).startswith('Loading…'):
                body = ''
            else:
                body_text = body_el.get_text(separator='\n', strip=False) if body_el else ''
                if 'Loading…' in body_text:
                    body_text = body_text.replace('Loading…', '')
                body = body_text.replace('\n\n', '\n').strip()

        # Author normalization: ensure None if empty or only stop words
        if author is not None:
            words = [w.strip() for w in author.split()]
            clean_words = [w for w in words if w.lower() not in stop_words]
            if not clean_words:
                author = None
            else:
                # Join with " and " as per spec
                author = ' and '.join(clean_words)

        records.append({
            'url': article_url,
            'title': title,
            'date': date_str,
            'author': author,
            'body': body
        })

    # Sort newest first by published_at numeric
    records.sort(key=lambda rec: rec['date'], reverse=True)
    return records
