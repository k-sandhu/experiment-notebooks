import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser
from typing import List, Dict

# FetchError is assumed to be defined elsewhere; not imported here

def extract(fetch, listing_url: str) -> List[Dict]:
    """
    Extract all news releases from the listing page and return records.
    """
    try:
        listing_html = fetch(listing_url)
    except Exception as e:
        raise e

    soup_listing = BeautifulSoup(listing_html, "html.parser")
    
    # Find all news item links in the listing
    news_links = []
    for link_tag in soup_listing.find_all('a', href=True):
        href = link_tag['href']
        if href.startswith('news_item.asp'):
            abs_url = urllib.parse.urljoin(listing_url, href)
            news_links.append(abs_url)
    
    records = []
    for rel_url in news_links:
        try:
            release_html = fetch(rel_url)
        except Exception:
            continue
        
        soup_release = BeautifulSoup(release_html, "html.parser")
        
        # Extract title: find the <b> tag inside the content td (the one with size 4)
        content_td = soup_release.find('td', valign='top')
        if content_td:
            title_tag = content_td.find('b')
            if not title_tag:
                # fallback: find <font size="4"><b> pattern
                font4 = content_td.find('font', attrs={'size': '4'})
                if font4:
                    title_tag = font4.find('b')
        if title_tag:
            title_text = title_tag.get_text(strip=True)
        else:
            # fallback: use <title> minus prefix
            title_tag = soup_release.find('title')
            if title_tag:
                title_text = title_tag.get_text(strip=True)
                prefix = "Oakhill Bakeries Group - "
                if title_text.startswith(prefix):
                    title_text = title_text[len(prefix):].strip()
                else:
                    title_text = title_text
            else:
                title_text = "Unknown"
        
        # Extract date from "Posted:" line
        date_str = None
        for font in soup_release.find_all('font'):
            txt = font.get_text(strip=False)
            if 'Posted:' in txt:
                # Example: "Posted: Monday, September 28, 2026"
                try:
                    parsed = parser.parse(txt, fuzzy=True)
                    date_str = parsed.strftime("%Y-%m-%d")
                except Exception:
                    pass
        if not date_str:
            # fallback: look for pattern like "Sep 28, 2026"
            import re
            pattern = r'([A-Za-z]{3,9})\s+\d{1,2},\s+\d{4}'
            for font in soup_release.find_all(['font', 'span']):
                txt = font.get_text()
                m = re.search(pattern, txt)
                if m:
                    try:
                        parsed = parser.parse(m.group(0), fuzzy=True)
                        date_str = parsed.strftime("%Y-%m-%d")
                        break
                    except Exception:
                        pass
        if not date_str:
            date_str = "1900-01-01"
        
        # Extract author from "Posted by:" line
        author_text = None
        for font in soup_release.find_all(['font', 'span']):
            txt = font.get_text(strip=False)
            if 'Posted by:' in txt:
                parts = txt.split('Posted by:', 1)
                if len(parts) > 1:
                    raw_author = parts[1].strip()
                    # remove trailing punctuation like '.'
                    raw_author = raw_author.rstrip('.').rstrip(',')
                    # remove possible "By" prefix
                    low = raw_author.lower()
                    if low.startswith('by '):
                        raw_author = raw_author[3:].strip()
                    # author may contain multiple names separated by commas? join with " and"
                    # simple: keep as is
                    author_text = raw_author
                break
        if author_text:
            author_text = author_text.strip()
        else:
            author_text = None
        
        # Extract body: main text between title and footer
        # Find footer row with &copy;
        footer_row = soup_release.find('tr', string=lambda s: s and '&copy;' in s)
        body_parts = []
        if content_td:
            # Get all text nodes from content_td excluding title and footer
            # Collect text from <font> tags and <br> tags
            for child in content_td.descendants:
                if child.name == 'font':
                    txt = child.get_text(separator=' ')
                    # replace <br> tags that might be adjacent? we need to handle <br> tags separately
                    # Instead, we collect raw text and later insert newlines
                    # Simple approach: get all text from content_td, then split by <br>
                    # We'll collect all text from <font> tags and <br> tags
                    # but easier: get the whole content_td string and replace <br> with '\n\n'
                    pass
            # Reconstruct body by walking content_td and replacing <br> with '\n\n'
            # Get the raw HTML of content_td as string
            raw_content = str(content_td)
            # Replace <br> and <br /> with '\n\n'
            raw_content = raw_content.replace('<br>', '\n\n').replace('<br />', '\n\n')
            # Parse again to get text with newlines
            temp_soup = BeautifulSoup(raw_content, "html.parser")
            # Find all text nodes that are not inside title <b> or footer
            # Collect paragraphs: text between <br> tags
            # Simple: get all text from temp_soup.contents that are not title or footer
            # We'll extract all text from temp_soup excluding the title <b> and footer row
            # Remove title <b> by hiding it
            # Find title <b> and remove its text from consideration
            title_b = content_td.find('b') if content_td.find('b') else None
            # Collect all text nodes that are not inside title_b and not inside footer_row
            collected = []
            for node in temp_soup.find('td', valign='top').descendants:
                if node.name == 'b' and title_b and node == title_b:
                    continue
                if footer_row and footer_row in node.parents:
                    continue
                if node.name == 'br':
                    collected.append('\n\n')
                elif node.name == 'font':
                    txt = node.get_text(strip=False)
                    collected.append(txt)
                elif node.name is None:  # NavigableString
                    txt = str(node)
                    # if it's whitespace, skip? keep
                    collected.append(txt)
            # Join collected with spaces? but we want paragraphs separated by blank lines
            # We'll join with '\n\n' between non-empty text blocks
            body_lines = []
            for item in collected:
                if item.strip():
                    body_lines.append(item.strip())
            body_text = '\n\n'.join(body_lines)
        else:
            body_text = ""
        
        # Build record
        record = {
            "url": rel_url,
            "title": title_text,
            "date": date_str,
            "author": author_text,
            "body": body_text
        }
        records.append(record)
    
    # Sort newest first
    records.sort(key=lambda x: x["date"], reverse=True)
    return records
