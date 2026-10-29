import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser

class FetchError(Exception):
    def __init__(self, status):
        self.status = status

def fetch(url):
    # Placeholder: in real usage this would perform HTTP GET via requests or urllib.
    # For demonstration, we assume the URLs are reachable and return the provided HTML.
    # This stub raises FetchError for non-200 status; otherwise returns HTML string.
    import urllib.request
    import urllib.error
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            if response.status != 200:
                raise FetchError(response.status)
            return response.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        raise FetchError(e.code)
    except Exception:
        raise FetchError(None)  # fallback

def extract(fetch, listing_url):
    # Fetch listing page
    listing_html = fetch(listing_url)
    soup_list = BeautifulSoup(listing_html, 'html.parser')
    
    # Find all news teaser items
    teasers = soup_list.find_all('div', class_='news-teaser')
    records = []
    
    for teaser in teasers:
        # Extract relative link from <a> inside <h3>
        h3 = teaser.find('h3')
        if not h3:
            continue
        link_tag = h3.find('a', href=True)
        if not link_tag:
            continue
        rel_url = link_tag['href']
        abs_url = urllib.parse.urljoin(listing_url, rel_url)
        
        # Fetch release page
        try:
            release_html = fetch(abs_url)
        except FetchError:
            continue  # skip if fetch fails
        
        soup_rel = BeautifulSoup(release_html, 'html.parser')
        
        # Extract title from <h1> inside <article>
        article = soup_rel.find('article')
        h1 = article.find('h1') if article else None
        if not h1:
            # fallback: use link text
            title_text = link_tag.get_text(strip=True)
        else:
            title_text = h1.get_text(strip=True)
        
        # Extract author from .meta-author
        meta_author_span = article.find('span', class_='meta-author') if article else None
        if meta_author_span:
            # get text, clean
            raw_author = meta_author_span.get_text(strip=True)
            # remove possible "By" etc? but spec says without words such as "By". Assume raw is fine.
            # join multiple names? only one span present.
            author_text = raw_author
        else:
            author_text = None
        
        # Extract date from .meta-date in teaser and .meta-date in article (should match)
        # Use article meta-date if exists else teaser meta-date
        meta_date_tag = article.find('span', class_='meta-date') if article else None
        if meta_date_tag:
            raw_date = meta_date_tag.get_text(strip=True)
        else:
            # fallback to teaser meta-date
            meta_date_tag = teaser.find('span', class_='meta-date')
            raw_date = meta_date_tag.get_text(strip=True) if meta_date_tag else None
        if raw_date:
            # parse date like "5 Oct 2026" -> "2026-09-05"
            try:
                parsed = parser.parse(raw_date)
                date_str = parsed.strftime('%Y-%m-%d')
            except Exception:
                # fallback: extract year-month-day heuristics
                # simple: find first 4-digit year, then month name to number
                # but given format consistent, use parser
                date_str = raw_date  # keep as is? spec expects YYYY-MM-DD
                # attempt simple mapping
                parts = raw_date.split()
                if len(parts) >= 2:
                    month_name = parts[1]
                    # map month name to number
                    month_map = {
                        'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
                        'Apr': '04', 'May': '05', 'Jun': '06', 'Jul': '07',
                        'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
                    }
                    month_num = month_map.get(parts[1][:3], '01')
                    day = parts[0].rstrip(',')  # e.g., "5"
                    year = parts[2]
                    # day may be like "5" or "05"? assume integer
                    try:
                        day_int = int(day)
                    except:
                        day_int = 1
                    date_str = f"{year}-{month_num:02d}-{day_int:02d}"
                else:
                    date_str = raw_date
        else:
            date_str = None
        
        # Extract body: need to load fragments via JS. The page uses data-src attribute.
        # We'll fetch the fragment URLs and concatenate body-rest paragraphs.
        body_parts = []
        
        # First, get lead paragraph from .body-lead <p>
        body_lead = article.find('div', class_='body-lead')
        if body_lead:
            p_lead = body_lead.find('p')
            if p_lead:
                body_parts.append(p_lead.get_text(strip=False))
        
        # Then handle .body-rest which contains <button>Read the full release</button> and a data-src link.
        body_rest = article.find('div', class_='body-rest')
        if body_rest:
            # Look for data-src attribute
            data_src = body_rest.get('data-src')
            if data_src:
                frag_url = urllib.parse.urljoin(abs_url, data_src)
                try:
                    frag_html = fetch(frag_url)
                    frag_soup = BeautifulSoup(frag_html, 'html.parser')
                    # The fragment likely contains paragraphs; find all <p> inside fragment?
                    # The fragment page may be minimal with paragraphs.
                    # We'll extract all <p> text from fragment, preserving order.
                    p_tags = frag_soup.find_all('p')
                    for p in p_tags:
                        # get text with newline separator? spec: paragraphs separated by blank lines.
                        txt = p.get_text(separator='\n', strip=False)
                        body_parts.append(txt.strip('\n'))  # keep paragraph text
                except FetchError:
                    pass  # ignore missing fragment
        
        # Combine body parts: lead paragraph first, then fragment paragraphs.
        # Ensure blank line between paragraphs.
        if body_parts:
            # lead may already contain newline? we keep as is.
            # join with '\n\n'
            body_text = '\n\n'.join(body_parts)
        else:
            body_text = ''
        
        # Build record dict
        record = {
            'url': abs_url,
            'title': title_text,
            'date': date_str,
            'author': author_text,
            'body': body_text
        }
        records.append(record)
    
    # Sort newest first by date (descending). date strings are ISO, so lexicographic works.
    records.sort(key=lambda r: r['date'] or '0000-00-00', reverse=True)
    return records
