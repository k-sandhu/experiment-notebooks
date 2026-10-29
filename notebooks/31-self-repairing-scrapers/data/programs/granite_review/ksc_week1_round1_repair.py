import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser

# FetchError is assumed to be defined elsewhere; we only reference it

def extract(fetch, listing_url):
    # Fetch the listing page
    listing_html = fetch(listing_url)
    
    # Parse listing page
    soup_listing = BeautifulSoup(listing_html, 'html.parser')
    
    # Find all teaser articles
    teasers = soup_listing.find_all('article', class_='teaser')
    
    # Collect release URLs from teasers
    release_urls = []
    for teaser in teasers:
        link_tag = teaser.find('a', href=True)
        if link_tag:
            rel_url = link_tag['href']
            abs_url = urllib.parse.urljoin(listing_url, rel_url)
            # Only keep those that match /media/news/ pattern (teaser links)
            if abs_url.startswith('https://www.ksc.example/media/news/'):
                release_urls.append(abs_url)
    
    # Fetch each release page and extract data
    records = []
    for rel_url in release_urls:
        try:
            release_html = fetch(rel_url)
        except Exception:  # FetchError may be raised; catch generic for safety
            continue
        
        soup_release = BeautifulSoup(release_html, 'html.parser')
        
        # Get title from h1 (main heading)
        h1 = soup_release.find('h1')
        title = h1.get_text(strip=True) if h1 else ""
        
        # Find meta meta inside dl.meta
        meta_dl = soup_release.find('dl', class_='meta')
        date_text = None
        author_text = None
        
        if meta_dl:
            # Iterate dt/dd pairs
            dt_children = meta_dl.find_all(['dt', 'dd'])
            i = 0
            while i < len(dt_children):
                dt = dt_children[i]
                if dt.name == 'dt' and dt.get_text(strip=True).strip().lower() == 'published':
                    dd = meta_dl.find_next('dd')
                    if dd and dd.name == 'dd':
                        date_text = dd.get_text(strip=True)
                if dt.name == 'dt' and dt.get_text(strip().lower()) == 'author':
                    dd = meta_dl.find_next('dd')
                    if dd and dd.name == 'dd':
                        author_text = dd.get_text(strip=True)
                i += 1
        
        # Parse date: e.g., "30 September 2026"
        date_parsed = None
        if date_text:
            try:
                date_parsed = parser.parse(date_text, fuzzy=True).date()
            except Exception:
                pass
        
        # Author cleaning
        author = None
        if author_text:
            # Remove possible "By " prefix
            text = author_text.strip()
            if text.lower().startswith('by '):
                text = text[3:].strip()
            # Split by commas or "and" (case insensitive) and clean
            parts = [p.strip() for p in text.split(',') if p.strip()]
            # Also handle "and" separated parts if commas not used
            # Simple: if "and" appears in text, split by " and " as well
            if ' and ' in text:
                parts = [p.strip() for p in text.split(' and ') if p.strip()]
            if parts:
                # Join with " and "
                author = " and ".join(parts)
            else:
                author = text
        
        # Body: find .body div? In sample, <div class="body"> contains paragraphs
        body_div = soup_release.find('div', class_='body')
        body_text = ""
        if body_div:
            # get all paragraphs inside body_div
            paras = body_div.find_all('p')
            paras_text = [p.get_text(strip=False) for p in paras]
            # join with blank line between paragraphs
            body_text = '\n\n'.join(paras_text)
        else:
            # fallback: get all p not in contact
            paras = soup_release.find_all('p')
            paras_text = []
            for p in paras:
                txt = p.get_text(strip=False)
                if 'contact' in p.get('class', []) or 'contact' in txt.lower():
                    continue
                paras_text.append(txt)
            body_text = '\n\n'.join(paras_text)
        
        # Build record
        date_str = None
        if date_parsed:
            date_str = date_parsed.strftime('%Y-%m-%d')
        
        record = {
            'url': rel_url,
            'title': title,
            'date': date_str,
            'author': author,
            'body': body_text
        }
        records.append(record)
    
    # Sort newest first by date descending
    # Filter out records with None date for sorting; they go last
    def sort_key(r):
        d = r['date']
        if d is None:
            return ''  # will sort to end
        return d
    
    records.sort(key=sort_key, reverse=True)
    
    return records
