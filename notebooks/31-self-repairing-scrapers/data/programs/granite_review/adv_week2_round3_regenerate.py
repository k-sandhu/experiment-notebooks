import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser

# FetchError is assumed to be defined elsewhere; we import it if available
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
        # Extract relative link from <a> inside <h2>
        h2 = article.find('h2')
        if not h2:
            continue
        link_tag = h2.find('a', href=True)
        if not link_tag:
            continue
        rel_url = link_tag['href']
        abs_url = urllib.parse.urljoin(base_url, rel_url)

        # Get title from link text (full headline)
        title_tag = link_tag
        title = title_tag.get_text(strip=True)

        # Extract date from <p class="date">
        date_p = article.find('p', class_='date')
        date_text = date_p.get_text(strip=True) if date_p else ''
        # Parse "Publié le 8 octobre 2026" -> "2026-10-08"
        try:
            date_match = parser.parse(date_text, fuzzy=True)
            # dateutil returns a datetime; we format as YYYY-MM-DD
            date_str = date_match.date().isoformat()
        except Exception:
            # fallback: try simple extraction
            import re
            m = re.search(r'(\d{1,2})\s+(\w+)\s+(\d{4})', date_text)
            if m:
                day = m.group(1)
                month_name = m.group(2)
                year = m.group(3)
                # map month name to number (simple dict for French months)
                month_map = {
                    'janvier': '01', 'février': '02', 'mars': '03', 'avril': '04',
                    'mai': '05', 'juin': '06', 'juillet': '07', 'août': '08',
                    'septembre': '09', 'octobre': '10', 'novembre': '11', 'décembre': '12'
                }
                month = month_map.get(month_name.lower().replace('.', ''), '01')
                # handle "1er" case like "1er septembre"
                if day.startswith('1') and day.endswith('er'):
                    day = day[:2]  # "01"
                date_str = f"{year}-{month:02d}-{day:02d}"
            else:
                date_str = None

        # Extract author from <p class="auteur">
        author_p = article.find('p', class_='auteur')
        author_raw = author_p.get_text(strip=True) if author_p else ''
        # Clean: remove "Par " prefix and any job titles? Keep names only.
        # Simple: take text after "Par " if present
        if author_raw.startswith('Par '):
            author_text = author_raw[4:].strip()
        else:
            author_text = author_raw.strip()
        # Remove possible trailing commas, etc. Keep names like "Bastien Corvelin"
        # Join multiple names with " and " if needed (unlikely). We'll just use cleaned text.
        # Remove common words like "et al."? Not needed.
        # If empty, set None
        if not author_text:
            author = None
        else:
            # Very simple: split by commas or "et" and clean
            parts = [p.strip() for p in author_text.split('et')]
            # further split by commas? Not needed for single name.
            # Keep as is.
            author = author_text

        # Fetch release page
        try:
            release_html = fetch(abs_url)
        except FetchError as e:
            # skip if cannot fetch
            continue

        release_soup = BeautifulSoup(release_html, 'html.parser')

        # Title from main h1 (full headline)
        h1 = release_soup.find('h1')
        if h1:
            title = h1.get_text(strip=True)
        else:
            # fallback to link title already extracted
            pass

        # Date from release page <p class="date"> (same format)
        date_p_rel = release_soup.find('p', class_='date')
        if date_p_rel and date_p_rel != date_p:
            date_text_rel = date_p_rel.get_text(strip=True)
            try:
                date_match_rel = parser.parse(date_text_rel, fuzzy=True)
                date_str = date_match_rel.date().isoformat()
            except Exception:
                pass

        # Author from release page <p class="auteur">
        author_p_rel = release_soup.find('p', class_='auteur')
        if author_p_rel:
            author_raw_rel = author_p_rel.get_text(strip=True)
            if author_raw_rel.startswith('Par '):
                author_text_rel = author_raw_rel[4:].strip()
            else:
                author_text_rel = author_raw_rel.strip()
            if not author_text_rel:
                author = None
            else:
                author = author_text_rel
        else:
            # keep earlier author if exists
            pass

        # Body from <div class="contenu">
        contenu = release_soup.find('div', class_='contenu')
        if contenu:
            # Get paragraphs inside, join with blank line
            paras = []
            for p in contenu.find_all('p'):
                paras.append(p.get_text(separator='\n', strip=True))
            # Join with double newline (blank line)
            body_lines = [p.strip() for p in paras if p.strip()]
            body = '\n\n'.join(body_lines)
        else:
            # fallback: get all text inside main excluding header/footer? Not needed.
            body = ''

        # Build record
        record = {
            'url': abs_url,
            'title': title,
            'date': date_str if date_str else None,
            'author': author if author else None,
            'body': body
        }
        # Ensure date is string YYYY-MM-DD; if None, maybe skip? but should exist.
        if record['date'] is None:
            # try parse from listing date again
            if date_str is None and date_p:
                # use listing date
                try:
                    date_match = parser.parse(date_text, fuzzy=True)
                    record['date'] = date_match.date().isoformat()
                except:
                    pass
        records.append(record)

    # Sort newest first by date (descending). Dates are strings ISO, comparable lexicographically.
    # Filter out records with missing date? Keep all with date.
    def get_date_key(rec):
        d = rec['date']
        if d and isinstance(d, str) and len(d) == 10 and d[4] == '-':
            return d
        return ''  # oldest

    records.sort(key=lambda r: get_date_key(r), reverse=True)

    return records
