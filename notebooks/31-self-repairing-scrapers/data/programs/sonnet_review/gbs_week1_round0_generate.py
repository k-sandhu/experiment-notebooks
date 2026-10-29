import json
import re
from urllib.parse import urljoin, urlparse, urlunparse, urlencode, parse_qsl

from bs4 import BeautifulSoup
from dateutil import parser as dateparser

MAX_LIST_PAGES = 100

_NOISE_RE = re.compile(
    r"share|social|newsletter|related|cookie|subscribe|(^|[_\-])tags?([_\-]|$)|"
    r"contact|about|boilerplate|breadcrumb|promo|banner",
    re.I,
)
_BLOCK_TAGS = ["p", "h2", "h3", "h4", "h5", "h6", "li", "blockquote", "pre"]


def _clean(text):
    return " ".join((text or "").replace("\xa0", " ").split())


def _norm_url(url):
    p = urlparse(url)
    path = p.path.rstrip("/") or "/"
    return urlunparse((p.scheme, p.netloc, path, "", p.query, ""))


def _next_data(soup):
    tag = soup.find("script", id="__NEXT_DATA__")
    if not tag:
        return None
    try:
        return json.loads(tag.string or tag.get_text())
    except Exception:
        return None


def _page_props(data):
    try:
        return data["props"]["pageProps"]
    except Exception:
        return {}


# --------------------------------------------------------------- listing

def _base_path(listing_url):
    return urlparse(listing_url).path.rstrip("/")


def _listing_links(soup, page_url, listing_url, props):
    base = _base_path(listing_url)
    host = urlparse(listing_url).netloc
    found = []

    root = soup.find("main") or soup.body or soup
    for a in root.find_all("a", href=True):
        full = urljoin(page_url, a["href"])
        p = urlparse(full)
        if p.netloc != host:
            continue
        path = p.path.rstrip("/")
        if not path.startswith(base + "/") or path == base:
            continue
        rest = path[len(base) + 1:]
        if not rest or re.match(r"^(page/\d+|p/\d+)$", rest):
            continue
        if "/" in rest and re.match(r"^(page|tag|category|topic|archive)/", rest):
            continue
        found.append(_norm_url(full))

    def walk(obj):
        if isinstance(obj, dict):
            slug = obj.get("slug")
            if isinstance(slug, str) and ("title" in obj or "publishedAt" in obj):
                yield slug
            for v in obj.values():
                yield from walk(v)
        elif isinstance(obj, list):
            for v in obj:
                yield from walk(v)

    for slug in walk(props):
        found.append(_norm_url(urljoin(listing_url.rstrip("/") + "/", slug.strip("/"))))
    return found


def _with_page(url, n):
    p = urlparse(url)
    q = [(k, v) for k, v in parse_qsl(p.query) if k != "page"]
    q.append(("page", str(n)))
    return urlunparse((p.scheme, p.netloc, p.path, p.params, urlencode(q), ""))


def _pagination_urls(soup, page_url, listing_url, props):
    host = urlparse(listing_url).netloc
    base = _base_path(listing_url)
    urls = []

    for tag in soup.find_all(["link", "a"], href=True):
        rel = tag.get("rel") or []
        if isinstance(rel, str):
            rel = rel.split()
        text = _clean(tag.get_text()).lower()
        label = (tag.get("aria-label") or "").lower()
        href = tag["href"]
        full = urljoin(page_url, href)
        p = urlparse(full)
        if p.netloc != host:
            continue
        is_page_href = bool(
            re.search(r"(^|[?&])(page|p|pg)=\d+", p.query)
            or re.search(r"/page/\d+/?$", p.path)
        )
        if "next" in rel or (
            tag.name == "a"
            and (re.match(r"^(next|older|more)\b", text) or "next" in label
                 or text in ("›", "»", ">", "→"))
        ):
            urls.append(full)
        elif tag.name == "a" and is_page_href and p.path.rstrip("/").startswith(base):
            urls.append(full)

    # JSON pagination hints
    def find_keys(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                yield k, v
                yield from find_keys(v)
        elif isinstance(obj, list):
            for v in obj:
                yield from find_keys(v)

    total = None
    for k, v in find_keys(props):
        kl = k.lower()
        if kl in ("nexturl", "nextlink", "next") and isinstance(v, str) and v:
            urls.append(urljoin(page_url, v))
        elif kl in ("nextpage",) and isinstance(v, int) and not isinstance(v, bool):
            urls.append(_with_page(listing_url, v))
        elif kl in ("totalpages", "pagecount", "numpages", "pages") and isinstance(v, int) \
                and not isinstance(v, bool):
            total = v
    if total and 1 < total <= MAX_LIST_PAGES:
        for i in range(2, total + 1):
            urls.append(_with_page(listing_url, i))
    return urls


def _collect_listing(fetch, listing_url):
    from_queue = [listing_url]
    seen_pages = set()
    links = []
    seen_links = set()
    first = True
    while from_queue and len(seen_pages) < MAX_LIST_PAGES:
        url = from_queue.pop(0)
        key = _norm_url(url)
        if key in seen_pages:
            continue
        seen_pages.add(key)
        try:
            html = fetch(url)
        except Exception:
            if first:
                raise
            continue
        first = False
        soup = BeautifulSoup(html, "html.parser")
        data = _next_data(soup)
        props = _page_props(data) if data else {}
        for link in _listing_links(soup, url, listing_url, props):
            if link not in seen_links:
                seen_links.add(link)
                links.append(link)
        for nxt in _pagination_urls(soup, url, listing_url, props):
            if _norm_url(nxt) not in seen_pages:
                from_queue.append(nxt)
    return links


# --------------------------------------------------------------- release

def _json_article(props):
    art = props.get("article") if isinstance(props, dict) else None
    return art if isinstance(art, dict) else {}


def _date_from_value(value):
    if not value or not isinstance(value, str):
        return None
    m = re.match(r"^\s*(\d{4})-(\d{2})-(\d{2})", value)
    if m:
        return "%s-%s-%s" % m.groups()
    try:
        return dateparser.parse(value, dayfirst=True).strftime("%Y-%m-%d")
    except Exception:
        return None


def _html_date(soup, art):
    for t in (art or soup).find_all("time"):
        d = _date_from_value(t.get("datetime") or t.get_text())
        if d:
            return d
    for key in ("article:published_time", "datePublished", "date", "pubdate"):
        m = soup.find("meta", attrs={"property": key}) or soup.find("meta", attrs={"name": key}) \
            or soup.find("meta", attrs={"itemprop": key})
        if m and m.get("content"):
            d = _date_from_value(m["content"])
            if d:
                return d
    meta = (art or soup).find(class_=re.compile(r"meta", re.I))
    if meta:
        for span in meta.find_all(["span", "time", "div", "p"]):
            txt = _clean(span.get_text())
            if re.search(r"\d{4}", txt) and not re.search(r"updated|reviewed", txt, re.I):
                d = _date_from_value(txt)
                if d:
                    return d
    return None


def _split_names(raw):
    raw = _clean(raw)
    raw = re.sub(r"^\s*(written\s+)?by\s*:?\s+", "", raw, flags=re.I)
    names = []
    for part in re.split(r"\s+and\s+|\s*&\s*|;|\s*\|\s*", raw):
        part = _clean(part)
        part = re.sub(r"^by\s+", "", part, flags=re.I)
        part = part.split(",")[0].strip()
        part = re.split(r"\s+[-–—]\s+", part)[0].strip()
        if part:
            names.append(part)
    return names


def _json_authors(art):
    a = art.get("author", art.get("authors"))
    names = []

    def add(x):
        if isinstance(x, str):
            names.extend(_split_names(x))
        elif isinstance(x, dict):
            n = x.get("name") or x.get("fullName")
            if isinstance(n, str):
                names.extend(_split_names(n))
        elif isinstance(x, list):
            for i in x:
                add(i)

    add(a)
    return names


def _html_authors(soup, art):
    scope = art or soup
    el = scope.find(class_=re.compile(r"author|byline", re.I))
    if el:
        txt = _clean(el.get_text(" "))
        if txt:
            return _split_names(txt)
    m = soup.find("meta", attrs={"name": "author"})
    if m and m.get("content"):
        return _split_names(m["content"])
    return []


def _json_body(art):
    body = art.get("body")
    if not isinstance(body, list):
        return None
    paras = []
    for block in body:
        if not isinstance(block, dict):
            continue
        if block.get("_type") not in (None, "block"):
            continue
        children = block.get("children") or []
        text = _clean("".join(c.get("text", "") for c in children if isinstance(c, dict)))
        if text:
            paras.append(text)
    return "\n\n".join(paras) if paras else None


def _is_noise(el, container):
    node = el
    while node is not None and node is not container:
        if getattr(node, "attrs", None) is not None:
            if node.name in ("aside", "nav", "form", "button", "footer", "script",
                             "style", "noscript", "figcaption"):
                return True
            cls = " ".join(node.get("class") or []) + " " + (node.get("id") or "")
            if _NOISE_RE.search(cls):
                return True
        node = node.parent
    return False


def _html_body(art):
    if art is None:
        return None
    container = art.find(class_=re.compile(r"richtext|rich-text|article-body|articlebody|"
                                           r"post-body|entry-content|content__body", re.I))
    if container is None:
        container = art
    paras = []
    for el in container.find_all(_BLOCK_TAGS):
        if el.find_parent(_BLOCK_TAGS) is not None and \
                container in el.find_parent(_BLOCK_TAGS).parents:
            # nested inside another selected block that is itself within container
            parent = el.find_parent(_BLOCK_TAGS)
            if parent is not container and not _is_noise(parent, container):
                continue
        if _is_noise(el, container):
            continue
        if container is art and el.find_parent(class_=re.compile(r"meta", re.I)):
            continue
        text = _clean(el.get_text(" ")) if False else _clean(el.get_text())
        if text:
            paras.append(text)
    return "\n\n".join(paras) if paras else None


def _parse_release(html, url):
    soup = BeautifulSoup(html, "html.parser")
    data = _next_data(soup)
    jart = _json_article(_page_props(data)) if data else {}
    art = soup.find("article") or soup.find("main")

    title = None
    h1 = (art or soup).find("h1") or soup.find("h1")
    if h1:
        title = _clean(h1.get_text())
    if not title and jart.get("title"):
        title = _clean(jart["title"])
    if not title:
        og = soup.find("meta", attrs={"property": "og:title"})
        if og and og.get("content"):
            title = _clean(og["content"])

    date = _date_from_value(jart.get("publishedAt") or jart.get("datePublished")
                            or jart.get("publishedDate")) or _html_date(soup, art)

    names = _json_authors(jart) if jart else []
    if not names and not jart.get("author"):
        names = _html_authors(soup, art)
    author = " and ".join(dict.fromkeys(names)) if names else None

    body = _html_body(art) or _json_body(jart)
    if not body:
        body = ""

    return {"url": url, "title": title, "date": date, "author": author, "body": body}


def extract(fetch, listing_url):
    links = _collect_listing(fetch, listing_url)
    records = []
    for url in links:
        try:
            html = fetch(url)
        except FetchError:
            continue
        rec = _parse_release(html, url)
        if rec["title"] and rec["date"]:
            records.append(rec)
    records.sort(key=lambda r: r["date"], reverse=True)
    return records
