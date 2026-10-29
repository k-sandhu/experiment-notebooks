import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser
from typing import List, Dict, Optional

# Assume FetchError is defined elsewhere; we import it here
# from extractor import FetchError  # Not needed for this snippet

def extract(fetch, listing_url: str) -> List[Dict]:
    """
    Extract all news releases from the listing page and return records.
    """
    try:
        listing_html = fetch(listing_url)
    except Exception as e:
        # Re-raise if fetch fails
        raise e

    # Parse listing page
    soup_listing = BeautifulSoup(listing_html, "html.parser")
    
    # Find all news item links in the listing
    news_links = []
    # The listing uses <a> tags inside <td> cells with href like "news_item.asp?id=7790"
    # Look for <a> tags that contain href starting with "news_item.asp"
    for link_tag in soup_listing.find_all('a', href=True):
        href = link_tag['href']
        if href.startswith('news_item.asp'):
            # Resolve absolute URL
            abs_url = urllib.parse.urljoin(listing_url, href)
            news_links.append(abs_url)
    
    # Collect release records
    records = []
    for rel_url in news_links:
        try:
            release_html = fetch(rel_url)
        except Exception:
            # Skip if fetch fails
            continue
        
        soup_release = BeautifulSoup(release_html, "html.parser")
        
        # Extract title: find the main headline <b> or <font> with size 4 etc.
        # In sample, title appears as <font face="Arial" size="4"><b>Title</b></font>
        title_tag = soup_release.find('b')
        if not title_tag:
            # fallback: find font size 4
            title_tag = soup_release.find('font', size='4')
        if title_tag:
            # Get text, clean up extra <br> etc.
            title_text = title_tag.get_text(strip=True)
        else:
            # fallback: title from <title> tag minus prefix
            title_tag = soup_release.find('title')
            if title_tag:
                title_text = title_tag.get_text(strip=True)
                # Remove "Oakhill Bakeries Group - " prefix if present
                if title_text.startswith("Oakhill Bakeries Group - "):
                    title_text = title_text[len("Oakhill Bakeries Group - "):].strip()
            else:
                title_text = "Unknown"
        
        # Extract date: look for "Posted:" line
        date_line = None
        for span in soup_release.find_all(['font', 'span'], text=lambda t: t and 'Posted:' in t):
            date_line = span.get_text(strip=True)
            break
        if date_line:
            # Example: "Monday, September 28, 2026"
            # Use dateutil to parse
            # Extract date part (ignore day of week)
            # Simple split
            parts = date_line.split(',')
            if len(parts) >= 2:
                day_str = parts[1].strip().split()[0]  # "September 28"
                year_str = parts[1].strip().split()[2]  # "2026"
                month_str = parts[1].strip().split()[1]  # "September"
                try:
                    # Use dateutil parser for robustness
                    parsed = parser.parse(date_line)
                    # Return date only
                    date_str = parsed.strftime("%Y-%m-%d")
                except Exception:
                    # fallback: extract month name to number
                    from calendar import month_abbr
                    month_num = None
                    for i, abbr in enumerate(month_abbr[1:], 1):
                        if month_str.lower() == abbr.lower():
                            month_num = i
                            break
                    if month_num:
                        # day and year from parts
                        day = int(parts[1].split()[0].split()[1] if ' ' in parts[1].split()[0] else parts[1].split()[0])  # not reliable
                        # simpler: use regex
                        import re
                        match = re.search(r'(\d{1,2})', parts[1])
                        if match:
                            day = int(match.group(1))
                        year = int(parts[1].split()[2])
                        date_str = f"{year:04d}-{month_num:02d}-{day:02d}"
                    else:
                        date_str = "1900-01-01"  # fallback
            else:
                date_str = "1900-01-01"
        else:
            # fallback: maybe in <meta> or other
            # search for date pattern
            import re
            # look for patterns like "Sep 28, 2026"
            pattern = r'([A-Za-z]{3,9})\s+\d{1,2},\s+\d{4}'
            matches = re.findall(pattern, date_line) if date_line else []
            if matches:
                # use first match
                m = matches[0]
                # parse with dateutil
                try:
                    parsed = parser.parse(m)
                    date_str = parsed.strftime("%Y-%m-%d")
                except:
                    date_str = "1900-01-01"
            else:
                date_str = "1900-01-01"
        
        # Extract author: look for "Posted by:" line
        author_text = None
        for span in soup_release.find_all(['font', 'span'], text=lambda t: t and 'Posted by:' in t):
            # get parent or text
            author_line = span.get_text(strip=True)
            # extract after "Posted by:"
            if 'Posted by:' in author_line:
                # split
                parts = author_line.split('Posted by:', 1)
                if len(parts) > 1:
                    author_text = parts[1].strip()
                break
        if author_text:
            # clean: remove job titles? simple: take first name/last name as is, but remove "By" etc.
            # remove trailing punctuation
            author_text = author_text.strip()
            # if contains "By" remove it
            if author_text.lower().startswith('by '):
                author_text = author_text[3:].strip()
            # join multiple names with " and " if needed (unlikely)
            # keep as is
        else:
            author_text = None
        
        # Extract body: main text paragraphs, exclude navigation and footer
        # Find the main content <td> or <font> after title
        # In sample, body is <font face="Arial" size="2">...</font> with <br><br> separators
        body_parts = []
        # Find all <font> tags with size not 1 or 4? simpler: get all text nodes between title and footer
        # locate footer row with &copy;
        footer_row = soup_release.find('tr', string=lambda s: s and '&copy;' in s)
        if footer_row:
            # get content before footer
            # find all <td> before footer
            content_div = None
            for child in soup_release.find('td', recursive=False).children:
                # not reliable; simpler: get all text excluding known footer
                pass
            # fallback: get all <font> tags except title and footer
            # find title tag and footer tag positions
            title_tag = soup_release.find('b') if soup_release.find('b') else None
            # collect text from all <font> tags that are not title and not footer
            for font in soup_release.find_all('font'):
                if font.find_parent(['b']) and title_tag:
                    continue
                if footer_row in font.parents:
                    continue
                text = font.get_text(strip=False)
                # keep <br> as separator? we want blank lines between paragraphs
                # replace <br> with '\n\n'
                text = text.replace('<br>', '\n\n').replace('<br />', '\n\n')
                if text.strip():
                    body_parts.append(text.strip())
            body_text = '\n\n'.join(body_parts)
        else:
            # simple fallback
            # get all text from body excluding first title line and footer
            all_text = soup_release.get_text(separator=' ')
            # remove title line? not perfect
            body_text = all_text
        
        # Clean body: remove extra newlines? ensure paragraphs separated by blank line
        # Already joined with '\n\n'
        body_text = body_text.strip()
        
        # Build record
        record = {
            "url": rel_url,
            "title": title_text,
            "date": date_str,
            "author": author_text if author_text else None,
            "body": body_text
        }
        records.append(record)
    
    # Sort records newest first by date (YYYY-MM-DD string sorts lexicographically)
    # Ensure date strings are valid; filter out fallback "1900-01-01"? keep all
    records.sort(key=lambda x: x["date"], reverse=True)
    return records
