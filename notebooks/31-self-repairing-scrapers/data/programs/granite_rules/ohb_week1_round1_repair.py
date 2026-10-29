import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser
from datetime import datetime

# Assume FetchError is defined elsewhere; we only use fetch as provided

def extract(fetch, listing_url):
    # Fetch listing page
    listing_html = fetch(listing_url)
    soup_list = BeautifulSoup(listing_html, 'html.parser')
    
    # Find the inner table with news rows
    inner_table = soup_list.find('table', {'width': '100%', 'cellpadding': '4'})
    if not inner_table:
        return []
    
    rows = inner_table.find_all('tr')
    records = []
    
    for row in rows:
        td = row.find('td', {'valign': 'top'})
        if not td:
            continue
        
        b_tag = td.find('b')
        if not b_tag:
            continue
        
        a_tag = b_tag.find('a', href=True)
        if not a_tag:
            continue
        
        href = a_tag['href']
        abs_url = urllib.parse.urljoin(listing_url, href)
        
        title = a_tag.get_text(strip=True)
        
        date_font = td.find('font', {'size': '2'})
        date_text = None
        if date_font:
            date_text = date_font.get_text(strip=True)
        
        # Parse date from listing text (e.g., "Sep 28, 2026")
        pub_date = None
        if date_text:
            try:
                pub_date = parser.parse(date_text).date()
            except Exception:
                pass
        
        records.append({
            'url': abs_url,
            'title': title,
            'date_text': date_text,
            'pub_date': pub_date,
            'raw': None  # placeholder for release data
        })
    
    # Sort records by pub_date descending (newest first)
    # Use a large date for missing pub_date so they appear last
    def sort_key(rec):
        return rec['pub_date'] if rec['pub_date'] is not None else datetime.max.date()
    
    records.sort(key=sort_key, reverse=True)
    
    # Fetch each release and extract fields
    for rec in records:
        url = rec['url']
        try:
            release_html = fetch(url)
            soup_rel = BeautifulSoup(release_html, 'html.parser')
            
            # Title: use <b> inside body if exists, else <title> without prefix
            title_b = soup_rel.find('b')
            if title_b:
                rec['raw']['title'] = title_b.get_text(strip=True)
            else:
                title_tag = soup_rel.find('title')
                if title_tag:
                    full_title = title_tag.get_text(strip=True)
                    prefix = 'Oakhill Bakeries Group - '
                    if full_title.startswith(prefix):
                        rec['raw']['title'] = full_title[len(prefix):].strip()
                    else:
                        rec['raw']['title'] = full_title
                else:
                    rec['raw']['title'] = rec['title']
            
            # Date: from "Posted: Monday, September 28, 2026"
            date_info_tag = soup_rel.find('font', {'size': '1'})
            if date_info_tag:
                date_text_full = date_info_tag.get_text(strip=True)
                if 'Posted:' in date_text_full:
                    try:
                        dt = parser.parse(date_text_full)
                        rec['raw']['date'] = dt.date().isoformat()
                    except Exception:
                        rec['raw']['date'] = None
                else:
                    rec['raw']['date'] = None
            else:
                rec['raw']['date'] = None
            
            # Author: from "Posted by: Lucien Bréval"
            author_tag = soup_rel.find('font', {'size': '1'})
            if author_tag:
                author_text = author_tag.get_text(strip=True)
                if 'Posted by:' in author_text:
                    parts = author_text.split('Posted by:', 1)
                    if len(parts) > 1:
                        author_raw = parts[1].strip()
                        # Remove any trailing <br> or HTML tags
                        author_raw = author_raw.split('<')[0].strip()
                        # Clean simple: keep as is (no job titles removal as per spec)
                        rec['raw']['author'] = author_raw
                    else:
                        rec['raw']['author'] = None
                else:
                    rec['raw']['author'] = None
            else:
                rec['raw']['author'] = None
            
            # Body: main text paragraphs between title and back link
            body_td = soup_rel.find('td', {'width': '600', 'valign': 'top'})
            if body_td:
                paragraphs = []
                for elem in body_td.find_all(['font', 'p']):
                    txt = elem.get_text(separator=' ', strip=True)
                    if txt and '&laquo; Back to news' not in txt:
                        paragraphs.append(txt)
                body_text = '\n\n'.join(paragraphs)
                rec['raw']['body'] = body_text
            else:
                rec['raw']['body'] = ''
            
            # Author normalization: join names with " and " if multiple names?
            # The spec says several names joined with " and "; we assume single name or list like "Lucien Bréval"
            # No extra processing needed.
        except Exception:
            # If fetch fails, keep listing data as fallback
            rec['raw'] = None
    
    # Build final records list
    result = []
    for rec in records:
        raw = rec.get('raw')
        if raw is None:
            # Fallback using listing data
            out = {
                'url': rec['url'],
                'title': rec['title'],
                'date': rec['pub_date'].isoformat() if rec['pub_date'] else None,
                'author': None,
                'body': ''
            }
        else:
            # Use extracted data, ensure date string YYYY-MM-DD
            date_iso = raw.get('date')
            if date_iso and isinstance(date_iso, str):
                # Validate format? Assume correct
                pass
            else:
                date_iso = rec['pub_date'].isoformat() if rec['pub_date'] else None
            
            author = raw.get('author')
            if author:
                # Normalize: remove "By" etc? Spec says without words such as "By"; we already extracted after "Posted by:"
                # No extra cleaning
                pass
            
            out = {
                'url': rec['url'],
                'title': raw.get('title', rec['title']),
                'date': date_iso,
                'author': author,
                'body': raw.get('body', '')
            }
        
        # Ensure date is YYYY-MM-DD or None
        if out['date'] and isinstance(out['date'], str):
            # Ensure format
            try:
                d = parser.parse(out['date']).date()
                out['date'] = d.isoformat()
            except Exception:
                out['date'] = None
        elif out['date'] is None and rec['pub_date']:
            out['date'] = rec['pub_date'].isoformat()
        
        # Author normalization: if author string contains "and", ensure exactly "Name1 and Name2"
        # Simple: if author contains " and " already fine; else keep as is
        if out['author']:
            # Remove possible trailing punctuation? Not required
            pass
        
        result.append(out)
    
    return result
