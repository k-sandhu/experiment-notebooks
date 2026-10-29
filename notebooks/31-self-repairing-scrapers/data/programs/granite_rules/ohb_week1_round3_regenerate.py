import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser

# Assume FetchError is defined elsewhere; we just use it
# No import of FetchError here

def extract(fetch, listing_url):
    # Fetch listing page
    listing_html = fetch(listing_url)
    soup_listing = BeautifulSoup(listing_html, 'html.parser')
    
    # Find all news item links in listing
    links = []
    # The listing contains <a> tags inside <td> with href like "news_item.asp?id=7790"
    # Search within the main table cell
    main_table = soup_listing.find('table', {'width': '100%', 'cellpadding': '4'})
    if main_table:
        rows = main_table.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            for cell in cells:
                # Look for <a> tags inside cell
                a_tags = cell.find_all('a', href=True)
                for a in a_tags:
                    href = a['href']
                    if href.startswith('news_item.asp'):
                        # Resolve absolute URL
                        abs_url = urllib.parse.urljoin(listing_url, href)
                        links.append(abs_url)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_links = []
    for link in links:
        if link not in seen:
            seen.add(link)
            unique_links.append(link)
    
    # Fetch each release page and extract info
    records = []
    for link in unique_links:
        try:
            release_html = fetch(link)
        except Exception as e:
            # Skip if fetch fails
            continue
        soup_release = BeautifulSoup(release_html, 'html.parser')
        
        # Extract title: find <title> or <b> inside main cell
        title_tag = soup_release.find('title')
        if title_tag:
            title = title_tag.get_text(strip=True)
            # Remove "Oakhill Bakeries Group - " prefix if present
            if title.startswith('Oakhill Bakeries Group - '):
                title = title[len('Oakhill Bakeries Group - '):].strip()
        else:
            # fallback: find <b> inside main cell
            main_cell = soup_release.find('td', {'valign': 'top'})
            if main_cell:
                b_tags = main_cell.find_all('b')
                if b_tags:
                    title = b_tags[0].get_text(strip=True)
                else:
                    title = main_cell.get_text(strip=True)
            else:
                title = soup_release.get_text(strip=True)
        
        # Extract date: look for "Posted:" line
        date_raw = None
        # Find <font> with size="1" containing "Posted:"
        font_cells = soup_release.find_all('font', {'size': '1'})
        for font in font_cells:
            text = font.get_text(strip=True)
            if 'Posted:' in text:
                # Example: "Posted: Monday, September 28, 2026"
                # Extract date part after "Posted:"
                parts = text.split('Posted:')
                if len(parts) > 1:
                    date_str = parts[1].strip()
                    # Clean up
                    date_str = date_str.replace(',', '').replace('Monday', '').strip()
                    # Keep only numbers and month name? Use dateutil to parse
                    # dateutil can parse "September 28, 2026"
                    try:
                        dt = parser.parse(date_str)
                        date_iso = dt.strftime('%Y-%m-%d')
                        date_raw = date_iso
                    except:
                        pass
        
        if date_raw is None:
            # fallback: find any date pattern in <font size="1">
            # simple regex not allowed; try find all <font size="1"> and parse
            pass
        
        # Extract author: "Posted by: Lucien Bréval"
        author_raw = None
        font_cells = soup_release.find_all('font', {'size': '1'})
        for font in font_cells:
            text = font.get_text(strip=True)
            if 'Posted by:' in text:
                # Remove "Posted by:" prefix
                if 'Posted by:' in text:
                    author_part = text.split('Posted by:')[1].strip()
                    # Remove trailing period or other punctuation
                    author_part = author_part.rstrip('.')
                    author_raw = author_part
        
        # Clean author: remove job titles? simple: split by '.' and take first? Not needed.
        # Remove "By" etc. We'll just strip "By " if present
        if author_raw:
            # Remove leading "By " if exists
            if author_raw.lower().startswith('by '):
                author_raw = author_raw[3:].strip()
            # Remove trailing punctuation
            author_raw = author_raw.rstrip('.')
        
        # Extract body: main text paragraphs inside main cell, excluding navigation and footer
        main_cell = soup_release.find('td', {'valign': 'top'})
        if main_cell:
            # Get all text nodes inside main_cell, but exclude navigation links and footer
            # Remove navigation links (Home, About us etc.) and footer
            # Simple approach: get all <font> and <p> inside main_cell, concatenate paragraphs separated by blank line
            paragraphs = []
            # Find all <font> and <p> tags inside main_cell
            for tag in main_cell.find_all(['font', 'p'], recursive=True):
                # Get text
                txt = tag.get_text(separator=' ', strip=True)
                # If tag is <p> with align center maybe skip if contains "&laquo; Back to news"
                if '&laquo; Back to news' in txt:
                    continue
                # Avoid empty
                if txt.strip():
                    paragraphs.append(txt.strip())
            # Join paragraphs with double newline
            body_lines = []
            for p in paragraphs:
                # Some paragraphs may contain <br> tags; we already extracted text
                # Just add as line
                body_lines.append(p)
            body = '\n\n'.join(body_lines)
        else:
            # fallback: get all text except footer
            all_text = soup_release.get_text(separator='\n', strip=True)
            # Remove footer line if contains copyright
            if '&copy;' in all_text:
                # split and take before footer
                parts = all_text.split('&copy;', 1)
                body = parts[0] if len(parts) > 1 else all_text
            else:
                body = all_text
        
        # Clean body: remove extra spaces, ensure at least one newline between paragraphs
        # Simple: replace multiple spaces with single space within lines
        lines = body.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if line:  # keep non-empty
                cleaned_lines.append(line)
        body = '\n\n'.join(cleaned_lines)
        
        # Ensure body length >0
        
        # Build record
        record = {
            'url': link,
            'title': title,
            'date': date_raw if date_raw else None,
            'author': author_raw if author_raw else None,
            'body': body
        }
        records.append(record)
    
    # Sort newest first: date descending
    def get_date(rec):
        d = rec['date']
        if d and isinstance(d, str):
            try:
                dt = parser.parse(d)
                return dt
            except:
                return None
        return None
    
    records.sort(key=get_date, reverse=True)
    
    return records
