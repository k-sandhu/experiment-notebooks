import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser

# Assume FetchError is defined elsewhere; we only use fetch as provided

def extract(fetch, listing_url):
    # Fetch listing page
    listing_html = fetch(listing_url)
    soup_list = BeautifulSoup(listing_html, 'html.parser')
    
    # Find all news item links in the listing table
    news_links = []
    # Locate the table with news rows; look for <a> tags with href containing news_item.asp
    # Simple approach: find all <a> tags with href containing 'news_item.asp'
    for a_tag in soup_list.find_all('a', href=True):
        href = a_tag['href']
        if 'news_item.asp' in href:
            # Resolve absolute URL
            abs_url = urllib.parse.urljoin(listing_url, href)
            # Extract id from href like ?id=7790
            # We'll store the URL for later fetching
            news_links.append(abs_url)
    
    # Sort links by date? Need to get date from listing text (e.g., "Sep 28, 2026")
    # We'll parse date from the text after <b> and before </b>? In listing each row has <b><a>title</b><br>date</font>
    # Let's extract pairs (url, date_text) from listing rows
    records = []
    # Find the inner table after <td valign="top">
    inner_table = soup_list.find('table', {'width': '100%', 'cellpadding': '4'})
    if inner_table:
        rows = inner_table.find_all('tr')
        for row in rows:
            # Find <td> inside row
            td = row.find('td', {'valign': 'top'})
            if td:
                # Find <b><a> link and date
                b_tag = td.find('b')
                if b_tag:
                    a_tag = b_tag.find('a', href=True)
                    if a_tag:
                        href = a_tag['href']
                        abs_url = urllib.parse.urljoin(listing_url, href)
                        # Get title text (full headline) from a_tag.string
                        title = a_tag.get_text(strip=True)
                        # Get date text after <b> and before </b>? Actually date is in <font size="2"> after <b>
                        # Look for <font> containing date
                        date_font = td.find('font', {'size': '2'})  # size 2 font for date
                        if date_font:
                            date_text = date_font.get_text(strip=True)
                            # date_text like "Sep 28, 2026"
                            # parse to date
                            try:
                                # Use dateutil parser
                                pub_date = parser.parse(date_text).date()
                            except Exception:
                                pub_date = None
                        else:
                            pub_date = None
                        # Store for later fetching with date
                        records.append({'url': abs_url, 'title': title, 'date': None, 'author': None, 'body': None, 'raw_date_text': date_text})
    
    # Sort records by pub_date descending (newest first)
    # We'll fetch each release page and extract fields
    # We'll need to map back to records; use list of dicts with url
    # We'll create list of (url, date) pairs
    items = []
    for rec in records:
        url = rec['url']
        date_text = rec.get('raw_date_text')
        try:
            pub_date = parser.parse(date_text).date()
        except Exception:
            pub_date = None
        items.append((url, pub_date, rec))
    
    # Sort by pub_date descending
    items.sort(key=lambda x: x[1] if x[1] else datetime.max, reverse=True)
    
    # Fetch each release and extract
    for url, pub_date, rec in items:
        try:
            release_html = fetch(url)
            soup_rel = BeautifulSoup(release_html, 'html.parser')
            # Title: from <title> or <b> inside body? Use <b> inside body? In sample, <b>Oakhill Revises...</b>
            title_tag = soup_rel.find('b')
            if title_tag:
                rec['title'] = title_tag.get_text(strip=True)
            else:
                # fallback to <title> minus prefix
                title_tag = soup_rel.find('title')
                if title_tag:
                    full_title = title_tag.get_text(strip=True)
                    # remove "Oakhill Bakeries Group - " prefix
                    if full_title.startswith('Oakhill Bakeries Group - '):
                        rec['title'] = full_title[len('Oakhill Bakeries Group - '):].strip()
                    else:
                        rec['title'] = full_title
            
            # Date: from "Posted: Monday, September 28, 2026"
            date_info_tag = soup_rel.find('font', {'size': '1'})  # size 1 font contains Posted: ...
            if date_info_tag:
                date_text_full = date_info_tag.get_text(strip=True)
                # extract date part like "September 28, 2026"
                # simple regex not allowed; use parser on the whole string
                # parser can handle "Monday, September 28, 2026"
                try:
                    # parse and get date
                    dt = parser.parse(date_text_full)
                    rec['date'] = dt.date().isoformat()
                except Exception:
                    # fallback to pub_date from listing
                    rec['date'] = pub_date.isoformat() if pub_date else None
            else:
                rec['date'] = pub_date.isoformat() if pub_date else None
            
            # Author: from "Posted by: Lucien Bréval"
            author_tag = soup_rel.find('font', {'size': '1'})  # same as date_info_tag
            if author_tag:
                author_text = author_tag.get_text(strip=True)
                # extract after "Posted by:"
                if 'Posted by:' in author_text:
                    # split
                    parts = author_text.split('Posted by:', 1)
                    if len(parts) > 1:
                        author_raw = parts[1].strip()
                        # remove trailing <br> etc
                        author_raw = author_raw.split('<')[0].strip()
                        # clean any extra tags? simple
                        # remove job titles? we just take names; assume no titles
                        # remove "By" etc not present
                        rec['author'] = author_raw
                    else:
                        rec['author'] = None
                else:
                    rec['author'] = None
            else:
                rec['author'] = None
            
            # Body: main text paragraphs between title and back link
            # Find body <font size="2"> after title? In sample, after <br><br> after date line
            # Locate <font size="2"> after date line? Simpler: get all <font size="2"> and <p> etc, exclude navigation
            # Remove header table and footer and back link
            # Get body <td> content
            body_td = soup_rel.find('td', {'width': '600', 'valign': 'top'})
            if body_td:
                # Get all text from body_td excluding the back link <p align="center">
                # Find all <font> and <p> inside body_td, concatenate paragraphs separated by blank line
                paragraphs = []
                for elem in body_td.find_all(['font', 'p']):
                    # get text, strip
                    txt = elem.get_text(separator=' ', strip=True)
                    if txt:
                        # avoid back link paragraph: if contains "&laquo; Back to news" skip
                        if '&laquo; Back to news' in txt:
                            continue
                        paragraphs.append(txt)
                # Join paragraphs with <br><br>? Need blank lines between paragraphs as in original
                # In sample, paragraphs separated by <br><br>
                # We'll join with '\n\n'
                body_text = '\n\n'.join(paragraphs)
                rec['body'] = body_text
            else:
                rec['body'] = ''
    
    # Return list of dicts with required keys (ensure date string YYYY-MM-DD)
    result = []
    for rec in items:  # items already sorted
        # rec dict already filled
        # ensure keys exist
        out = {
            'url': rec['url'],
            'title': rec['title'],
            'date': rec['date'],
            'author': rec['author'],
            'body': rec['body']
        }
        # If any missing, set defaults
        if out['date'] is None:
            # fallback to pub_date iso
            if pub_date:
                out['date'] = pub_date.isoformat()
            else:
                out['date'] = None
        if out['author'] is None:
            out['author'] = None
        result.append(out)
    
    return result
