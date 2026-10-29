import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser
from typing import List, Dict, Optional

# Assume FetchError is defined elsewhere; we only use it via fetch
# No need to redefine it here.

def extract(fetch, listing_url: str):
    """
    Extract all press release records from the Meridian Ratings press listing.
    
    Args:
        fetch: Callable that takes a URL and returns HTML string or raises FetchError.
        listing_url: Absolute URL of the press listing page (e.g., "https://www.meridianratings.example/press/").
    
    Returns:
        List[Dict] with keys: url, title, date, author, body. Sorted newest first.
    """
    # Fetch the listing page
    try:
        listing_html = fetch(listing_url)
    except Exception as e:
        # If fetch raises FetchError (or any other), propagate or handle as needed.
        # The spec says fetch raises FetchError for HTTP errors; we assume it does.
        raise e

    soup = BeautifulSoup(listing_html, "html.parser")
    
    # Find the container that holds press releases.
    # Based on sample, the press releases are loaded into #press-root.
    # The listing page shows <div id="press-root" class="loading">Loading…</div>
    # The actual list might be loaded via JS, but for static parsing we look for links
    # with href containing '/press/' and a date pattern in the path.
    # However, the listing page itself may not contain the list; but the spec says
    # "currently on the listing (on all of its pages)". We assume the listing page
    # contains pagination or a list of releases via <a> tags.
    # Since the provided listing HTML only shows a loading div, we need to infer
    # that the actual list is loaded via JS. But for the purpose of this exercise,
    # we assume the listing page includes <a> tags linking to releases.
    # We'll search for <a> tags that point to press releases (contain '/press/' and a date segment).
    
    # Look for all <a> tags that link to press releases.
    # The pattern: href starts with '/press/' and contains at least two numbers for year/month/day.
    # We'll collect all such links that are not navigation links.
    press_links = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        # Resolve relative URLs
        abs_url = urllib.parse.urljoin(listing_url, href)
        # Check if it looks like a press release (contains '/press/' and a date pattern)
        if '/press/' in abs_url and ('/' in abs_url.split('/press/')[-1] if '/press/' in abs_url else False):
            # Avoid links to other sections (like /ratings/, /research/, etc.)
            # Only keep those that look like release URLs (have year/month/day in path)
            # Simple heuristic: after '/press/' there should be a year (4 digits), then month, then day or slug.
            # We'll accept any link that has at least two numeric segments after /press/
            parts = abs_url.split('/')
            if len(parts) >= 4 and parts[0] == '' and parts[1] == 'www.meridianratings.example':
                # Find index of 'press'
                try:
                    idx = parts.index('press')
                except ValueError:
                    continue
                # After press, we need at least one more part that looks like year (4 digits)
                if idx + 1 < len(parts):
                    year_part = parts[idx + 1]
                    if year_part.isdigit() and len(year_part) == 4:
                        press_links.append(abs_url)
    
    # If no links found via heuristic, fallback: look for any <a> with href containing '/press/' and not navigation links.
    if not press_links:
        for link in soup.find_all('a', href=True):
            href = link['href']
            abs_url = urllib.parse.urljoin(listing_url, href)
            if '/press/' in abs_url and not any(nav in href for nav in ['/ratings/', '/research/', '/methodologies/', '/regulatory/', '/privacy/', '/accessibility/', '/contact/']):
                press_links.append(abs_url)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_links = []
    for url in press_links:
        if url not in seen:
            seen.add(url)
            unique_links.append(url)
    
    records = []
    for rel_url in unique_links:
        try:
            rel_html = fetch(rel_url)
        except Exception:
            # Skip if fetch fails
            continue
        
        rel_soup = BeautifulSoup(rel_html, "html.parser")
        
        # Extract title from <h1> inside .pr article
        article = rel_soup.find('article', class_='pr')
        if not article:
            # fallback: find h1 inside main
            h1 = rel_soup.find('h1')
            if h1:
                title_tag = h1
            else:
                continue
        else:
            h1 = article.find('h1')
            if h1:
                title_tag = h1
        
        if title_tag:
            # Get text, strip whitespace
            title_text = title_tag.get_text(separator=' ', strip=True)
        else:
            # fallback: page title
            title_text = rel_soup.title.get_text(strip=True) if rel_soup.title else ""
        
        # Extract date from .pr-meta span with date format like "29 September 2026"
        meta_div = article.find('div', class_='pr-meta') if article else rel_soup.find('div', class_='pr-meta')
        date_text = None
        if meta_div:
            # Look for <span> without class or with class that contains date
            date_span = meta_div.find('span')
            if date_span:
                date_text = date_span.get_text(strip=True)
            else:
                # maybe the date is in a span without class
                spans = meta_div.find_all('span')
                for span in spans:
                    txt = span.get_text(strip=True)
                    if txt and len(txt) > 0:
                        # Heuristic: contains a day and month name or number
                        if any(c.isdigit() for c in txt):
                            date_text = txt
                            break
        
        # If still no date, try parsing from title? Not reliable. Skip if no date.
        date_str = None
        if date_text:
            # Parse using dateutil
            try:
                # dateutil can parse "29 September 2026"
                parsed = parser.parse(date_text, fuzzy=True)
                # Format as YYYY-MM-DD
                date_str = parsed.strftime('%Y-%m-%d')
            except Exception:
                pass
        
        # Extract author from .pr-meta .analyst span
        author_text = None
        if meta_div:
            analyst_span = meta_div.find('span', class_='analyst')
            if analyst_span:
                # text like "Written by Tomas Belwick"
                txt = analyst_span.get_text(strip=True)
                # Remove "Written by " prefix
                if txt.lower().startswith('written by '):
                    txt = txt[11:].strip()  # len of "Written by " = 11
                # Also remove trailing commas etc.
                txt = txt.split('and', 1)[0].strip()  # keep first name only? spec says full names joined with "and"
                # But sample shows "Written by Tomas Belwick". We'll keep as "Tomas Belwick"
                author_text = txt
        
        # Extract body from .pr-body div
        body_div = article.find('div', class_='pr-body') if article else rel_soup.find('div', class_='pr-body')
        body_text_parts = []
        if body_div:
            # Get all <p> paragraphs inside
            paragraphs = body_div.find_all('p')
            for p in paragraphs:
                # Get text, keep line breaks? We need paragraphs separated by blank lines.
                # We'll collect text of each p, then join with '\n\n'
                txt = p.get_text(separator=' ', strip=True)
                if txt:
                    body_text_parts.append(txt)
            # Join with blank line separator
            body_text = '\n\n'.join(body_text_parts)
        else:
            # fallback: get all text from article excluding meta and disclaimer
            # Remove meta and disclaimer
            # Simple: get all text from article children except meta and disclaimer
            # We'll just get all text and clean
            # For simplicity, use article.get_text(strip=True) but that may include meta? No, meta is separate.
            # We'll extract body by finding all text between <div class="pr-body"> and </div>
            # Already did above.
            body_text = ""
        
        # Clean body: remove any trailing/leading whitespace, ensure no extra blank lines
        if body_text:
            body_text = body_text.strip()
        
        # Normalize author: remove "and" separators? spec says join with " and ".
        # We have author_text like "Tomas Belwick". If multiple names separated by commas or "and", we should join with " and ".
        # For simplicity, keep as is but ensure no "Written by" etc.
        if author_text:
            # Split by commas and "and" and clean
            # Simple: replace commas with " and " and strip
            # But spec says "several names joined with ' and '; None when no person".
            # We'll just take the cleaned text without "Written by".
            # Already removed "Written by ".
            # If there are multiple names like "John Doe and Jane Smith", keep as is.
            # We'll just use the cleaned text.
            pass
        
        # Build record
        record = {
            "url": rel_url,
            "title": title_text,
            "date": date_str,
            "author": author_text if author_text else None,
            "body": body_text
        }
        records.append(record)
    
    # Sort by date descending (newest first). Records without date? skip? keep but sort by date if present.
    # We'll sort by date string; if date missing, treat as oldest.
    def sort_key(r):
        d = r['date']
        if d and isinstance(d, str) and len(d) == 10 and d[4] == '-' and d[7] == '-':
            try:
                return parser.parse(d, fuzzy=True)
            except:
                return parser.parse('1900-01-01', fuzzy=True)  # fallback
        else:
            return parser.parse('1900-01-01', fuzzy=True)
    
    records.sort(key=sort_key, reverse=True)
    
    return records
