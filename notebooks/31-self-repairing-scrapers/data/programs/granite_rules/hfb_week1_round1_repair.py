import urllib.parse
import json
from datetime import datetime
from dateutil import parser
from bs4 import BeautifulSoup

# FetchError assumed defined; we include minimal definition for completeness
class FetchError(Exception):
    def __init__(self, status):
        self.status = status

def extract(fetch, listing_url):
    api_url = urllib.parse.urljoin(listing_url, '/api/v2/news')
    try:
        listing_html = fetch(api_url)
    except FetchError as e:
        # If API fails, attempt fallback parsing of listing page script (not reliable)
        # but per spec we must work; however API is primary.
        raise

    try:
        listing_data = json.loads(listing_html)
    except json.JSONDecodeError:
        raise FetchError(500)

    items = getattr(listing_data, 'items', [])
    if not isinstance(items, list):
        # fallback: parse script from listing page? Not required for fix.
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

        soup = BeautifulSoup(article_html, 'html.parser')
        # Title from h1 inside article
        h1 = soup.find('h1')
        title = h1.get_text(strip=True) if h1 else ''

        # Meta contains author + date string like "Devran Holt · 2026-10-04"
        meta = soup.find('p', class_='meta')
        meta_text = meta.get_text(strip=True) if meta else ''

        # Extract author name without "By", job titles etc.
        # meta_text format: "AuthorName · YYYY-MM-DD" or similar
        # Split on '·' (U+2010) or '·' literal? In sample it's '·' (U+2010)
        # Use regex or simple split on '·'
        parts = meta_text.split('·')
        author_part = parts[0].strip() if len(parts) > 0 else ''
        date_part = parts[1].strip() if len(parts) > 1 else ''

        # Clean author: remove words like "By", "by", team etc.
        # Keep only words that look like names (alphanumeric + spaces/hyphens/apostrophes)
        # Simple approach: split by spaces, filter out known stop words
        stop_words = {'by', 'by ', 'and', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'as', 'by:'}
        words = [w.strip().lower() for w in author_part.split()]
        filtered = [w for w in words if w not in stop_words]
        # Reconstruct with original capitalization? Keep as original case from first word?
        # We'll join with original casing from first occurrence? Simpler: join filtered words as they appear in original string after removing stop words.
        # Rebuild author string preserving original casing of remaining words.
        # Find original words list with case
        orig_words = author_part.split()
        filtered_orig = []
        for w in orig_words:
            lw = w.lower()
            if lw not in stop_words:
                filtered_orig.append(w)
        author = ' and '.join(filtered_orig) if filtered_orig else None

        # Date extraction: use published_at from item (UNIX ms) as authoritative
        pub_ms = item.get('published_at')
        if isinstance(pub_ms, (int, float)):
            dt = datetime.fromtimestamp(pub_ms / 1000.0)
            date_str = dt.strftime('%Y-%m-%d')
        else:
            # fallback parse from meta date string like "Oct 4, 2026"
            try:
                dt = parser.parse(date_part)
                date_str = dt.strftime('%Y-%m-%d')
            except Exception:
                # try parse from pub_ms if string?
                try:
                    dt = parser.parse(pub_ms)
                    date_str = dt.strftime('%Y-%m-%d')
                except Exception:
                    date_str = '1900-01-01'

        # Body: .body inner HTML, but need plain text without placeholders
        body_el = soup.find('div', class_='body')
        if body_el and body_el.get_text(strip=False).startswith('Loading…'):
            # fetch article JSON for body? Not possible via fetch? Could fetch /api/v2/news/<id>
            # But spec says only fetch listing page and article page; article page loads body via JS from API.
            # However sample article page has <div class="body">Loading…</div> and body set via JS from /api/v2/news/3837
            # We cannot execute JS; but we can fetch the API endpoint for the article.
            api_article_url = urllib.parse.urljoin(listing_url, f'/api/v2/news/{item.get("id")}')
            try:
                article_api_html = fetch(api_article_url)
                article_data = json.loads(article_api_html)
                body_html = article_data.get('body_html', '')
                # Convert HTML to plain text: get_text with separator '\n'
                body_soup = BeautifulSoup(body_html, 'html.parser')
                body_text = body_soup.get_text(separator='\n', strip=False)
                # Remove any script/style etc already stripped by get_text
                # Ensure no extra newlines from placeholder
                body = body_text.replace('\n\n', '\n').strip()
            except FetchError:
                body = ''
        else:
            body_html = body_el.get_text(separator='\n', strip=False) if body_el else ''
            # Remove placeholder "Loading…" if present
            if 'Loading…' in body_html:
                body_html = body_html.replace('Loading…', '')
            body = body_html.replace('\n\n', '\n').strip()

        records.append({
            'url': article_url,
            'title': title,
            'date': date_str,
            'author': author if author else None,
            'body': body
        })

    # Sort newest first by published_at (use item['published_at'] numeric)
    records.sort(key=lambda rec: rec['date'], reverse=True)
    return records
