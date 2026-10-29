import urllib.parse
import json
import re
from bs4 import BeautifulSoup
from dateutil import parser

# FetchError is assumed to be defined elsewhere

def extract(fetch, listing_url):
    listing_html = fetch(listing_url)
    soup_listing = BeautifulSoup(listing_html, 'html.parser')
    
    cards = soup_listing.find_all('div', class_='news-card')
    records = []
    
    for card in cards:
        link_tag = card.find('a', href=True)
        if not link_tag:
            continue
        rel_url = link_tag['href']
        abs_url = urllib.parse.urljoin(listing_url, rel_url)
        
        try:
            release_html = fetch(abs_url)
        except Exception:
            continue
        soup_release = BeautifulSoup(release_html, 'html.parser')
        
        # Title from <h1> inside <article> or fallback <h3> in card
        title_tag = soup_release.find('h1')
        if not title_tag:
            title_tag = card.find('h3')
        title = title_tag.get_text(strip=True) if title_tag else ''
        
        # Date from JSON-LD or .page-meta
        date_str = None
        script_tags = soup_release.find_all('script', type='application/ld+json')
        for script in script_tags:
            if script.string:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and 'datePublished' in data:
                        dt_str = data['datePublished']
                        dt = parser.parse(dt_str)
                        date_str = dt.strftime('%Y-%m-%d')
                        break
                except Exception:
                    continue
        
        if not date_str:
            meta = soup_release.find('p', class_='page-meta')
            if meta:
                text = meta.get_text(strip=True)
                # Look for patterns like "28 September 2026"
                m = re.search(r'(\d{1,2} \w+ \d{4})', text)
                if m:
                    try:
                        dt = parser.parse(m.group(1))
                        date_str = dt.strftime('%Y-%m-%d')
                    except Exception:
                        pass
        
        if not date_str:
            continue
        
        # Author from JSON-LD
        author_raw = None
        for script in script_tags:
            if script.string:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and 'author' in data:
                        auth = data['author']
                        if isinstance(auth, dict) and 'name' in auth:
                            author_raw = auth['name']
                        elif isinstance(auth, list):
                            names = []
                            for a in auth:
                                if isinstance(a, dict) and 'name' in a:
                                    names.append(a['name'])
                            if names:
                                author_raw = ' and '.join(names)
                        elif isinstance(auth, str):
                            author_raw = auth
                        break
                except Exception:
                    continue
        
        if author_raw:
            # Remove leading "By " (case-insensitive)
            lowered = author_raw.lower()
            if lowered.startswith('by '):
                author_raw = author_raw[3:].strip()
            # Keep as is (no removal of job titles per spec)
        else:
            author_raw = None
        
        # Body: collect paragraphs and headings from <article> or <div class='prose'>
        article = soup_release.find('article')
        if not article:
            # fallback to prose div
            article = soup_release.find('div', class_='prose')
        
        if article:
            # Get all block-level elements that should be paragraphs/headings
            # We'll extract text for <p>, <h2>, <h3>, <h4> etc inside article
            paras = []
            for elem in article.find_all(['p', 'h2', 'h3', 'h4', 'h5', 'h6']):
                # Get text without extra whitespace
                txt = elem.get_text(separator=' ', strip=True)
                if txt:
                    # For headings, keep as is; for paragraphs keep as is
                    paras.append(txt)
            # Join with blank line (\n\n) to separate paragraphs/headings
            body = '\n\n'.join(paras)
        else:
            body = ''
        
        record = {
            'url': abs_url,
            'title': title,
            'date': date_str,
            'author': author_raw if author_raw else None,
            'body': body,
        }
        records.append(record)
    
    # Sort newest first by date descending
    records.sort(key=lambda r: r['date'], reverse=True)
    return records
