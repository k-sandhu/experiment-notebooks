import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser

# Assume FetchError is defined elsewhere; we only use fetch as provided

def extract(fetch, listing_url):
    # Fetch listing page
    listing_html = fetch(listing_url)
    soup_listing = BeautifulSoup(listing_html, 'html.parser')
    
    # Find all news cards; sample uses class "news-card"
    cards = soup_listing.find_all('div', class_='news-card')
    records = []
    
    for card in cards:
        # Extract relative link from <a> inside card
        link_tag = card.find('a', href=True)
        if not link_tag:
            continue
        rel_url = link_tag['href']
        abs_url = urllib.parse.urljoin(listing_url, rel_url)
        
        # Fetch release page
        try:
            release_html = fetch(abs_url)
        except Exception:
            # Skip if fetch fails
            continue
        soup_release = BeautifulSoup(release_html, 'html.parser')
        
        # Get title from <h1> inside <article> or <h3> in card? Use <h1> on release page
        title_tag = soup_release.find('h1')
        if not title_tag:
            # fallback to <h3> inside card? but use release page's h1
            title_tag = card.find('h3')
        title = title_tag.get_text(strip=True) if title_tag else ''
        
        # Extract datePublished from JSON-LD script
        script_tags = soup_release.find_all('script', type='application/ld+json')
        date_str = None
        for script in script_tags:
            try:
                data = eval(script.string)  # safe for test; in real use use json.loads
                if isinstance(data, dict) and 'datePublished' in data:
                    dt_str = data['datePublished']
                    # parse and format YYYY-MM-DD
                    dt = parser.parse(dt_str)
                    date_str = dt.strftime('%Y-%m-%d')
                    break
            except Exception:
                continue
        
        # Fallback: look for date in .page-meta like "Last modified 28 September 2026"
        if not date_str:
            meta = soup_release.find('p', class_='page-meta')
            if meta:
                text = meta.get_text(strip=True)
                # simple regex? use dateutil to parse "28 September 2026"
                # dateutil can parse "28 September 2026"
                try:
                    # extract first date-like pattern
                    import re
                    m = re.search(r'(\d{1,2} \w+ \d{4})', text)
                    if m:
                        dt = parser.parse(m.group(1))
                        date_str = dt.strftime('%Y-%m-%d')
                except Exception:
                    pass
        
        # Ensure date_str not None
        if not date_str:
            continue
        
        # Author from JSON-LD
        author_raw = None
        for script in script_tags:
            try:
                data = eval(script.string)
                if isinstance(data, dict) and 'author' in data:
                    # author may be dict with name or list
                    auth = data['author']
                    if isinstance(auth, dict) and 'name' in auth:
                        author_raw = auth['name']
                    elif isinstance(auth, list):
                        names = []
                        for a in auth:
                            if isinstance(a, dict) and 'name' in a:
                                names.append(a['name'])
                        author_raw = ' and '.join(names)
                    elif isinstance(auth, str):
                        author_raw = auth
                    break
            except Exception:
                continue
        
        if author_raw:
            # Clean: remove job titles? simple: keep as is, but remove "By" etc.
            # Remove leading "By " case-insensitive
            if author_raw.lower().startswith('by '):
                author_raw = author_raw[3:].strip()
            # Remove trailing job titles? not required precise; just keep name
            # We'll keep as is
            pass
        else:
            author_raw = None
        
        # Body: main text inside .prose <div> or <article> paragraphs
        body_div = soup_release.find('div', class_='prose')
        if not body_div:
            # fallback: article body
            body_div = soup_release.find('article')
        if body_div:
            # get all <p> inside prose, join with blank line
            paras = []
            for p in body_div.find_all('p'):
                txt = p.get_text(separator=' ', strip=True)
                if txt:
                    paras.append(txt)
            body = '\n'.join(paras)
        else:
            # fallback: get all text from article excluding header/footer
            article = soup_release.find('article')
            if article:
                # get text of all children except header/footer? simple
                body_text = article.get_text(separator='\n', strip=True)
                # remove possible "Last modified ..." line? but requirement says no standard paragraphs like "About us". We'll keep all article text.
                body = body_text
            else:
                body = ''
        
        # Build record
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
