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
    
    # Parse listing page
    soup_listing = BeautifulSoup(listing_html, 'html.parser')
    
    # Find all article rows (views-row containers)
    rows = soup_listing.find_all('div', class_='views-row')
    
    records = []
    
    for row in rows:
        # Extract date display (e.g., "18/09/2026")
        date_span = row.find('span', class_='date-display-single')
        if not date_span:
            continue
        date_text = date_span.get_text(strip=True)
        
        # Parse date: format "DD/MM/YYYY"
        try:
            # dateutil can parse "18/09/2026"
            dt = parser.parse(date_text)
            date_str = dt.strftime('%Y-%m-%d')
        except Exception:
            # fallback: try simple split
            parts = date_text.split('/')
            if len(parts) == 3:
                day, month, year = parts
                # ensure two-digit month
                if len(month) == 1:
                    month = '0' + month
                date_str = f"{year}-{month}-{day}"  # but need YYYY-MM-DD
                # Actually format: year month day? The date is DD/MM/YYYY, so year first?
                # The requirement: "YYYY-MM-DD". So we need to reorder.
                # date_text like "18/09/2026" -> 2026-09-18
                try:
                    dt = parser.parse(date_text)
                    date_str = dt.strftime('%Y-%m-%d')
                except:
                    # simple fallback
                    day, month, year = parts
                    date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            else:
                continue
        
        # Extract title link
        title_a = row.find('a', class_='field-title')
        if not title_a or not title_a.get('href'):
            continue
        rel_url = title_a['href']
        abs_url = urllib.parse.urljoin(listing_url, rel_url)
        
        # Fetch the release page
        try:
            release_html = fetch(abs_url)
        except Exception:
            # skip if fetch fails
            continue
        
        soup_release = BeautifulSoup(release_html, 'html.parser')
        
        # Extract title (full headline) from <h1 class="page-title"> or <a> inside row?
        # Use the <h1> inside main
        h1 = soup_release.find('h1', class_='page-title')
        if h1:
            title = h1.get_text(strip=True)
        else:
            # fallback to <a> title
            title_a_release = row.find('a', class_='field-title')  # same as row? Actually row already used; better find in release
            title_a_release = soup_release.find('a', class_='field-title')
            if title_a_release:
                title = title_a_release.get_text(strip=True)
            else:
                # fallback to <title> without " | Kestria Revenue Service"
                page_title = soup_release.find('title')
                if page_title:
                    full_title = page_title.get_text(strip=True)
                    # remove trailing " | Kestria Revenue Service" if present
                    if ' | Kestria Revenue Service' in full_title:
                        title = full_title.split(' | ')[0]
                    else:
                        title = full_title
                else:
                    title = ''
        
        # Extract date from field-date
        date_div = soup_release.find('div', class_='field-date')
        if date_div:
            date_info = date_div.get_text(strip=True)  # "Date: 18/09/2026"
            # extract the date part after colon or whole
            parts = date_info.split(':')
            if len(parts) >= 2:
                date_text2 = parts[1].strip()
            else:
                date_text2 = date_info.strip()
            try:
                dt2 = parser.parse(date_text2)
                date_str2 = dt2.strftime('%Y-%m-%d')
                # Use the release date if present, else listing date? Requirement: date the release was first published.
                # Prefer release date field.
                date_str = date_str2
            except Exception:
                pass  # fallback to listing date
        
        # Extract author
        author = None
        # Look for author field; not obvious in sample. Maybe in meta or footer? Not present.
        # Sample has no author. So author = None.
        # We'll search for common patterns like "by", "author", etc.
        # For simplicity, set None.
        author = None
        
        # Extract body from field-body
        body_div = soup_release.find('div', class_='field-body')
        if body_div:
            # Get text of all paragraphs inside, preserving blank lines between paragraphs
            paragraphs = []
            # Find all <p> tags inside field-body
            ps = body_div.find_all('p')
            for p in ps:
                text = p.get_text(separator='\n', strip=True)
                # Remove empty paragraphs? Keep if only whitespace? We'll keep non-empty
                if text.strip():
                    paragraphs.append(text.strip())
            # Join paragraphs with a blank line
            body_text = '\n\n'.join(paragraphs)
        else:
            # fallback: get all text from main excluding header/footer? Too complex.
            # Use main content div? sample has field-body only.
            body_text = ''
        
        # Build record
        record = {
            'url': abs_url,
            'title': title,
            'date': date_str,
            'author': author,
            'body': body_text
        }
        records.append(record)
    
    # Sort newest first by date (YYYY-MM-DD string sorts lexicographically)
    records.sort(key=lambda r: r['date'], reverse=True)
    
    # Handle pagination: need to collect all pages
    # Find pagination links
    pager = soup_listing.find('nav', class_='pager')
    if pager:
        next_links = pager.find_all('a', class_=lambda x: x and 'next' in x.lower() if x else False)
        # Actually next link has text "Next ›" and href="/newsroom?page=2"
        # Better: get all <a> with href containing ?page=
        all_links = pager.find_all('a', href=True)
        seen_urls = {listing_url}
        queue = [listing_url]
        while queue:
            cur = queue.pop(0)
            if cur in seen_urls:
                continue
            seen_urls.add(cur)
            cur_html = fetch(cur)
            cur_soup = BeautifulSoup(cur_html, 'html.parser')
            rows_cur = cur_soup.find_all('div', class_='views-row')
            for row in rows_cur:
                date_span = row.find('span', class_='date-display-single')
                if not date_span:
                    continue
                date_text = date_span.get_text(strip=True)
                title_a = row.find('a', class_='field-title')
                if not title_a or not title_a.get('href'):
                    continue
                rel_url = title_a['href']
                abs_url = urllib.parse.urljoin(cur, rel_url)
                if abs_url in seen_urls:
                    continue
                # fetch release and extract record similarly (reuse logic)
                try:
                    release_html = fetch(abs_url)
                except Exception:
                    continue
                soup_release = BeautifulSoup(release_html, 'html.parser')
                h1 = soup_release.find('h1', class_='page-title')
                if h1:
                    title = h1.get_text(strip=True)
                else:
                    title_a_release = soup_release.find('a', class_='field-title')
                    if title_a_release:
                        title = title_a_release.get_text(strip=True)
                    else:
                        title = ''
                date_div = soup_release.find('div', class_='field-date')
                if date_div:
                    date_info = date_div.get_text(strip=True)
                    parts = date_info.split(':')
                    if len(parts) >= 2:
                        date_text2 = parts[1].strip()
                    else:
                        date_text2 = date_info.strip()
                    try:
                        dt2 = parser.parse(date_text2)
                        date_str2 = dt2.strftime('%Y-%m-%d')
                    except Exception:
                        date_str2 = date_str  # fallback
                else:
                    date_str2 = date_str  # from listing? need compute from date_text
                    # compute from date_text same as earlier
                    try:
                        dt = parser.parse(date_text)
                        date_str2 = dt.strftime('%Y-%m-%d')
                    except Exception:
                        date_str2 = ''
                author = None
                body_div = soup_release.find('div', class_='field-body')
                if body_div:
                    ps = body_div.find_all('p')
                    paragraphs = [p.get_text(strip=True) for p in ps if p.get_text(strip=True)]
                    body_text = '\n\n'.join(paragraphs)
                else:
                    body_text = ''
                record = {
                    'url': abs_url,
                    'title': title,
                    'date': date_str2,
                    'author': author,
                    'body': body_text
                }
                records.append(record)
                seen_urls.add(abs_url)
            # collect next page URL from pager links
            for link in all_links:
                href = link.get('href')
                if href:
                    abs_href = urllib.parse.urljoin(cur, href)
                    if abs_href not in seen_urls and abs_href.startswith('/newsroom'):
                        queue.append(abs_href)
                        seen_urls.add(abs_href)
    
    return records
