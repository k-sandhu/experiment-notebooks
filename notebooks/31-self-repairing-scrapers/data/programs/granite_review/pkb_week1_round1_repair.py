import urllib.parse
from datetime import datetime
from dateutil import parser
from bs4 import BeautifulSoup

class FetchError(Exception):
    def __init__(self, status):
        self.status = status
        super().__init__(f"FetchError: HTTP {status}")

def extract(fetch, listing_url):
    try:
        listing_html = fetch(listing_url)
    except FetchError as e:
        raise e

    soup = BeautifulSoup(listing_html, 'html.parser')
    teasers = soup.find_all('div', class_='news-teaser')
    records = []

    for teaser in teasers:
        link_tag = teaser.find('a', href=True)
        if not link_tag:
            continue
        rel_url = link_tag['href']
        abs_url = urllib.parse.urljoin(listing_url, rel_url)

        try:
            release_html = fetch(abs_url)
        except FetchError:
            continue

        release_soup = BeautifulSoup(release_html, 'html.parser')
        article = release_soup.find('article')
        if not article:
            continue

        # Title from <h1> inside article
        title_tag = article.find('h1')
        title = title_tag.get_text(strip=True) if title_tag else ''

        # Date from meta-date in teaser or article meta
        date_str = None
        meta_date_tag = teaser.find('span', class_='meta-date')
        if meta_date_tag:
            date_str = meta_date_tag.get_text(strip=True)
        else:
            meta_div = article.find('div', class_='meta')
            if meta_div:
                meta_date_tag = meta_div.find('span', class_='meta-date')
                if meta_date_tag:
                    date_str = meta_date_tag.get_text(strip=True)

        date = None
        if date_str:
            try:
                dt = parser.parse(date_str, fuzzy=True)
                date = dt.strftime('%Y-%m-%d')
            except Exception:
                pass

        # Author from meta-author in teaser or article meta
        author = None
        meta_author_tag = teaser.find('span', class_='meta-author')
        if meta_author_tag:
            raw_author = meta_author_tag.get_text(strip=True)
            # Simple cleaning: remove common "By" prefix and job titles? spec says without job titles and "By".
            # We'll just keep as is; if starts with "By ", remove "By ".
            if raw_author.lower().startswith('by '):
                raw_author = raw_author[3:].strip()
            author = raw_author
        else:
            meta_div = article.find('div', class_='meta')
            if meta_div:
                meta_author_tag = meta_div.find('span', class_='meta-author')
                if meta_author_tag:
                    raw_author = meta_author_tag.get_text(strip=True)
                    if raw_author.lower().startswith('by '):
                        raw_author = raw_author[3:].strip()
                    author = raw_author

        # Body: collect lead paragraph and fragment paragraphs
        body_parts = []

        # Lead paragraph
        lead_div = article.find('div', class_='body-lead')
        if lead_div:
            lead_p = lead_div.find('p')
            if lead_p:
                body_parts.append(lead_p.get_text(strip=False))

        # Fragment via data-src
        body_rest_div = article.find('div', class_='body-rest')
        fragment_url = None
        if body_rest_div and body_rest_div.get('data-src'):
            fragment_rel = body_rest_div.get('data-src')
            fragment_url = urllib.parse.urljoin(abs_url, fragment_rel)
            try:
                fragment_html = fetch(fragment_url)
                fragment_soup = BeautifulSoup(fragment_html, 'html.parser')
                for p in fragment_soup.find_all('p'):
                    txt = p.get_text(strip=False)
                    if txt.strip():
                        body_parts.append(txt)
            except FetchError:
                pass  # fragment not available, continue

        # Any other <p> inside article (excluding lead) as fallback
        for p in article.find_all('p', recursive=True):
            # Skip lead paragraph if already added (simple check by class)
            if lead_div and 'body-lead' in p.get('class', []):
                continue
            txt = p.get_text(strip=False)
            if txt.strip():
                body_parts.append(txt)

        # Join with blank line (\n\n) between paragraphs
        body = '\n\n'.join(part.strip() for part in body_parts if part.strip()) if body_parts else ''

        records.append({
            'url': abs_url,
            'title': title,
            'date': date,
            'author': author,
            'body': body
        })

    # Sort newest first by date
    def get_sort_key(rec):
        d = rec['date']
        if d and isinstance(d, str):
            try:
                return parser.parse(d, fuzzy=True)
            except Exception:
                return datetime.min
        return datetime.min

    records.sort(key=get_sort_key, reverse=True)
    return records
