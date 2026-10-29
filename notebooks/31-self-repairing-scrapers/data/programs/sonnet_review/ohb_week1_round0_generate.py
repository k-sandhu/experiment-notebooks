import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from dateutil import parser as dateparser

ITEM_RE = re.compile(r"news_item", re.I)
NEXT_TEXT_RE = re.compile(r"^\s*(next|older|older news|more news|more|next page|›|»|>|&gt;|\d+)\s*(›|»|>)?\s*$", re.I)
DATE_LABEL_RE = re.compile(r"^\s*(posted|published|publication date|date)(\s+on)?\s*:\s*(.+?)\s*$", re.I | re.S)
AUTHOR_LABEL_RE = re.compile(r"^\s*(posted by|written by|authors?|by)\s*:\s*(.+?)\s*$", re.I | re.S)
ORG_WORDS_RE = re.compile(r"\b(oakhill|group|team|office|department|press|communications|media|staff|editor)\b", re.I)
BOILERPLATE_RE = re.compile(
    r"^(about oakhill|about us|media contact|press contact|contact:|for more information|for further information|"
    r"share this|related (news|links)|tags?:|subscribe|sign up|newsletter|back to news|«\s*back)",
    re.I,
)


def _soup(html):
    return BeautifulSoup(html, "html.parser")


def _clean(text):
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def _parse_date(text):
    text = _clean(text)
    try:
        return dateparser.parse(text, fuzzy=True, default=dateparser.parse("2000-01-01")).strftime("%Y-%m-%d")
    except (ValueError, OverflowError, TypeError):
        return None


def _listing_items(soup, base_url):
    items = []
    for a in soup.find_all("a", href=True):
        if ITEM_RE.search(a["href"]):
            url = urljoin(base_url, a["href"].strip())
            title = _clean(a.get_text(" "))
            container = a.find_parent("tr") or a.parent
            ctext = _clean(container.get_text(" ")) if container else ""
            items.append((url, title, _parse_date(ctext.replace(title, "")) if ctext else None))
    return items


def _next_pages(soup, base_url, listing_url):
    found = []
    lp = urlparse(listing_url)
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(("#", "javascript:", "mailto:")) or ITEM_RE.search(href):
            continue
        rel = a.get("rel") or []
        text = _clean(a.get_text(" "))
        url = urljoin(base_url, href)
        p = urlparse(url)
        if p.netloc != lp.netloc:
            continue
        same_section = p.path == lp.path or p.path == urlparse(base_url).path
        if ("next" in [r.lower() for r in rel]) or (NEXT_TEXT_RE.match(text) and same_section and p.query):
            found.append(url)
        elif NEXT_TEXT_RE.match(text) and same_section and url != base_url:
            found.append(url)
    return found


def _extract_release(html, url, fallback_title, fallback_date):
    soup = _soup(html)
    for t in soup(["script", "style", "noscript"]):
        t.decompose()

    date = None
    author = None
    date_node = None
    author_node = None
    for s in soup.find_all(string=True):
        if date_node is None:
            m = DATE_LABEL_RE.match(s)
            if m:
                d = _parse_date(m.group(3))
                if d:
                    date, date_node = d, s
                    continue
        if author_node is None:
            m = AUTHOR_LABEL_RE.match(s)
            if m:
                author_node = s
                author = m.group(2)

    # content container
    anchor = date_node or author_node
    container = anchor.find_parent("td") if anchor else None
    if container is None:
        container = soup.find("body") or soup

    # title
    title = None
    for el in container.find_all(["h1", "h2", "font"]):
        if el.name == "font" and el.get("size") not in ("4", "5", "6"):
            continue
        txt = _clean(el.get_text(" "))
        if txt:
            title = txt
            title_el = el
            break
    if title is None:
        h = soup.find(["h1", "h2"])
        if h:
            title = _clean(h.get_text(" "))
            title_el = None
        else:
            title_el = None
            tt = soup.find("title")
            title = _clean(tt.get_text(" ")) if tt else fallback_title
            if " - " in title and fallback_title and title.endswith(fallback_title):
                title = fallback_title
    if title_el is not None and title_el.parent is not None:
        title_el.decompose()

    # author
    if author:
        author = _clean(author)
        parts = [p.strip() for p in re.split(r",|;|&|\band\b", author, flags=re.I) if p.strip()]
        names = []
        for p in parts:
            if ORG_WORDS_RE.search(p) or p.lower() in ("none", "n/a", "staff"):
                continue
            names.append(p)
        author = " and ".join(names) if names else None

    # strip metadata text nodes
    for node in (date_node, author_node):
        if node is not None:
            node.extract()
    if date is None:
        date = fallback_date

    # drop trailing navigation
    for a in container.find_all("a", href=True):
        if re.search(r"back to|«", a.get_text(), re.I):
            holder = a.find_parent("p") or a
            holder.decompose()

    for br in container.find_all("br"):
        br.replace_with("\n")
    for blk in container.find_all(["p", "div", "li", "h1", "h2", "h3", "h4", "ul", "ol", "table", "tr"]):
        blk.insert_before("\n\n")
        blk.insert_after("\n\n")

    text = container.get_text().replace("\xa0", " ")
    paras = []
    for line in re.split(r"\n+", text):
        line = _clean(line)
        if not line:
            continue
        if line == title:
            continue
        paras.append(line)

    # cut standard boilerplate and everything after it
    cleaned = []
    for p in paras:
        if BOILERPLATE_RE.match(p):
            break
        cleaned.append(p)
    body = "\n\n".join(cleaned)

    return {"url": url, "title": title, "date": date, "author": author, "body": body}


def extract(fetch, listing_url):
    items = []
    seen_pages = set()
    queue = [listing_url]
    while queue and len(seen_pages) < 50:
        page = queue.pop(0)
        if page in seen_pages:
            continue
        seen_pages.add(page)
        try:
            html = fetch(page)
        except FetchError:
            if page == listing_url:
                raise
            continue
        soup = _soup(html)
        items.extend(_listing_items(soup, page))
        for n in _next_pages(soup, page, listing_url):
            if n not in seen_pages and n not in queue:
                queue.append(n)

    records = []
    seen = set()
    for url, title, ldate in items:
        if url in seen:
            continue
        seen.add(url)
        try:
            html = fetch(url)
        except FetchError:
            continue
        rec = _extract_release(html, url, title, ldate)
        records.append(rec)

    order = {r["url"]: i for i, r in enumerate(records)}
    records.sort(key=lambda r: (r["date"] or "", -order[r["url"]]), reverse=True)
    return records
