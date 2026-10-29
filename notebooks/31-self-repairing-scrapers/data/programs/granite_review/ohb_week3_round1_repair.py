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
        title_tag = None
        # Look for <b> inside the second td (content column)
        content_td = soup_release.find('td', valign='top')
        if content_td:
            title_tag = content_td.find('b')
        if not title_tag:
            # fallback: find <font size="4"><b> pattern
            title_tag = soup_release.find('font', size='4')
            if title_tag:
                title_tag = title_tag.find('b')
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
        date_line = None
        for font in soup_release.find_all('font'):
            txt = font.get_text(strip=False)
            if 'Posted:' in txt:
                date_line = txt
                break
        if date_line:
            # Example: "Posted: Monday, September 28, 2026"
            # Use dateutil parser which handles day-of-week
            try:
                parsed = parser.parse(date_line, fuzzy=True)
                date_str = parsed.strftime("%Y-%m-%d")
            except Exception:
                # fallback regex
                import re
                m = re.search(r'(\d{1,2})\s*[A-Za-z]+,\s*[A-Za-z]+\s+\d{4}', date_line)
                if m:
                    # crude fallback not used
                    date_str = "1900-01-01"
                else:
                    date_str = "1900-01-01"
        else:
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
                    except:
                        pass
            else:
                date_str = "1900-01-01"
        
        # Extract author from "Posted by:" line
        author_text = None
        for font in soup_release.find_all(['font', 'span']):
            txt = font.get_text(strip=False)
            if 'Posted by:' in txt:
                # extract after "Posted by:"
                parts = txt.split('Posted by:', 1)
                if len(parts) > 1:
                    raw_author = parts[1].strip()
                    # remove trailing punctuation like '.'
                    raw_author = raw_author.rstrip('.').rstrip(',')
                    # remove possible "By" prefix
                    if raw_author.lower().startswith('by '):
                        raw_author = raw_author[3:].strip()
                    # author may contain multiple names separated by commas? join with " and"
                    # simple: keep as is
                    author_text = raw_author
                break
        if author_text:
            # clean extra spaces
            author_text = author_text.strip()
        else:
            author_text = None
        
        # Extract body: main text between title and footer
        # Find footer row with &copy;
        footer_row = soup_release.find('tr', string=lambda s: s and '&copy;' in s)
        body_parts = []
        # iterate through children of content td excluding title and footer
        content_td = soup_release.find('td', valign='top')
        if content_td:
            for child in content_td.children:
                if child.name == 'font':
                    # skip title font (contains title text)
                    if child.find_parent('b') and title_tag:
                        # simple check: if child's text matches title? crude
                        pass
                    # get text, replace <br> with '\n\n'
                    txt = child.get_text(separator=' ')
                    # replace <br> tags that might be inside? they are separate tags
                    # but get_text collapses whitespace; we need to preserve paragraph breaks
                    # Instead collect text from all <font> tags except title and footer
                    # simpler: get all text from content_td, strip title line and footer
                    # We'll collect all <font> text that is not title and not footer
                    pass
                # fallback: collect all <font> text except title and footer
            for font in content_td.find_all('font'):
                # skip if font contains title (simple check)
                if font.find_parent('b') and title_tag:
                    continue
                if footer_row in font.parents:
                    continue
                txt = font.get_text(strip=False)
                # replace <br> tags with '\n\n' (they appear as <br> tags)
                # since get_text collapses, we need to look inside
                # easier: get the raw string of the font tag and replace <br>
                raw = str(font)
                raw = raw.replace('<br>', '\n\n').replace('<br />', '\n\n')
                # extract text between <font>...</font> without tags? use .get_text won't keep <br>
                # use .contents and join?
                # simple: use .get_text with separator=' ' then replace <br>? not accurate
                # Given constraints, use .get_text and rely on <br> being rendered as <br> in HTML;
                # BeautifulSoup .get_text() will convert <br> to newline? No, it treats as text node? Actually <br> is a tag, .get_text() will output empty? It outputs the tag name? No, .get_text() returns text without tags, but <br> has no text, so it disappears.
                # So we need to manually replace <br> tags with '\n\n' before extracting text.
                # We'll do: replace <br> tags in the whole content_td string? Too heavy.
                # Simpler: get all text from content_td excluding title and footer using .get_text and then clean?
                # Given sample, body consists of <font size="2"> paragraphs separated by <br><br>.
                # We'll collect text from each <font> tag (size 2) and join with '\n\n'
                if 'size="2"' in font.attrs or 'size="2"' in str(font):
                    txt = font.get_text(strip=False)
                    # replace <br> tags inside? they are separate tags, not inside font? In sample, <br> are separate <br> tags outside <font>.
                    # Actually sample: <font size="2">text<br><br>more</font>? No, <br> appear outside <font>.
                    # Let's just get all text from content_td excluding title row and footer row by walking.
                    pass
        # Very simplified: get all text from content_td, remove title line and footer line
        all_text = content_td.get_text(separator=' ')
        # Remove the title line (contains title) and "Posted:" line? We'll extract body after title and before footer.
        # Find index of title text in all_text? Not reliable.
        # Given time, use simple: get text from all <font> tags except the title <b> and footer.
        body_text_parts = []
        for font in content_td.find_all('font'):
            if font.find_parent('b') and title_tag:
                continue
            if footer_row in font.parents:
                continue
            txt = font.get_text(strip=False)
            # replace <br> tags that might be adjacent? we can't because get_text removes tags.
            # In sample, body paragraphs are separated by <br><br> which appear as <br> tags outside <font>.
            # So we need to also consider <br> tags.
            # Collect all text nodes (tags and text) and replace <br> with '\n\n'
            # Simpler: get the whole content_td as string and replace <br> with '\n\n' then extract between title and footer.
            # We'll do: get the raw HTML of content_td, replace <br> with '\n\n', then parse again? Too complex.
            # Given constraints, return body as concatenation of font texts with '\n\n' between non-empty.
            if txt.strip():
                body_text_parts.append(txt.strip())
        body_text = '\n\n'.join(body_text_parts)
        if not body_text:
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
