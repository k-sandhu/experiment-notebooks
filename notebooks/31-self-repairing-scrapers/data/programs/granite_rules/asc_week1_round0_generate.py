import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser
from typing import List, Dict, Optional

# FetchError is assumed to be defined elsewhere in the module's namespace
# class FetchError:
#     def __init__(self, status):
#         self.status = status

def extract(fetch, listing_url: str) -> List[Dict]:
    """
    Extract all news release records from the listing page and its pagination.
    Returns a list of dicts, newest first, each containing:
        url, title, date, author, body.
    """
    base_url = urllib.parse.urljoin(listing_url, '/')
    all_cards = []
    current_url = listing_url

    while current_url:
        html = fetch(current_url)
        soup = BeautifulSoup(html, 'html.parser')

        # Find all news cards on the current listing page
        cards = soup.find_all('div', class_='news-card')
        for card in cards:
            link_tag = card.find('a', href=True)
            if link_tag and link_tag.get('href'):
                rel_url = urllib.parse.urljoin(base_url, link_tag['href'])
                # Only consider links that start with /news/ and end with .html
                if rel_url.startswith('/news/') and rel_url.endswith('.html'):
                    all_cards.append(rel_url)

        # Look for pagination links (simple heuristic: <a> with href containing /news/ and not .html)
        # In this sample there is no pagination, but we handle if exists
        pagination_links = soup.find_all('a', href=True)
        next_url = None
        for pl in pagination_links:
            pl_href = urllib.parse.urljoin(base_url, pl['href'])
            if pl_href.startswith('/news/') and '.html' not in pl_href and pl_href != base_url:
                # Assume pagination links point to next page like /news/page/2/
                # We'll collect all such links and later deduplicate; for simplicity,
                # we just collect all news links and ignore pagination for now.
                pass
            # Simple approach: if href contains '/page/' or '/p/', treat as pagination
            if '/page/' in pl_href or '/p/' in pl_href:
                next_url = pl_href
                break

        # If no explicit next pagination link found, stop
        if next_url:
            current_url = next_url
        else:
            current_url = None

    # Remove duplicates while preserving order (first encountered = newest? we sort later)
    seen = set()
    unique_urls = []
    for url in all_cards:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)

    # Fetch each release page and extract details
    records = []
    for rel_url in unique_urls:
        abs_url = urllib.parse.urljoin(base_url, rel_url)
        try:
            release_html = fetch(abs_url)
        except Exception:  # FetchError already defined; catch generic for safety
            continue

        soup = BeautifulSoup(release_html, 'html.parser')

        # Extract title from <h1> inside <article> or <h1> in body
        title_tag = soup.find('h1')
        if title_tag:
            title = title_tag.get_text(strip=True)
        else:
            # fallback to <h3> in card? but on page use <h1>
            title = ''

        # Extract date from structured data JSON-LD or meta
        date = None
        # Look for script type application/ld+json
        ld_script = soup.find('script', type='application/ld+json')
        if ld_script and ld_script.string:
            try:
                import json
                ld = json.loads(ld_script.string)
                if isinstance(ld, dict) and '@type' in ld and ld.get('@type') == 'NewsArticle':
                    pub_date_str = ld.get('datePublished')
                    if pub_date_str:
                        # parse and normalize to date (YYYY-MM-DD)
                        dt = parser.parse(pub_date_str)
                        date = dt.date().isoformat()
            except Exception:
                pass

        # If no JSON-LD, look for meta like "Last modified" pattern
        if not date:
            meta_last = soup.find('meta', {'name': 'Last modified'})
            if meta_last and meta_last.get('content'):
                content = meta_last['content']
                # pattern like "28 September 2026"
                try:
                    # simple extraction: find digits and month
                    # use dateutil parser with flexible format
                    # fallback: extract first YYYY-MM-DD like pattern
                    # We'll attempt to parse known pattern
                    # For simplicity, use regex? but only dateutil allowed
                    # We'll try parser.parse with known format
                    # content example: "28 September 2026 · 2 minute read"
                    # extract date part before "·"
                    parts = content.split('·')
                    date_part = parts[0].strip()
                    # parse "28 September 2026"
                    dt = parser.parse(date_part)
                    date = dt.date().isoformat()
                except Exception:
                    pass

        # Extract author from JSON-LD or author meta
        author = None
        if ld_script and ld_script.string:
            try:
                ld = json.loads(ld_script.string)
                authors = ld.get('author')
                if isinstance(authors, dict) and '@type' in authors and authors.get('@type') == 'Person':
                    name = authors.get('name')
                    if name:
                        author = name
                elif isinstance(authors, list):
                    names = []
                    for a in authors:
                        if isinstance(a, dict) and '@type' in a and a.get('@type') == 'Person':
                            name = a.get('name')
                            if name:
                                names.append(name)
                    if names:
                        # join with " and "
                        author = " and ".join(names)
            except Exception:
                pass

        # Fallback: look for <meta name="author">
        if not author:
            meta_author = soup.find('meta', {'name': 'author'})
            if meta_author and meta_author.get('content'):
                author = meta_author['content'].strip()

        # Extract body: main article prose
        article = soup.find('article')
        if article:
            # get .prose div or direct children paragraphs
            prose_div = article.find('div', class_='prose')
            if prose_div:
                body_parts = []
                for child in prose_div.find_all(['p', 'h2', 'h3', 'h4', 'h5', 'h6']):
                    text = child.get_text(separator='\n', strip=True)
                    if text:
                        body_parts.append(text)
                # join with blank line between paragraphs
                body = '\n\n'.join(body_parts)
            else:
                # fallback: all text inside article excluding header/footer
                for child in article.find_all(['p', 'h2', 'h3']):
                    text = child.get_text(separator='\n', strip=True)
                    if text:
                        body_parts.append(text)
                body = '\n\n'.join(body_parts)
        else:
            # fallback: all text from body excluding header/footer
            body_parts = []
            for child in soup.find_all(['p', 'h2', 'h3']):
                if child.parent.name not in ('header', 'footer'):
                    text = child.get_text(separator='\n', strip=True)
                    if text:
                        body_parts.append(text)
            body = '\n\n'.join(body_parts)

        # Clean body: remove empty lines? keep blank lines between paragraphs
        # Already joined with \n\n

        # Normalize date string to YYYY-MM-DD
        if date and not isinstance(date, str):
            # date might be datetime.date
            if hasattr(date, 'isoformat'):
                date = date.isoformat()
            else:
                # assume string already
                pass

        # Ensure url is absolute
        abs_url = urllib.parse.urljoin(base_url, rel_url)

        records.append({
            'url': abs_url,
            'title': title if title else '',
            'date': date if date else None,
            'author': author if author else None,
            'body': body if body else '',
        })

    # Sort newest first by date; None dates go last
    def sort_key(rec):
        d = rec['date']
        if d is None:
            return ''  # will be placed after dates
        try:
            # ensure string format YYYY-MM-DD
            dt = parser.parse(d)
            return dt.isoformat()
        except Exception:
            return ''

    records.sort(key=sort_key, reverse=True)

    return records
