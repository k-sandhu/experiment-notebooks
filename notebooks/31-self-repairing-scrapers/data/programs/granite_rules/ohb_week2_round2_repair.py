import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser

# FetchError is assumed to be defined elsewhere; we do not import it here.

def extract(fetch, listing_url):
    listing_html = fetch(listing_url)
    soup_listing = BeautifulSoup(listing_html, 'html.parser')
    
    main_table = soup_listing.find('table', {'width': '100%', 'cellpadding': '4'})
    links = []
    if main_table:
        rows = main_table.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            for cell in cells:
                a_tags = cell.find_all('a', href=True)
                for a in a_tags:
                    href = a['href']
                    if href.startswith('news_item.asp'):
                        abs_url = urllib.parse.urljoin(listing_url, href)
                        links.append(abs_url)
    
    seen = set()
    unique_links = []
    for link in links:
        if link not in seen:
            seen.add(link)
            unique_links.append(link)
    
    records = []
    for link in unique_links:
        try:
            release_html = fetch(link)
        except Exception:
            continue
        soup_release = BeautifulSoup(release_html, 'html.parser')
        
        # Title from <b> inside main cell
        main_cell = soup_release.find('td', {'valign': 'top'})
        title = None
        if main_cell:
            b_tags = main_cell.find_all('b')
            if b_tags:
                title = b_tags[0].get_text(strip=True)
            else:
                title = main_cell.get_text(strip=True)
        if not title:
            title_tag = soup_release.find('title')
            if title_tag:
                raw = title_tag.get_text(strip=True)
                if raw.startswith('Oakhill Bakeries Group - '):
                    title = raw[len('Oakhill Bakeries Group - '):].strip()
                else:
                    title = raw
        
        # Date from "Posted: Monday, September 28, 2026"
        date_str = None
        font_cells = soup_release.find_all('font', {'size': '1'})
        for font in font_cells:
            text = font.get_text(strip=True)
            if 'Posted:' in text:
                parts = text.split('Posted:', 1)
                if len(parts) > 1:
                    date_part = parts[1].strip()
                    try:
                        dt = parser.parse(date_part)
                        date_iso = dt.strftime('%Y-%m-%d')
                        date_str = date_iso
                        break
                    except Exception:
                        pass
        
        if date_str is None:
            for font in font_cells:
                text = font.get_text(strip=True)
                import re
                match = re.search(r'(?:\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}', text)
                if match:
                    try:
                        dt = parser.parse(match.group())
                        date_str = dt.strftime('%Y-%m-%d')
                        break
                    except Exception:
                        pass
        
        # Author from "Posted by: Lucien Bréval"
        author = None
        for font in font_cells:
            text = font.get_text(strip=True)
            if 'Posted by:' in text:
                author_part = text.split('Posted by:', 1)[1].strip()
                author_part = author_part.rstrip('.')
                if author_part.lower().startswith('by '):
                    author_part = author_part[3:].strip()
                author = author_part
                break
        
        # Body: main text paragraphs inside main_cell, excluding footer and back link
        body_parts = []
        if main_cell:
            for tag in main_cell.find_all(['font', 'p'], recursive=True):
                txt = tag.get_text(separator=' ', strip=True)
                if '&laquo; Back to news' in txt:
                    continue
                if txt.strip():
                    body_parts.append(txt.strip())
        
        if body_parts:
            body = '\n\n'.join(body_parts)
        else:
            all_text = soup_release.get_text(separator='\n', strip=True)
            if '&copy;' in all_text:
                body = all_text.split('&copy;', 1)[0]
            else:
                body = all_text
        
        # Clean body: collapse multiple spaces and normalize line breaks
        lines = body.split('\n')
        cleaned = []
        for line in lines:
            line = line.strip()
            if line:
                cleaned.append(line)
        body = '\n\n'.join(cleaned)
        
        # Normalize date string
        date_record = None
        if date_str:
            try:
                dt = parser.parse(date_str)
                date_record = dt.strftime('%Y-%m-%d')
            except Exception:
                pass
        
        # Normalize author: simple join if multiple names (not needed here)
        # Ensure None for no author
        if author and author.strip() == '':
            author = None
        
        record = {
            'url': link,
            'title': title if title else '',
            'date': date_record,
            'author': author if author else None,
            'body': body if body else ''
        }
        records.append(record)
    
    # Sort by date descending, None dates go last
    def sort_key(rec):
        d = rec['date']
        if d and isinstance(d, str):
            try:
                dt = parser.parse(d)
                return dt
            except Exception:
                return None
        return None
    
    records.sort(key=sort_key, reverse=True)
    
    return records
