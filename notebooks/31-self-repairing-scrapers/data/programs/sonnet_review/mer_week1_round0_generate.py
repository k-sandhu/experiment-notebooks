import json
import re
from urllib.parse import urljoin, urlparse, urlencode, parse_qsl, urlunparse

from bs4 import BeautifulSoup
from dateutil import parser as dateparser

RELEASE_RE = re.compile(
    r'(?:https?:)?(?://[A-Za-z0-9.\-:]+)?/press/\d{4}/\d{2}/\d{2}/[A-Za-z0-9\-_%.]+')
URL_DATE_RE = re.compile(r'/press/(\d{4})/(\d{2})/(\d{2})/')
STRING_RE = re.compile(r'''["'`]((?:https?:)?//[^"'`\s]+|/[^"'`\s]*)["'`]''')
NOISE_CLASS_RE = re.compile(
    r'share|social|related|newsletter|subscribe|cookie|consent|tags?$|tag-|'
    r'contact|about|disclaimer|breadcrumb|promo|banner|sidebar|print|pr-meta|byline',
    re.I)
MAX_PAGES = 40


def _norm(text):
    return re.sub(r'\s+', ' ', text or '').strip()


def _safe_fetch(fetch, url):
    try:
        return fetch(url)
    except FetchError:
        return None
    except Exception:
        return None


def _release_urls(text, base):
    text = text.replace('\\/', '/')
    out = []
    for m in RELEASE_RE.finditer(text):
        u = urljoin(base, m.group(0)).rstrip('.')
        u = u.split('#')[0]
        out.append(u)
    return out


def _with_param(url, key, value):
    p = urlparse(url)
    q = [(k, v) for k, v in parse_qsl(p.query) if k != key]
    q.append((key, str(value)))
    return urlunparse(p._replace(query=urlencode(q)))


def _next_links(text, base):
    nxt = []
    s = text.lstrip()
    if s[:1] in '{[':
        try:
            data = json.loads(s)
        except ValueError:
            data = None

        def walk(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    if k.lower() in ('next', 'next_url', 'nexturl', 'next_page_url', 'nextpage') \
                            and isinstance(v, str) and v:
                        nxt.append(urljoin(base, v))
                    else:
                        walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
        if data is not None:
            walk(data)
    else:
        soup = BeautifulSoup(text, 'html.parser')
        for a in soup.find_all(['a', 'link'], href=True):
            rel = a.get('rel') or []
            if isinstance(rel, str):
                rel = rel.split()
            label = _norm(a.get_text()).lower()
            if 'next' in [r.lower() for r in rel] or label in ('next', 'next page', 'next »', '»', 'older'):
                nxt.append(urljoin(base, a['href']))
    return nxt


def _crawl_source(fetch, start, found):
    """Fetch a source and follow its 'next' links; add release URLs to found."""
    seen = set()
    queue = [start]
    got_any = False
    while queue and len(seen) < MAX_PAGES:
        u = queue.pop(0)
        if u in seen:
            continue
        seen.add(u)
        text = _safe_fetch(fetch, u)
        if not text:
            continue
        urls = _release_urls(text, u)
        if urls:
            got_any = True
        for x in urls:
            if x not in found:
                found[x] = None
        queue.extend(_next_links(text, u))
    return got_any


def _candidate_endpoints(fetch, listing_url, html):
    soup = BeautifulSoup(html, 'html.parser')
    cands = []
    for l in soup.find_all('link', href=True):
        t = (l.get('type') or '').lower()
        if 'rss' in t or 'atom' in t or 'json' in t:
            cands.append(urljoin(listing_url, l['href']))
    for a in soup.find_all('a', href=True):
        h = a['href']
        if re.search(r'feed|rss|\.xml|\.json|/api/', h, re.I):
            cands.append(urljoin(listing_url, h))
    scripts = [urljoin(listing_url, s['src']) for s in soup.find_all('script', src=True)]
    host = urlparse(listing_url).netloc
    for s in scripts:
        if urlparse(s).netloc != host:
            continue
        js = _safe_fetch(fetch, s)
        if not js:
            continue
        for m in STRING_RE.finditer(js):
            v = m.group(1)
            if re.search(r'\.(css|png|jpe?g|svg|gif|woff2?|ico|js)(\?|$)', v, re.I):
                continue
            if re.search(r'api|\.json|feed|rss|\.xml|press|release|news', v, re.I):
                u = urljoin(listing_url, v)
                if urlparse(u).netloc == host:
                    cands.append(u)
    # inline script data
    for sc in soup.find_all('script'):
        if sc.string and not sc.get('src'):
            for m in STRING_RE.finditer(sc.string):
                v = m.group(1)
                if re.search(r'api|\.json|feed|press/', v, re.I):
                    cands.append(urljoin(listing_url, v))
    ordered = []
    for c in cands:
        if c not in ordered and c.rstrip('/') != listing_url.rstrip('/'):
            ordered.append(c)
    return ordered[:25]


def _discover(fetch, listing_url):
    found = {}
    html = _safe_fetch(fetch, listing_url) or ''
    _crawl_source(fetch, listing_url, found)
    for c in _candidate_endpoints(fetch, listing_url, html):
        if _crawl_source(fetch, c, found):
            # try page-number pagination for sources that look like APIs
            text = _safe_fetch(fetch, c) or ''
            if not text.lstrip()[:1] in '{[':
                continue
            for key in ('page', 'p'):
                added_total = 0
                for n in range(2, MAX_PAGES):
                    t = _safe_fetch(fetch, _with_param(c, key, n))
                    if not t:
                        break
                    new = [x for x in _release_urls(t, c) if x not in found]
                    if not new:
                        break
                    for x in new:
                        found[x] = None
                    added_total += len(new)
                if added_total:
                    break
    # also plain page-number pagination on the listing, if it is static
    return list(found)


def _parse_date(s):
    s = _norm(s)
    if not s:
        return None
    m = re.search(r'\d{4}-\d{2}-\d{2}', s)
    if m and re.match(r'^\d{4}-\d{2}-\d{2}', s):
        return m.group(0)
    try:
        return dateparser.parse(s, fuzzy=True, dayfirst=False).strftime('%Y-%m-%d')
    except (ValueError, OverflowError, TypeError):
        return None


def _jsonld(soup):
    for sc in soup.find_all('script', type=re.compile('ld\\+json', re.I)):
        try:
            data = json.loads(sc.string or '')
        except ValueError:
            continue
        stack = [data]
        while stack:
            o = stack.pop()
            if isinstance(o, list):
                stack.extend(o)
            elif isinstance(o, dict):
                if 'datePublished' in o or 'headline' in o:
                    return o
                stack.extend(o.values())
    return {}


def _find_date(soup, url):
    ld = _jsonld(soup)
    if ld.get('datePublished'):
        d = _parse_date(str(ld['datePublished']))
        if d:
            return d
    for attrs in ({'property': 'article:published_time'}, {'name': 'date'},
                  {'itemprop': 'datePublished'}, {'name': 'publish-date'},
                  {'name': 'DC.date.issued'}):
        m = soup.find('meta', attrs=attrs)
        if m and m.get('content'):
            d = _parse_date(m['content'])
            if d:
                return d
    art = soup.find('article') or soup
    for t in art.find_all('time'):
        ctx = _norm(t.parent.get_text(' ') if t.parent else '').lower()
        if re.search(r'updated|reviewed|modified', ctx) and not t.get('itemprop') == 'datePublished':
            continue
        d = _parse_date(t.get('datetime') or t.get_text())
        if d:
            return d
    meta = art.find(class_=re.compile(r'pr-meta|meta|dateline|date', re.I))
    if meta:
        for span in meta.find_all(['span', 'time', 'div', 'p']) or [meta]:
            txt = _norm(span.get_text(' '))
            if re.search(r'updated|reviewed|modified|effective', txt, re.I):
                continue
            if re.search(r'\d{4}', txt) and re.search(r'[A-Za-z]{3,}|\d[/.-]\d', txt):
                d = _parse_date(re.sub(r'^(published|date)[:\s]+', '', txt, flags=re.I))
                if d:
                    return d
    m = URL_DATE_RE.search(url)
    if m:
        return '%s-%s-%s' % m.groups()
    return None


def _clean_names(raw):
    raw = _norm(raw)
    raw = re.sub(r'^(written\s+by|authored\s+by|author(s)?|by|analyst(s)?)\s*[:\-]?\s+', '', raw,
                 flags=re.I)
    names = []
    for part in re.split(r'\s+and\s+|\s*&\s*|;|\s*\|\s*', raw):
        part = re.split(r',|\s[-–—]\s', part)[0]
        part = re.sub(r'^(by|and)\s+', '', _norm(part), flags=re.I)
        if part and not re.search(r'meridian|ratings|staff|press office', part, re.I):
            names.append(part)
    return names


def _find_author(soup):
    ld = _jsonld(soup)
    a = ld.get('author')
    if a:
        items = a if isinstance(a, list) else [a]
        names = []
        for it in items:
            n = it.get('name') if isinstance(it, dict) else it
            if isinstance(n, str):
                names.extend(_clean_names(n))
        if names:
            return ' and '.join(names)
    art = soup.find('article') or soup
    el = art.find(class_=re.compile(r'analyst|author|byline', re.I)) or \
        art.find(attrs={'rel': 'author'}) or art.find(attrs={'itemprop': 'author'})
    if el:
        nested = el.find_all(class_=re.compile(r'author-name|name', re.I)) if \
            el.find(class_=re.compile(r'author-name|name', re.I)) else []
        if nested:
            names = []
            for n in nested:
                names.extend(_clean_names(n.get_text(' ')))
        else:
            names = _clean_names(el.get_text(' '))
        if names:
            return ' and '.join(dict.fromkeys(names))
        return None
    m = soup.find('meta', attrs={'name': 'author'})
    if m and m.get('content'):
        names = _clean_names(m['content'])
        if names:
            return ' and '.join(names)
    return None


def _find_title(soup):
    art = soup.find('article') or soup.find('main') or soup
    h = art.find('h1') or soup.find('h1')
    if h:
        t = _norm(h.get_text(' '))
        if t:
            return t
    m = soup.find('meta', attrs={'property': 'og:title'})
    if m and m.get('content'):
        return _norm(m['content'])
    if soup.title:
        return _norm(re.sub(r'\s*[|\-–]\s*Meridian Ratings\s*$', '', soup.title.get_text()))
    return ''


BLOCKS = ('p', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote', 'pre')


def _find_body(soup):
    for t in soup(['script', 'style', 'noscript', 'nav', 'aside', 'form', 'button',
                   'iframe', 'header', 'footer']):
        t.decompose()
    container = None
    for sel in ('.pr-body', '[itemprop=articleBody]', '.article-body', '.release-body',
                '.press-body', '.entry-content', '.content-body'):
        container = soup.select_one(sel)
        if container:
            break
    if container is None:
        container = soup.find('article') or soup.find('main') or soup.body or soup
    for el in list(container.find_all(True)):
        if getattr(el, 'decomposed', False) or el.attrs is None:
            continue
        cls = ' '.join(el.get('class') or []) + ' ' + (el.get('id') or '')
        if el is not container and NOISE_CLASS_RE.search(cls):
            el.decompose()
    for br in container.find_all('br'):
        br.replace_with(' ')
    paras = []
    for el in container.find_all(BLOCKS):
        if any(p.name in BLOCKS for p in el.parents if p is not container
               and p in container.descendants):
            continue
        if el.name == 'h1':
            continue
        txt = _norm(el.get_text(''))
        if not txt:
            continue
        if re.match(r'^About\s+Meridian', txt, re.I):
            continue
        paras.append(txt)
    return '\n\n'.join(paras)


def _parse_release(html, url):
    soup = BeautifulSoup(html, 'html.parser')
    title = _find_title(soup)
    date = _find_date(soup, url)
    author = _find_author(soup)
    body = _find_body(soup)
    return {'url': url, 'title': title, 'date': date, 'author': author, 'body': body}


def extract(fetch, listing_url):
    urls = _discover(fetch, listing_url)
    records = []
    for u in urls:
        html = _safe_fetch(fetch, u)
        if not html:
            continue
        rec = _parse_release(html, u)
        if rec['title'] and rec['date']:
            records.append(rec)
    records.sort(key=lambda r: r['date'], reverse=True)
    return records
