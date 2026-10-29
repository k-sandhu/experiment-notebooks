import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser
import json
from typing import List, Dict

# FetchError is assumed to be defined elsewhere in the module's namespace
# class FetchError:
#     def __init__(self, status):
#         self.status = status

def extract(fetch, listing_url: str) -> List[Dict]:
    base_url = urllib.parse.urljoin(listing_url, '/')
    all_cards = []  # list of absolute URLs of release pages
    current_url = listing_url

    while current_url:
        try:
            html = fetch(current_url)
        except Exception:  # FetchError already defined; catch generic for safety
            break

        soup = BeautifulSoup(html, 'html.parser')

        # Find all news cards on the current listing page
        cards = soup.find_all('div', class_='news-card')
        for card in cards:
            link_tag = card.find('a', href=True)
            if link_tag and link_tag.get('href'):
                rel_href = link_tag['href']
                abs_url = urllib.parse.urljoin(base_url, rel_href)
                # Only consider links that start with /news/ and end with .html
                if abs_url.startswith('/news/') and abs_url.endswith('.html'):
                    all_cards.append(abs_url)

        # Look for pagination links (simple heuristic: <a> with href containing /news/ and not .html)
        pagination_links = soup.find_all('a', href=True)
        next_url = None
        for pl in pagination_links:
            pl_href = urllib.parse.urljoin(base_url, pl['href'])
            # Assume pagination links point to next page like /news/page/2/
            if '/page/' in pl_href or '/p/' in pl_href:
                # Ensure it's not a release link
                if not pl_href.endswith('.html'):
                    next_url = pl_href
                    break

        # If no explicit next pagination link found, stop
        if next_url:
            current_url = next_url
        else:
            current_url = None

    # Remove duplicates while preserving first occurrence order
    seen = set()
    unique_urls = []
    for url in all_cards:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)

    # Fetch each release page and extract details
    records = []
    for abs_url in unique_urls:
        try:
            release_html = fetch(abs_url)
        except Exception:
            continue

        soup = BeautifulSoup(release_html, 'html.parser')

        # Extract title from <h1> inside <article>
        title_tag = soup.find('h1')
        if title_tag:
            title = title_tag.get_text(strip=True)
        else:
            title = ''

        # Extract date from structured data JSON-LD
        date = None
        ld_script = soup.find('script', type='application/ld+json')
        if ld_script and ld_script.string:
            try:
                ld = json.loads(ld_script.string)
                if isinstance(ld, dict) and ld.get('@type') == 'NewsArticle':
                    pub_date_str = ld.get('datePublished')
                    if pub_date_str:
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
                parts = content.split('·')
                date_part = parts[0].strip()
                try:
                    dt = parser.parse(date_part)
                    date = dt.date().isoformat()
                except Exception:
                    pass

        # Extract author from JSON-LD
        author = None
        if ld_script and ld_script.string:
            try:
                ld = json.loads(ld_script.string)
                authors = ld.get('author')
                if isinstance(authors, dict) and authors.get('@type') == 'Person':
                    name = authors.get('name')
                    if name:
                        author = name
                elif isinstance(authors, list):
                    names = []
                    for a in authors:
                        if isinstance(a, dict) and a.get('@type') == 'Person':
                            name = a.get('name')
                            if name:
                                names.append(name)
                    if names:
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
            prose_div = article.find('div', class_='prose')
            if prose_div:
                body_parts = []
                for child in prose_div.find_all(['p', 'h2', 'h3', 'h4', 'h5', 'h6']):
                    text = child.get_text(separator='\n', strip=True)
                    if text:
                        body_parts.append(text)
                body = '\n\n'.join(body_parts)
            else:
                body_parts = []
                for child in article.find_all(['p', 'h2', 'h3']):
                    text = child.get_text(separator='\n', strip=True)
                    if text:
                        body_parts.append(text)
                body = '\n\n'.join(body_parts)
        else:
            body_parts = []
            for child in soup.find_all(['p', 'h2', 'h3']):
                if child.parent.name not in ('header', 'footer'):
                    text = child.get_text(separator='\n', strip=True)
                    if text:
                        body_parts.append(text)
            body = '\n\n'.join(body_parts)

        # Normalize date string to YYYY-MM-DD
        if date and not isinstance(date, str):
            if hasattr(date, 'isoformat'):
                date = date.isoformat()
            else:
                pass  # already string

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
            dt = parser.parse(d)
            return dt.isoformat()
        except Exception:
            return ''

    records.sort(key=sort_key, reverse=True)

    return records
