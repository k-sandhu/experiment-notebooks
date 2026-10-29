import urllib.parse
from datetime import datetime
from dateutil import parser
from bs4 import BeautifulSoup

# Assume FetchError is defined elsewhere; we only use fetch as provided

def extract(fetch, listing_url):
    # Fetch listing page
    listing_html = fetch(listing_url)
    soup_listing = BeautifulSoup(listing_html, 'html.parser')
    
    # Find all notice-row divs
    notice_rows = soup_listing.find_all('div', class_='notice-row')
    
    records = []
    
    for row in notice_rows:
        # Extract title link
        title_a = row.find('a', class_='notice-title')
        if not title_a:
            continue
        rel_url = title_a.get('href')
        abs_url = urllib.parse.urljoin(listing_url, rel_url)
        
        # Extract date from notice-date span (format DD.MM.YYYY)
        date_span = row.find('span', class_='notice-date')
        if not date_span:
            continue
        date_str = date_span.get_text(strip=True)
        # Parse date string like "28.09.2026" -> "2026-09-28"
        try:
            # dateutil can parse "28.09.2026"
            dt = parser.parse(date_str)
            pub_date = dt.strftime('%Y-%m-%d')
        except Exception:
            # fallback simple split
            parts = date_str.split('.')
            if len(parts) == 3:
                try:
                    pub_date = f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
                except Exception:
                    pub_date = None
        
        # Fetch release page
        release_html = fetch(abs_url)
        soup_release = BeautifulSoup(release_html, 'html.parser')
        
        # Title: full headline as plain text, exactly as release page shows it
        # Use h1 as main title (matches sample)
        h1 = soup_release.find('h1')
        if h1:
            title = h1.get_text(strip=True)
        else:
            # fallback to link text
            title = title_a.get_text(strip=True)
        
        # Author: find .sig or similar; sample has <p class="sig">Market Operations...</p>
        # We need name(s) without job titles/words like "By". Sample has "Market Operations, Ostara Commodities Exchange"
        # We'll extract text before comma if present and strip "Market Operations," etc.
        # But spec: name or names of person/people credited as author, without job titles and without words such as "By"
        # In sample, it's "Market Operations" which is not a person. Likely no author person.
        # We'll look for .sig or maybe elsewhere. For simplicity, if .sig exists, take its text and remove trailing ", Ostara Commodities Exchange"
        sig = soup_release.find('p', class_='sig')
        if sig:
            sig_text = sig.get_text(strip=True)
            # Remove trailing ", Ostara Commodities Exchange" if present
            if ', Ostara Commodities Exchange' in sig_text:
                sig_text = sig_text.split(', Ostara Commodities Exchange')[0].strip()
            # Also might contain "Market Operations," -> remove "Market Operations,"?
            # We'll just keep as is; spec says without job titles; "Market Operations" could be considered job title? Probably not a person.
            # Since no person name, return None? But sample has no person author. We'll return sig_text if it looks like a name? Safer to return None if no obvious name.
            # We'll check if sig_text contains a comma and a name pattern? Simpler: if sig_text contains "Market Operations" or similar generic, treat as no person -> None.
            # We'll implement: if sig_text contains any of generic phrases like "Market Operations", "Exchange", "Ostara Commodities Exchange", return None.
            generic_indicators = ['Market Operations', 'Ostara Commodities Exchange']
            if any(ind in sig_text for ind in generic_indicators):
                author = None
            else:
                # join multiple names with " and "? Not needed now.
                author = sig_text
        else:
            author = None
        
        # Body: full main text of release as plain text, paragraphs separated by blank lines.
        # Locate .notice-text div
        text_div = soup_release.find('div', class_='notice-text')
        if text_div:
            # Get paragraphs inside
            paragraphs = []
            for p in text_div.find_all('p'):
                # Get text of p, keep line breaks? We need paragraphs separated by blank lines.
                # Use p.get_text(strip=False) to keep internal spacing? But we want plain text without extra markup.
                # We'll get text and normalize whitespace? Keep single newline between paragraphs.
                paragraphs.append(p.get_text(strip=False).replace('\n', '').strip())
            # Join paragraphs with '\n\n'
            body = '\n\n'.join(paragraphs)
        else:
            # fallback: get all text from main? Not ideal.
            body = soup_release.get_text(separator='\n\n')
        
        # Build record
        record = {
            'url': abs_url,
            'title': title,
            'date': pub_date,
            'author': author,
            'body': body
        }
        records.append(record)
    
    # Sort newest first by publication date (YYYY-MM-DD)
    def sort_key(rec):
        d = rec['date']
        if d and len(d) == 10 and d[4] == '-' and d[7] == '-':
            try:
                return parser.parse(d)
            except Exception:
                return datetime.min
        # fallback: use original date string compare lexicographically (since format YYYY-MM-DD)
        return d or ''
    
    records.sort(key=sort_key, reverse=True)
    
    return records
