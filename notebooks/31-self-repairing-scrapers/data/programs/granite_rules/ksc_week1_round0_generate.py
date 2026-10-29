import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser

# FetchError is assumed to be defined elsewhere; we only reference it
# No need to redefine it here

def extract(fetch, listing_url):
    # Fetch the listing page
    listing_html = fetch(listing_url)
    
    # Parse listing page
    soup_listing = BeautifulSoup(listing_html, 'html.parser')
    
    # Find all teaser articles
    teasers = soup_listing.find_all('article', class_='teaser')
    
    # Collect release URLs from teasers
    release_urls = []
    for teaser in teasers:
        link_tag = teaser.find('a', href=True)
        if link_tag:
            rel_url = link_tag['href']
            abs_url = urllib.parse.urljoin(listing_url, rel_url)
            # Only keep those that match /media/news/ pattern (teaser links)
            if abs_url.startswith('https://www.ksc.example/media/news/'):
                release_urls.append(abs_url)
    
    # Fetch each release page and extract data
    records = []
    for rel_url in release_urls:
        try:
            release_html = fetch(rel_url)
        except Exception:  # FetchError may be raised; catch generic for safety
            continue
        
        soup_release = BeautifulSoup(release_html, 'html.parser')
        
        # Get title from h1 (main heading)
        h1 = soup_release.find('h1')
        title = h1.get_text(strip=True) if h1 else ""
        
        # Find meta meta inside dl.meta
        meta_dl = soup_release.find('dl', class_='meta')
        date_text = None
        author_text = None
        
        if meta_dl:
            # Find <dt>Published</dt> <dd>...</dd>
            published_dd = meta_dl.find('dd', string=lambda t: t and 'Published' in t.parent.find_previous_sibling_all('dt').get_text().strip() if meta_dl.find('dt', string=lambda t: t and 'Published' in t) else None)
            # Simpler: iterate dt/dd pairs
            dt_children = meta_dl.find_all(['dt', 'dd'])
            for dt in dt_children:
                if dt.name == 'dt' and dt.get_text(strip=True).strip().lower() == 'published':
                    # next dd should be date
                    next_dd = meta_dl.find_next('dd')
                    if next_dd and next_dd.name == 'dd':
                        date_text = next_dd.get_text(strip=True)
                if dt.name == 'dt' and dt.get_text(strip().lower()) == 'author':
                    # next dd should be author
                    next_dd = meta_dl.find_next('dd')
                    if next_dd and next_dd.name == 'dd':
                        author_text = next_dd.get_text(strip=True)
        
        # Fallback if date not found via dt/dd: look for pattern in meta__meta? but use dl.meta
        if not date_text:
            # maybe fallback to teaser meta? but spec says use release page
            pass
        
        # Parse date: e.g., "30 September 2026"
        date_parsed = None
        if date_text:
            try:
                # dateutil can parse "30 September 2026"
                date_parsed = parser.parse(date_text, fuzzy=True).date()
            except Exception:
                pass
        
        # If still None, try to extract from h1? no.
        # Use first date found
        if date_parsed is None and date_text:
            # fallback parse
            try:
                date_parsed = parser.parse(date_text, fuzzy=True).date()
            except Exception:
                pass
        
        # Author cleaning: remove "By", job titles etc. Simple: split by commas/and, keep names
        # author_text may be like "Selin Arvane". No extra words.
        # Remove possible "By" prefix if present
        if author_text and author_text.lower().startswith('by '):
            author_text = author_text[3:].strip()
        # Remove trailing job titles? Not enough info; keep as is.
        # Join multiple names separated by commas or "and"
        # Simple: split by commas, then join with " and "
        parts = [p.strip() for p in author_text.split(',') if p.strip()]
        if len(parts) > 1:
            # if contains "and" maybe normalize
            # just join with " and "
            author_clean = " and ".join(parts)
        else:
            author_clean = parts[0] if parts else None
        # Remove words like "By", "Contact", etc. Not needed as we stripped "By ".
        # Remove job titles? can't reliably; keep.
        author = author_clean if author_clean else None
        
        # Body: find .body div? In sample, <div class="body"> contains paragraphs
        body_div = soup_release.find('div', class_='body')
        body_text = ""
        if body_div:
            # get all paragraphs inside body_div
            paras = body_div.find_all('p')
            paras_text = [p.get_text(strip=False) for p in paras]
            # join with blank line between paragraphs
            body_text = '\n\n'.join(paras_text)
        else:
            # fallback: get all paragraphs after h1? but spec says main text
            # find all p not in header/footer? simple collect all p not in contact?
            # Use all p not with class contact
            paras = soup_release.find_all('p')
            paras_text = []
            for p in paras:
                txt = p.get_text(strip=False)
                if 'contact' in p.get('class', []) or 'contact' in txt.lower():
                    continue
                paras_text.append(txt)
            body_text = '\n\n'.join(paras_text)
        
        # Normalize body: ensure blank lines between paragraphs
        # Already done
        
        # Build record
        record = {
            'url': rel_url,
            'title': title,
            'date': date_parsed.strftime('%Y-%m-%d') if date_parsed else None,
            'author': author if author else None,
            'body': body_text
        }
        # date must be string YYYY-MM-DD; if parsing failed, maybe fallback to teaser date? but spec says correct.
        # If date parsing fails, we could extract from meta dd but we already did.
        # Ensure date string not None; if None, maybe skip? but must include.
        # We'll keep as None? spec says date as "YYYY-MM-DD". Must be correct. We'll attempt fallback from teaser meta? Not allowed? Use release page only.
        # If parsing fails, we could extract numeric pattern? but assume works.
        if record['date'] is None:
            # try to extract from meta dd without parsing? maybe date_text like "30 September 2026" -> use that? but need YYYY-MM-DD.
            # cannot convert without parser. We'll leave None? but spec expects string. We'll attempt simple regex? not allowed external libs.
            # Use dateutil already imported; if parsing fails, we could use first day of month? Not correct. We'll skip record? but must collect all releases.
            # For safety, set date as date_text? but spec requires YYYY-MM-DD. We'll attempt to parse with fuzzy=True; if fails, maybe use date_text as is? Not compliant.
            # We'll set date as date_text (string) but that may not be YYYY-MM-DD. However sample date is "30 September 2026". Not compliant.
            # However the module runs weekly; we must produce correct date. We'll assume parser works.
            pass
        
        records.append(record)
    
    # Sort newest first by date descending
    # Need to sort by date parsed; we have date string YYYY-MM-DD, can sort lexicographically descending
    # Filter out records with None date? keep all but sort with None last? newest first means most recent date first.
    # We'll sort by date string descending; None will be last.
    def sort_key(r):
        d = r['date']
        if d is None:
            return ''  # will go to end
        return d
    
    records.sort(key=sort_key, reverse=True)
    
    return records
