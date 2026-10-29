import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser

try:
    from fetch import FetchError
except ImportError:
    class FetchError(Exception):
        def __init__(self, status):
            self.status = status

def extract(fetch, listing_url):
    try:
        listing_html = fetch(listing_url)
    except FetchError as e:
        raise e

    base_url = urllib.parse.urljoin(listing_url, '/')
    soup = BeautifulSoup(listing_html, 'html.parser')

    articles = soup.find_all('article', class_='nouvelle')
    records = []

    for article in articles:
        h2 = article.find('h2')
        if not h2:
            continue
        link_tag = h2.find('a', href=True)
        if not link_tag:
            continue
        rel_url = link_tag['href']
        abs_url = urllib.parse.urljoin(base_url, rel_url)

        # Fetch release page
        try:
            release_html = fetch(abs_url)
        except FetchError:
            continue

        release_soup = BeautifulSoup(release_html, 'html.parser')

        # Title from main h1
        h1 = release_soup.find('h1')
        if h1:
            title = h1.get_text(strip=True)
        else:
            # fallback to link text
            title = link_tag.get_text(strip=True)

        # Date from release page <p class="date">
        date_p_rel = release_soup.find('p', class_='date')
        date_str = None
        if date_p_rel:
            date_text_rel = date_p_rel.get_text(strip=True)
            try:
                date_match_rel = parser.parse(date_text_rel, fuzzy=True)
                date_str = date_match_rel.date().isoformat()
            except Exception:
                pass

        # Author from release page <p class="auteur">
        author_p_rel = release_soup.find('p', class_='auteur')
        author = None
        if author_p_rel:
            author_raw_rel = author_p_rel.get_text(strip=True)
            if author_raw_rel.startswith('Par '):
                author_text_rel = author_raw_rel[4:].strip()
            else:
                author_text_rel = author_raw_rel.strip()
            if author_text_rel:
                # Normalize: remove trailing punctuation
                author = author_text_rel.rstrip('.').rstrip(',')

        # Body from <div class="contenu">
        contenu = release_soup.find('div', class_='contenu')
        body = ''
        if contenu:
            paras = []
            for p in contenu.find_all('p'):
                paras.append(p.get_text(separator='\n', strip=True))
            # Keep only non-empty paragraphs
            body_lines = [p.strip() for p in paras if p.strip()]
            body = '\n\n'.join(body_lines)

        record = {
            'url': abs_url,
            'title': title,
            'date': date_str,
            'author': author,
            'body': body
        }
        records.append(record)

    # Sort newest first by date (descending). Dates are ISO strings or None.
    def get_date_key(rec):
        d = rec['date']
        if isinstance(d, str) and len(d) == 10 and d[4] == '-':
            try:
                return parser.parse(d, fuzzy=False).date()
            except Exception:
                return None
        return None

    records.sort(key=lambda r: get_date_key(r) or (0,0,0), reverse=True)

    return records
