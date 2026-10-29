import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser

# FetchError is assumed to be defined elsewhere; we only use it as given.
# No need to redefine.

def extract(fetch, listing_url):
    """
    Extract all news release records from the Kestria Revenue Service newsroom listing.
    
    Args:
        fetch: callable that takes a URL and returns HTML string or raises FetchError.
        listing_url: absolute URL of the newsroom listing page.
    
    Returns:
        List[dict]: each dict contains keys 'url', 'title', 'date', 'author', 'body',
                    sorted newest first.
    """
    # Fetch the listing page
    listing_html = fetch(listing_url)
    soup_listing = BeautifulSoup(listing_html, 'html.parser')
    
    # Collect all release URLs from all listing pages via BFS
    seen_listing_urls = {listing_url}
    queue = [listing_url]
    all_release_urls = []
    
    while queue:
        cur_url = queue.pop(0)
        cur_html = fetch(cur_url)
        cur_soup = BeautifulSoup(cur_html, 'html.parser')
        
        rows = cur_soup.find_all('div', class_='views-row')
        for row in rows:
            date_span = row.find('span', class_='date-display-single')
            if not date_span:
                continue
            date_text = date_span.get_text(strip=True)
            
            title_a = row.find('a', class_='field-title')
            if not title_a or not title_a.get('href'):
                continue
            rel_url = title_a['href']
            abs_url = urllib.parse.urljoin(cur_url, rel_url)
            # Only consider release URLs (they start with /newsroom/...), not pagination
            if abs_url.startswith('/newsroom'):
                all_release_urls.append(abs_url)
        
        # Pagination: collect next listing page URLs
        pager = cur_soup.find('nav', class_='pager')
        if pager:
            links = pager.find_all('a', href=True)
            for link in links:
                href = link.get('href')
                if href:
                    abs_href = urllib.parse.urljoin(cur_url, href)
                    if abs_href.startswith('/newsroom') and abs_href not in seen_listing_urls:
                        seen_listing_urls.add(abs_href)
                        queue.append(abs_href)
    
    # Remove duplicates while preserving order (first occurrence corresponds to earliest listing page)
    seen = set()
    unique_release_urls = []
    base_domain = urllib.parse.urlparse(listing_url).scheme + '://' + urllib.parse.urlparse(listing_url).netloc
    for url in all_release_urls:
        abs_release_url = urllib.parse.urljoin(base_domain, url)
        if abs_release_url not in seen:
            seen.add(abs_release_url)
            unique_release_urls.append(abs_release_url)
    
    # Fetch and extract each release
    records = []
    seen_release_urls = set()
    
    for rel_url in unique_release_urls:
        abs_release_url = urllib.parse.urljoin(base_domain, rel_url)
        if abs_release_url in seen_release_urls:
            continue
        seen_release_urls.add(abs_release_url)
        
        try:
            release_html = fetch(abs_release_url)
        except Exception:
            continue
        soup_release = BeautifulSoup(release_html, 'html.parser')
        
        # Title from <h1 class="page-title">
        h1 = soup_release.find('h1', class_='page-title')
        if h1:
            title = h1.get_text(strip=True)
        else:
            # fallback to <a class="field-title"> inside release
            title_a_release = soup_release.find('a', class_='field-title')
            if title_a_release:
                title = title_a_release.get_text(strip=True)
            else:
                # fallback to <title> without trailing " | Kestria Revenue Service"
                page_title = soup_release.find('title')
                if page_title:
                    full_title = page_title.get_text(strip=True)
                    if ' | Kestria Revenue Service' in full_title:
                        title = full_title.split(' | ')[0]
                    else:
                        title = full_title
                else:
                    title = ''
        
        # Date from field-date (e.g., "Date: 18/09/2026")
        date_div = soup_release.find('div', class_='field-date')
        if date_div:
            date_info = date_div.get_text(strip=True)
            parts = date_info.split(':')
            if len(parts) >= 2:
                date_text2 = parts[1].strip()
            else:
                date_text2 = date_info.strip()
            try:
                dt = parser.parse(date_text2)
                date_str = dt.strftime('%Y-%m-%d')
            except Exception:
                # fallback to listing date if needed
                try:
                    dt = parser.parse(date_text)
                    date_str = dt.strftime('%Y-%m-%d')
                except Exception:
                    date_str = ''
        else:
            # fallback to listing date
            try:
                dt = parser.parse(date_text)
                date_str = dt.strftime('%Y-%m-%d')
            except Exception:
                date_str = ''
        
        # Author: look for common patterns; sample has none
        author = None
        # search for meta author or author field; simple heuristic
        author_div = soup_release.find(class_=lambda x: x and 'author' in x.lower())
        if author_div:
            txt = author_div.get_text(strip=True).lower()
            if 'by' in txt:
                txt = txt.replace('by', '').strip()
            # filter out common stop words and titles
            titles = {'by', 'and', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'of', 'for', 'with', 'as', 'is', 'it', 'we', 'you', 'our', 'their'}
            words = [w for w in txt.split() if w not in titles and w not in {'and'}]
            if words:
                author = ' and '.join(words)
        
        # Body from field-body
        body_div = soup_release.find('div', class_='field-body')
        body_text = ''
        if body_div:
            ps = body_div.find_all('p')
            paragraphs = []
            for p in ps:
                text = p.get_text(separator='\n', strip=True)
                if text.strip():
                    paragraphs.append(text.strip())
            body_text = '\n\n'.join(paragraphs)
        
        record = {
            'url': abs_release_url,
            'title': title,
            'date': date_str,
            'author': author,
            'body': body_text
        }
        records.append(record)
    
    # Sort newest first by date
    records.sort(key=lambda r: r['date'], reverse=True)
    return records
