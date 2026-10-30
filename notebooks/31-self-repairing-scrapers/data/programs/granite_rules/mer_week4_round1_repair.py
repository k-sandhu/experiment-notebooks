import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser
from typing import List, Dict, Optional

# FetchError is assumed to be defined elsewhere

def extract(fetch, listing_url: str):
    """
    Extract all press release records from the Meridian Ratings press listing.
    
    Args:
        fetch: Callable that performs HTTP GET and returns response body as str.
                Raises FetchError for HTTP errors.
        listing_url: URL of the press listing page (e.g., "/press/").
    
    Returns:
        List[Dict] with keys: url, title, date, author, body. Newest first.
    """
    # Fetch the listing page (or feed)
    try:
        listing_html = fetch(listing_url)
    except Exception as e:
        raise e

    # Check if listing page contains release links statically
    soup = BeautifulSoup(listing_html, "html.parser")
    base_url = urllib.parse.urljoin(listing_url.rstrip('/'), '/')
    
    # Look for release links directly
    release_links = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        full_href = urllib.parse.urljoin(base_url, href)
        path = urllib.parse.urlparse(full_href).path
        if path.startswith('/press/') and len(path.split('/')) >= 4:
            # simple filter: ensure path has year/month/day pattern
            parts = path.split('/')
            if len(parts) >= 4 and parts[1].isdigit() and parts[2].isdigit() and parts[3].isdigit():
                release_links.append(full_href)
    
    # If no links found, try the RSS feed
    if not release_links:
        feed_url = "/press/feed.xml"
        feed_full = urllib.parse.urljoin(base_url, feed_url)
        try:
            feed_html = fetch(feed_full)
            feed_soup = BeautifulSoup(feed_html, "xml")
            # RSS items
            for item in feed_soup.find_all('item'):
                link_el = item.find('link')
                if link_el:
                    link = link_el.get('href')
                    if link:
                        full_link = urllib.parse.urljoin(base_url, link)
                        release_links.append(full_link)
        except Exception:
            pass
    
    # Remove duplicates while preserving order
    seen = set()
    unique_links = []
    for link in release_links:
        if link not in seen:
            seen.add(link)
            unique_links.append(link)
    
    records = []
    for link in unique_links:
        try:
            release_html = fetch(link)
        except Exception:
            continue
        
        release_soup = BeautifulSoup(release_html, "html.parser")
        
        article = release_soup.find('article', class_='pr')
        if not article:
            continue
        
        title_tag = article.find('h1')
        title = title_tag.get_text(strip=True) if title_tag else ""
        
        meta_div = article.find('div', class_='pr-meta')
        date_text = ""
        if meta_div:
            date_span = meta_div.find('span')
            if date_span:
                date_text = date_span.get_text(strip=True)
        
        date_str = None
        if date_text:
            try:
                parsed = parser.parse(date_text)
                date_str = parsed.strftime('%Y-%m-%d')
            except Exception:
                pass
        
        author_text = None
        if meta_div:
            analyst_span = meta_div.find('span', class_='analyst')
            if analyst_span:
                raw = analyst_span.get_text(strip=True)
                if raw.lower().startswith('written by '):
                    raw = raw[len('Written by '):].strip()
                # Remove trailing punctuation
                raw = raw.rstrip('.').strip()
                if raw.lower().startswith('by '):
                    raw = raw[2:].strip()
                author_text = raw
        
        body_div = article.find('div', class_='pr-body')
        body_text = ""
        if body_div:
            paras = body_div.find_all('p')
            paras_text = [p.get_text(strip=False) for p in paras]
            body_text = '\n\n'.join(paras_text)
        
        if not body_text:
            # fallback: article text excluding meta and disclaimer
            for child in article.find_all(['div', 'span']):
                if child.get('class'):
                    cls = child.get('class')
                    if isinstance(cls, list):
                        if any('pr-meta' in c for c in cls) or any('disclaimer' in c for c in cls):
                            child.decompose()
                    elif 'pr-meta' in cls or 'disclaimer' in cls:
                        child.decompose()
            body_text = article.get_text(separator='\n\n', strip=False)
        
        # Normalize body: ensure paragraphs separated by blank line
        # Remove leading/trailing newlines and collapse multiple blank lines
        lines = [line.rstrip() for line in body_text.split('\n')]
        cleaned = []
        for line in lines:
            if line.strip() == '':
                cleaned.append('')
            else:
                cleaned.append(line)
        # join with '\n\n'
        body_text = '\n\n'.join(cleaned).strip('\n')
        
        rec = {
            'url': link,
            'title': title,
            'date': date_str if date_str else None,
            'author': author_text if author_text else None,
            'body': body_text
        }
        records.append(rec)
    
    # Sort newest first by date
    def sort_key(rec):
        d = rec['date']
        if d is None:
            return ''
        try:
            parsed = parser.parse(d)
            return parsed.isoformat()
        except Exception:
            return ''
    
    records.sort(key=sort_key, reverse=True)
    
    return records
