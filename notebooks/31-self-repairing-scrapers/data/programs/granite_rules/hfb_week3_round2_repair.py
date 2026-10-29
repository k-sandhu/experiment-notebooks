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
    
    # Find the API endpoint referenced in the script
    api_url = None
    for script in soup.find_all('script', string=lambda s: s and 'api/v3/newsroom/items' in s):
        # Look for pattern fetch('/api/v3/newsroom/items')
        import re
        match = re.search(r"fetch\('([^']+)'", script.string)
        if match:
            api_url = urllib.parse.urljoin(listing_url, match.group(1))
            break
    
    if api_url is None:
        # Fallback: try to construct from base
        base = urllib.parse.urlparse(listing_url)
        api_url = urllib.parse.urlunparse((base.scheme, base.netloc, '/api/v3/newsroom/items', '', '', ''))
    
    # Fetch API data
    try:
        api_resp = fetch(api_url)
    except Exception:
        # If API fetch fails, fallback to parsing script directly
        # Find the script tag that contains JSON data for news items
        script_tag = None
        for tag in soup.find_all('script', string=lambda s: s and 'api/v3/newsroom/items' in tag.string):
            if 'api/v3/newsroom/items' in tag.string:
                script_tag = tag
                break
        
        if script_tag is None:
            return []
        
        json_str = script_tag.string
        start = json_str.find('{')
        end = json_str.rfind('}') + 1
        if start == -1 or end == 0:
            return []
        json_text = json_str[start:end]
        
        try:
            data = json.loads(json_text)
            items = data.get('data', [])
        except json.JSONDecodeError:
            return []
    else:
        # Parse JSON from API response (could be HTML with script? but API returns JSON)
        # Assume API returns JSON directly
        try:
            api_data = json.loads(api_resp)
            items = api_data.get('data', [])
        except json.JSONDecodeError:
            # Maybe API returns HTML with script? fallback to script parsing as above
            script_tag = None
            for tag in soup.find_all('script', string=lambda s: s and 'api/v3/newsroom/items' in tag.string):
                if 'api/v3/newsroom/items' in tag.string:
                    script_tag = tag
                    break
            if script_tag is None:
                return []
            json_str = script_tag.string
            start = json_str.find('{')
            end = json_str.rfind('}') + 1
            if start == -1 or end == 0:
                return []
            json_text = json_str[start:end]
            try:
                data = json.loads(json_text)
                items = data.get('data', [])
            except json.JSONDecodeError:
                return []
    
    records = []
    
    for item in items:
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
            # fallback: find any h1
            for h1 in article_soup.find_all('h1'):
                if h1.string:
                    title = h1.get_text(strip=True)
                    break
            else:
                title = ""
        
        # Find date from item's published_at or meta
        date_str = None
        # Try item.published_at
        pub_at = item.get('published_at')
        if pub_at:
            try:
                dt = parser.parse(pub_at)
                date_str = dt.strftime('%Y-%m-%d')
            except Exception:
                pass
        
        # Fallback: meta element with date
        meta_elem = article_soup.find(class_='meta')
        if meta_elem and meta_elem.string:
            text = meta_elem.get_text(separator=' ', strip=True)
            # Look for pattern YYYY-MM-DD
            import re
            match = re.search(r'\d{4}-\d{2}-\d{2}', text)
            if match:
                date_str = match.group(0)
            else:
                # split by '·'
                parts = text.split('·')
                if len(parts) >= 2:
                    date_part = parts[1].strip()
                    try:
                        dt = parser.parse(date_part)
                        date_str = dt.strftime('%Y-%m-%d')
                    except Exception:
                        pass
        
        # Author from item or meta
        author = None
        # item author display
        author_display = item.get('author', {}).get('display_name')
        if author_display:
            author = author_display.strip()
        
        # meta author
        if meta_elem and meta_elem.string:
            text = meta_elem.get_text(separator=' ', strip=True)
            parts = text.split('·')
            if len(parts) >= 1:
                author_part = parts[0].strip()
                # remove possible "By" etc
                if author_part and author_part.lower() != 'by':
                    # clean trailing punctuation
                    author_part = author_part.rstrip('.').rstrip(',').rstrip(';')
                    # join multiple names with " and"? sample single name
                    if ' and ' in author_part:
                        # keep as is
                        pass
                    else:
                        # if multiple names separated by commas, join with " and"
                        names = [n.strip() for n in author_part.split(',')]
                        if len(names) > 1:
                            author_part = ' and '.join(names)
                    author = author_part
        
        if author is None and author_display is None:
            author = None
        
        # Body: from #article inner content excluding header/footer
        article_div = article_soup.find(id='article')
        if article_div:
            # collect paragraphs/text blocks
            paragraphs = []
            # get all text nodes that are direct children or within article_div but not header/footer
            # simple: get all <p>, <div> with class not containing footer etc
            for child in article_div.find_all(['p', 'div', 'h2', 'h3', 'h4', 'h5', 'h6'], recursive=True):
                # skip if child has class that indicates navigation or footer (heuristic)
                skip_classes = ['footer', 'hfb-footer', 'hfb-header', 'nav']
                skip = any(cls in child.get('class', []) for cls in skip_classes) if child.get('class') else False
                if skip:
                    continue
                text = child.get_text(separator='\n', strip=False)
                if text.strip():
                    paragraphs.append(text.strip())
            # join with blank line between paragraphs
            body = '\n\n'.join(paragraphs)
        else:
            # fallback: find class body
            body_elem = article_soup.find(class_='body')
            if body_elem:
                body_text = body_elem.get_text(separator='\n\n', strip=False)
                if 'Loading' in body_text:
                    body = ""
                else:
                    body = body_text.strip()
            else:
                body = ""
        
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
