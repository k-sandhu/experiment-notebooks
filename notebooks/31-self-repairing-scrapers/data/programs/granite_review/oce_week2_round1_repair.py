import urllib.parse
from datetime import datetime
from dateutil import parser
from bs4 import BeautifulSoup

# Assume FetchError is defined elsewhere; we only use fetch as provided

def extract(fetch, listing_url):
    listing_html = fetch(listing_url)
    soup_listing = BeautifulSoup(listing_html, 'html.parser')
    
    notice_rows = soup_listing.find_all('div', class_='notice-row')
    records = []
    
    for row in notice_rows:
        title_a = row.find('a', class_='notice-title')
        if not title_a:
            continue
        rel_url = title_a.get('href')
        abs_url = urllib.parse.urljoin(listing_url, rel_url)
        
        date_span = row.find('span', class_='notice-date')
        if not date_span:
            continue
        date_str = date_span.get_text(strip=True)  # e.g., "08.10.2026"
        
        # Parse DD.MM.YYYY -> YYYY-MM-DD
        try:
            # dateutil can parse "08.10.2026" as day.month.year? Might interpret as month.day.year.
            # Safer: split and reformat
            parts = [p.strip() for p in date_str.split('.')]
            if len(parts) == 3 and all(p.isdigit() for p in parts):
                day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
                pub_date = f"{year:04d}-{month:02d}-{day:02d}"
            else:
                # fallback parser with dayfirst=True
                dt = parser.parse(date_str, dayfirst=True)
                pub_date = dt.strftime('%Y-%m-%d')
        except Exception:
            pub_date = None
        
        release_html = fetch(abs_url)
        soup_release = BeautifulSoup(release_html, 'html.parser')
        
        # Title from h1
        h1 = soup_release.find('h1')
        if h1:
            title = h1.get_text(strip=True)
        else:
            title = title_a.get_text(strip=True)
        
        # Author: look for .sig, extract name without job titles/words like "By"
        sig = soup_release.find('p', class_='sig')
        author = None
        if sig:
            sig_text = sig.get_text(strip=True)
            # Remove trailing ", Ostara Commodities Exchange" or similar generic phrases
            generic_indicators = ['Market Operations', 'Ostara Commodities Exchange']
            if any(ind in sig_text for ind in generic_indicators):
                # No person author
                author = None
            else:
                # Clean possible trailing comma+name? Keep as is if looks like name(s)
                # Simple: strip leading/trailing punctuation and extra words?
                # We'll just use sig_text as author if it doesn't contain generic phrases
                author = sig_text
        
        # Body from .notice-text div paragraphs
        text_div = soup_release.find('div', class_='notice-text')
        if text_div:
            paragraphs = []
            for p in text_div.find_all('p'):
                # Get text preserving paragraph separation; strip only leading/trailing whitespace
                txt = p.get_text(strip=False)
                # Normalize internal whitespace? Keep as is but remove extra newlines?
                # Replace any sequence of whitespace with a single space? No, need paragraphs separated by blank line.
                # We'll keep text as is and later join with '\n\n'
                paragraphs.append(txt.strip())
            body = '\n\n'.join(paragraphs)
        else:
            # fallback: get all text from main? Not ideal but safe
            body = soup_release.get_text(separator='\n\n')
        
        record = {
            'url': abs_url,
            'title': title,
            'date': pub_date,
            'author': author,
            'body': body
        }
        records.append(record)
    
    # Sort newest first by pub_date (YYYY-MM-DD)
    def sort_key(rec):
        d = rec['date']
        if d and len(d) == 10 and d[4] == '-' and d[7] == '-':
            try:
                return parser.parse(d)
            except Exception:
                return datetime.min
        # fallback lexicographic (since format YYYY-MM-DD)
        return d or ''
    
    records.sort(key=sort_key, reverse=True)
    return records
