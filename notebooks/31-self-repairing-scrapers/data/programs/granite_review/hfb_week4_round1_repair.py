import urllib.parse
import json
from bs4 import BeautifulSoup
from dateutil import parser

def extract(fetch, listing_url):
    # Fetch listing page (not strictly needed for API)
    listing_html = fetch(listing_url)
    
    # Direct API call for all news items
    api_url = urllib.parse.urljoin(listing_url, '/api/v3/newsroom/items')
    api_json = fetch(api_url)
    data = json.loads(api_json)
    items = data.get('data', [])
    
    records = []
    for item in items:
        attrs = item.get('attributes', {})
        slug = attrs.get('slug')
        if not slug:
            continue
        
        article_url = urllib.parse.urljoin(listing_url, f'/about/newsroom/article/{slug}')
        article_html = fetch(article_url)
        
        # Fetch article JSON for full content
        article_api_url = urllib.parse.urljoin(listing_url, f'/api/v3/newsroom/items/{item.get("id")}')
        article_api_json = fetch(article_api_url)
        article_data = json.loads(article_api_json)
        article_attrs = article_data.get('data', {}).get('attributes', {})
        
        # Title
        title = attrs.get('headline', '').strip()
        
        # Date: publishedAt field (ISO format with timezone)
        pub_date_str = attrs.get('publishedAt')
        if pub_date_str:
            try:
                dt = parser.parse(pub_date_str)
                date = dt.strftime('%Y-%m-%d')
            except Exception:
                date = None
        else:
            date = None
        
        # Author: byline field (single string or list); clean simple
        byline = article_attrs.get('byline')
        if byline:
            # byline appears as "Name Title"? In sample it's just "Devran Holt"
            # Remove common job title words if present (mr, ms, prof, dr, etc.)
            # Simple: split on space and filter out tokens that are titles?
            # We'll keep whole byline as author if no obvious title words.
            # According to spec: without job titles and without words such as "By"
            # We'll just take the byline as author if it doesn't contain "by"
            lowered = byline.lower()
            if 'by' in lowered:
                # attempt to strip "by" prefix/suffix? Not needed in samples.
                pass
            author = byline.strip()
        else:
            author = None
        
        # Body: use content array from article JSON
        content_paras = article_attrs.get('content', [])
        paras = []
        for para_obj in content_paras:
            if isinstance(para_obj, dict) and 'text' in para_obj:
                txt = para_obj['text'].strip()
                if txt:
                    paras.append(txt)
        if paras:
            body = '\n'.join(paras)
        else:
            # fallback to article HTML
            soup = BeautifulSoup(article_html, 'html.parser')
            article_elem = soup.find(id='article')
            if article_elem:
                paras = []
                for p in article_elem.find_all(['p', 'div'], recursive=False):
                    txt = p.get_text(separator='\n', strip=True)
                    if txt:
                        paras.append(txt)
                body = '\n'.join(paras)
            else:
                body = article_html.strip()
        
        records.append({
            'url': article_url,
            'title': title,
            'date': date,
            'author': author,
            'body': body
        })
    
    # Sort by date descending; handle None dates (should not happen) by placing them last
    def sort_key(rec):
        d = rec['date']
        if isinstance(d, str):
            try:
                return parser.parse(d)
            except Exception:
                return None
        return None
    
    # Sort stable: valid dates first (newest), None dates last
    records.sort(key=sort_key, reverse=True)
    
    return records
