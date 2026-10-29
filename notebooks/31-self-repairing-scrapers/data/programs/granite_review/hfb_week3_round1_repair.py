import urllib.parse
from datetime import datetime
from dateutil import parser
from bs4 import BeautifulSoup
import json

# FetchError is assumed to be defined elsewhere; we import it here
# from your_module import FetchError  # Not needed for implementation

def extract(fetch, listing_url):
    """
    Extract all news releases from the listing page and return records.
    
    Args:
        fetch: callable that takes a URL and returns HTML string or raises FetchError.
        listing_url: absolute URL of the listing page.
    
    Returns:
        List[dict] with keys: url, title, date, author, body. Newest first.
    """
    # Fetch listing page
    try:
        listing_html = fetch(listing_url)
    except Exception as e:
        # Re-raise as FetchError if needed; assume fetch already raises FetchError
        raise

    # Parse listing with BeautifulSoup
    soup = BeautifulSoup(listing_html, 'html.parser')
    
    # Find the script tag that contains JSON data for news items
    script_tag = None
    for tag in soup.find_all('script', string=lambda s: s and 'api/v3/newsroom/items' in s):
        if 'api/v3/newsroom/items' in tag.string:
            script_tag = tag
            break
    
    if script_tag is None:
        # Fallback: look for <ul id="newsroom"> and parse manually (not used in sample)
        # but sample uses JS injection, so rely on script
        return []
    
    # Extract JSON string from script
    json_str = script_tag.string
    # Find the {...} block that contains the data
    start = json_str.find('{')
    end = json_str.rfind('}') + 1
    if start == -1 or end == 0:
        return []
    json_text = json_str[start:end]
    
    # Parse JSON
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError:
        # Attempt to extract the inner object after "document.getElementById('newsroom').innerHTML = "
        # but simpler: look for "d.data" pattern
        # fallback: return empty
        return []
    
    # data should have items list
    items = data.get('data', [])  # based on script: d.data.map(...)
    records = []
    
    for item in items:
        # Build absolute URL for article
        slug = item.get('slug', '')
        rel_url = f"/about/newsroom/article/{slug}"
        abs_url = urllib.parse.urljoin(listing_url, rel_url)
        
        # Fetch article page
        try:
            article_html = fetch(abs_url)
        except Exception:
            continue  # skip if fetch fails
        
        article_soup = BeautifulSoup(article_html, 'html.parser')
        
        # Find title: look for <h1> inside article or #article
        title_elem = article_soup.find('h1')
        if title_elem and title_elem.string:
            title = title_elem.get_text(strip=True)
        else:
            # fallback: find link with href containing slug in listing? not needed
            # search for any h1
            for h1 in article_soup.find_all('h1'):
                if h1.string:
                    title = h1.get_text(strip=True)
                    break
            else:
                title = ""
        
        # Find date: look for meta or .meta class
        date_str = None
        meta_elem = article_soup.find(class_='meta')
        if meta_elem and meta_elem.string:
            text = meta_elem.get_text(separator=' ', strip=True)
            # split by '·' or '•' or space? sample uses "·"
            parts = text.split('·')
            if len(parts) >= 2:
                date_part = parts[1].strip()
                try:
                    dt = parser.parse(date_part)
                    date_str = dt.strftime('%Y-%m-%d')
                except Exception:
                    pass
            else:
                # maybe just date in text
                # try to find pattern YYYY-MM-DD
                import re
                match = re.search(r'\d{4}-\d{2}-\d{2}', text)
                if match:
                    date_str = match.group(0)
        
        # fallback from item
        if date_str is None:
            pub_at = item.get('published_at')
            if pub_at:
                try:
                    dt = parser.parse(pub_at)
                    date_str = dt.strftime('%Y-%m-%d')
                except Exception:
                    pass
        
        # Author: from meta or item
        author = None
        if meta_elem and meta_elem.string:
            text = meta_elem.get_text(separator=' ', strip=True)
            parts = text.split('·')
            if len(parts) >= 1:
                author_part = parts[0].strip()
                # remove possible "By" etc
                if author_part and author_part != 'By':
                    # clean trailing punctuation
                    author_part = author_part.rstrip('.').rstrip(',')
                    # join multiple names with " and"? sample single name
                    author = author_part
        if author is None:
            author_display = item.get('author', {}).get('display_name')
            if author_display:
                # clean
                author = author_display.strip()
        
        # Body: from .body div or #article inner content excluding header/footer
        body_elem = article_soup.find(class_='body')
        if not body_elem:
            # fallback: find #article and get its children excluding header/footer
            article_div = article_soup.find(id='article')
            if article_div:
                # get all text with blank lines between paragraphs
                paragraphs = []
                for child in article_div.find_all(['p', 'div', 'h2', 'h3'], recursive=False):
                    if child.get_text(strip=False).strip():
                        paragraphs.append(child.get_text(separator='\n', strip=False))
                body = '\n\n'.join(p.strip() for p in paragraphs if p.strip())
            else:
                body = ""
        else:
            # get text with blank lines between paragraphs
            body_text = body_elem.get_text(separator='\n\n', strip=False)
            # remove possible "Loading…" placeholder
            if 'Loading' in body_text:
                body = ""
            else:
                body = body_text.strip()
        
        # Build record
        record = {
            'url': abs_url,
            'title': title if title else '',
            'date': date_str if date_str else '',
            'author': author if author else None,
            'body': body
        }
        records.append(record)
    
    # Sort newest first: date descending
    def get_date(rec):
        d = rec['date']
        if not d:
            return datetime.min
        try:
            return parser.parse(d)
        except Exception:
            return datetime.min
    
    records.sort(key=get_date, reverse=True)
    return records
