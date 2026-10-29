import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser

# Assume FetchError is defined elsewhere; we only use fetch
def extract(fetch, listing_url):
    # Fetch listing page
    listing_html = fetch(listing_url)
    
    # The listing page uses JS to load data from /api/v3/newsroom/items
    # We need to fetch that API endpoint directly
    api_url = urllib.parse.urljoin(listing_url, '/api/v3/newsroom/items')
    api_json = fetch(api_url)
    
    # Parse JSON (simplified; in reality fetch returns str, need json.loads)
    import json
    data = json.loads(api_json)
    items = data.get('data', [])
    
    records = []
    for item in items:
        slug = item.get('attributes', {}).get('slug')
        if not slug:
            continue
        article_url = urllib.parse.urljoin(listing_url, f'/about/newsroom/article/{slug}')
        article_html = fetch(article_url)
        
        # Fetch article JSON via API
        article_api_url = urllib.parse.urljoin(listing_url, f'/api/v3/newsroom/items/{item.get("id")}')
        article_api_json = fetch(article_api_url)
        article_data = json.loads(article_api_json)
        attrs = article_data.get('data', {}).get('attributes', {})
        
        # Extract fields
        title = attrs.get('headline', '').strip()
        # date: first published date attribute
        pub_date_str = attrs.get('published_at') or attrs.get('date')
        if pub_date_str:
            try:
                dt = parser.parse(pub_date_str)
                date = dt.strftime('%Y-%m-%d')
            except Exception:
                date = None
        else:
            date = None
        
        # author: combine names, filter out titles/by
        author_raw = attrs.get('author', [])
        if isinstance(author_raw, str):
            author_raw = [author_raw]
        # simple cleaning: split by commas/and, keep words not containing titles
        names = []
        for a in author_raw:
            a_clean = a.lower()
            if 'by' in a_clean or any(t in a_clean for t in ['mr', 'ms', 'prof', 'dr']):
                continue
            names.append(a.strip())
        if names:
            author = ' and '.join(names)
        else:
            author = None
        
        # body: use article HTML, remove header/footer/nav etc.
        soup = BeautifulSoup(article_html, 'html.parser')
        article_elem = soup.find(id='article')
        if article_elem:
            # get text of all paragraphs inside article, preserving blank lines
            paras = []
            for p in article_elem.find_all(['p', 'div'], recursive=False):
                txt = p.get_text(separator='\n', strip=True)
                if txt:
                    paras.append(txt)
            body = '\n'.join(paras)
        else:
            # fallback: get text from main
            main = soup.find('main')
            if main:
                body = main.get_text(separator='\n', strip=True)
            else:
                body = article_html.strip()
        
        records.append({
            'url': article_url,
            'title': title,
            'date': date if date else None,
            'author': author,
            'body': body
        })
    
    # Sort newest first (assuming API returns newest first; keep order)
    # If date parsing needed for sort, use datetime
    def get_sort_key(rec):
        d = rec['date']
        if d and isinstance(d, str):
            try:
                return parser.parse(d)
            except Exception:
                return None
        return None
    records.sort(key=get_sort_key, reverse=True)
    
    return records
