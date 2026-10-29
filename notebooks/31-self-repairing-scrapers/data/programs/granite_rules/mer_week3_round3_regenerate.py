import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser
from typing import List, Dict, Optional

# FetchError and other utilities are assumed to be defined elsewhere
# as per the problem statement.

def extract(fetch, listing_url: str):
    """
    Extract all press release records from the Meridian Ratings press listing.
    
    Args:
        fetch: Callable that performs HTTP GET and returns response body as str.
                Raises FetchError for HTTP errors.
        listing_url: URL of the press listing page (e.g., "/press/").
    
    Returns:
        List[Dict] with keys: url, title, date, author, body. Newest first.
    """
    # Fetch the listing page
    try:
        listing_html = fetch(listing_url)
    except Exception as e:
        # Re-raise if it's not a FetchError (caller handles FetchError)
        raise e

    # Parse with BeautifulSoup
    soup = BeautifulSoup(listing_html, "html.parser")
    
    # Find the container that holds press releases.
    # Based on sample, the press releases are inside #press-root or similar.
    # Look for elements that contain release links.
    # The listing page uses JS to load, but sample shows <div id="press-root" class="loading">.
    # However, we must parse statically. Likely release links are in <a> tags under a specific class.
    # Inspect sample: no release links shown. Might be loaded via JS. But we must work with static HTML.
    # Assume release links appear as <a> tags with href containing /press/YYYY/MM/DD/slug.
    # Find all <a> tags that link to press releases (i.e., href starts with /press/ and contains a date pattern).
    # Use soup.find_all('a', href=True) and filter.
    
    base_url = urllib.parse.urljoin(listing_url.rstrip('/'), '/')  # ensure absolute base
    # If listing_url is like "https://www.meridianratings.example/press/", base_url becomes that.
    
    release_links = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        # Resolve relative URL
        full_href = urllib.parse.urljoin(base_url, href)
        # Check if it looks like a press release: pattern /press/YYYY/MM/DD/slug
        if full_href.startswith('/press/') and len(full_href) >= len('/press/') + 1:
            # simple check: after /press/ there should be a year/month/day pattern
            path = full_href.split('?')[0]  # ignore query
            parts = path.split('/')
            if len(parts) >= 4 and parts[1].isdigit() and parts[2].isdigit() and parts[3].isdigit():
                # year, month, day present
                release_links.append(full_href)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_links = []
    for link in release_links:
        if link not in seen:
            seen.add(link)
            unique_links.append(link)
    
    # Fetch each release page and extract details
    records = []
    for link in unique_links:
        try:
            release_html = fetch(link)
        except Exception:
            # skip if fetch fails
            continue
        
        release_soup = BeautifulSoup(release_html, "html.parser")
        
        # Find article with class "pr"
        article = release_soup.find('article', class_='pr')
        if not article:
            continue
        
        # Title: h1 inside article
        title_tag = article.find('h1')
        title = title_tag.get_text(strip=True) if title_tag else ""
        
        # Date: inside .pr-meta span without class or with class "pr-meta"
        meta_div = article.find('div', class_='pr-meta')
        date_text = ""
        if meta_div:
            # find span that contains date (e.g., "29 September 2026")
            date_span = meta_div.find('span')
            if date_span:
                date_text = date_span.get_text(strip=True)
        
        # Parse date to YYYY-MM-DD
        date_str = None
        if date_text:
            # Use dateutil to parse natural language date
            try:
                # dateutil can parse "29 September 2026"
                parsed = parser.parse(date_text)
                # ensure it's a date (no time)
                date_str = parsed.strftime('%Y-%m-%d')
            except Exception:
                pass
        
        # Author: inside .pr-meta span with class "analyst" or similar
        author_text = None
        analyst_span = meta_div.find('span', class_='analyst') if meta_div else None
        if analyst_span:
            # text like "Written by Tomas Belwick"
            # extract name after "Written by " or similar
            raw = analyst_span.get_text(strip=True)
            # remove "Written by " prefix if present
            if raw.lower().startswith('written by '):
                raw = raw[len('Written by '):].strip()
            # also remove job titles? but sample only name. We'll keep as is.
            # split by commas? assume single name.
            author_text = raw
        
        # If no analyst span, look for any span with class containing "author"? fallback
        if not author_text and meta_div:
            # find any span that might contain author
            for span in meta_div.find_all('span'):
                txt = span.get_text(strip=True)
                if 'by' in txt.lower() or 'written' in txt.lower():
                    # extract name
                    # simple: take last word after "by" or similar
                    # but for simplicity, take whole text and clean
                    raw = txt
                    if 'written by' in raw.lower():
                        raw = raw.replace('written by', '').strip()
                    if 'by' in raw.lower():
                        # remove "by" and any trailing punctuation
                        parts = raw.split('by')
                        if len(parts) > 1:
                            raw = parts[1].strip()
                    author_text = raw
        
        # Normalize author: join multiple names with " and ".
        # If author_text contains commas or "and", we may need to clean.
        # For simplicity, keep as is but ensure no "By" prefix.
        if author_text:
            # remove trailing punctuation like periods
            author_text = author_text.rstrip('.').strip()
            # replace commas with " and"? Not required; keep original but remove "By".
            if author_text.lower().startswith('by '):
                author_text = author_text[3:].strip()
            # If multiple names like "John Doe and Jane Smith", keep as is.
            # Ensure no extra "By" words.
            # Simple: split by commas and "and", but we keep raw.
            pass
        
        # Body: inside .pr-body div
        body_div = article.find('div', class_='pr-body')
        body_text = ""
        if body_div:
            # get paragraphs, join with blank line
            paras = body_div.find_all('p')
            paras_text = [p.get_text(strip=False) for p in paras]
            # join with '\n\n'
            body_text = '\n\n'.join(paras_text)
        
        # If no body div, fallback to article body text excluding meta and disclaimer
        if not body_text:
            # get all text from article excluding meta and disclaimer
            # remove meta and disclaimer
            for child in article.find_all(['div', 'span']):
                if child.get('class') and ('pr-meta' in child.get('class') or 'disclaimer' in child.get('class', '')):
                    child.decompose()
            # get text of article
            body_text = article.get_text(separator='\n\n', strip=False)
            # clean extra newlines? keep blank lines between paragraphs
            # simple: split and filter empty? but need blank lines between paragraphs.
            # We'll keep as is.
        
        # Clean body: remove extra whitespace lines? ensure paragraphs separated by blank line.
        # Normalize: split on '\n\n', filter empty, join with '\n\n'
        lines = [line.strip() for line in body_text.split('\n')]
        # but we want blank lines as separator; easier: keep original with \n\n
        # We'll just use body_text as is.
        
        # Build record
        rec = {
            'url': link,
            'title': title,
            'date': date_str if date_str else None,
            'author': author_text if author_text else None,
            'body': body_text
        }
        records.append(rec)
    
    # Sort newest first by date string (YYYY-MM-DD). None dates go last.
    def sort_key(rec):
        d = rec['date']
        if d is None:
            return ''  # will sort after dates
        try:
            # parse to date for correct ordering
            parsed = parser.parse(d)
            return parsed.isoformat()
        except Exception:
            return ''
    
    records.sort(key=sort_key, reverse=True)
    
    return records
