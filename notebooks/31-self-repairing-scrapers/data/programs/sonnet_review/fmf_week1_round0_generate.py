import json
import re
from urllib.parse import urljoin, urlparse, urldefrag

from bs4 import BeautifulSoup
from dateutil import parser as dateparser

_JUNK_CLASS = re.compile(
    r"(share|social|related|newsletter|subscribe|cookie|consent|breadcrumb|tags?$|tag-|"
    r"contact|about-us|aboutus|boilerplate|member-cta|sidebar|promo|print|pagination|"
    r"comments|author-box|back-to)", re.I)
_STOP_HEADING = re.compile(r"^\s*(about\b|contact|media contact|related|share|more news|"
                           r"latest news|tags|subscribe|newsletter)", re.I)
_ISO_DATE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")


def _soup(html):
    return BeautifulSoup(html, "html.parser")


def _clean(text):
    return re.sub(r"\s+", " ", text or "").strip()


def _norm_url(u):
    return urldefrag(u)[0]


# ---------------------------------------------------------------- listing

def _is_next_link(a):
    rel = a.get("rel") or []
    if isinstance(rel, str):
        rel = rel.split()
    if "next" in [r.lower() for r in rel]:
        return True
    txt = _clean(a.get_text()).lower()
    label = (a.get("aria-label") or "").lower()
    return txt in ("next", "next page", "older", "older posts", "›", "»", "next »", "next ›") \
        or label in ("next", "next page")


def _page_links(soup, page_url, listing_url):
    """Links to further listing pages (next / numbered pagination)."""
    out = []
    base_path = urlparse(listing_url).path.rstrip("/")
    for a in soup.find_all(["a", "link"], href=True):
        href = _norm_url(urljoin(page_url, a["href"]))
        p = urlparse(href)
        if p.netloc != urlparse(listing_url).netloc:
            continue
        if a.name == "link":
            rel = a.get("rel") or []
            if "next" in rel:
                out.append(href)
            continue
        numbered = (
            (p.path.rstrip("/") == base_path and re.search(r"(^|&)(page|p|paged)=\d+", p.query))
            or re.fullmatch(re.escape(base_path) + r"/(page/)?\d+", p.path.rstrip("/"))
        )
        if _is_next_link(a) or numbered:
            out.append(href)
    return out


def _listing_items(soup, page_url, listing_url):
    items = []
    base_path = urlparse(listing_url).path.rstrip("/")
    netloc = urlparse(listing_url).netloc

    containers = soup.select('[itemtype*="NewsArticle"], .media-item')
    anchors = []
    for c in containers:
        a = c.find("a", attrs={"itemprop": "url"}, href=True) or c.find("a", href=True)
        if a:
            anchors.append(a)
    if not anchors:
        main = soup.find("main") or soup
        for a in main.find_all("a", href=True):
            p = urlparse(urljoin(page_url, a["href"]))
            path = p.path.rstrip("/")
            if p.netloc == netloc and path.startswith(base_path + "/") and path != base_path \
                    and not re.fullmatch(re.escape(base_path) + r"/(page/)?\d+", path) \
                    and not p.query:
                anchors.append(a)
    for a in anchors:
        href = _norm_url(urljoin(page_url, a["href"]))
        if href not in items:
            items.append(href)
    return items


# ---------------------------------------------------------------- release

def _to_iso(value):
    if not value:
        return None
    value = value.strip()
    m = _ISO_DATE.match(value)
    if m:
        return "%s-%s-%s" % m.groups()
    try:
        return dateparser.parse(value, dayfirst=True).strftime("%Y-%m-%d")
    except (ValueError, OverflowError, TypeError):
        return None


def _jsonld_objects(soup):
    for s in soup.find_all("script", type=re.compile("ld\\+json", re.I)):
        try:
            data = json.loads(s.string or s.get_text())
        except ValueError:
            continue
        stack = [data]
        while stack:
            d = stack.pop()
            if isinstance(d, list):
                stack.extend(d)
            elif isinstance(d, dict):
                if "@graph" in d:
                    stack.append(d["@graph"])
                yield d


def _find_date(soup, article):
    scope = article or soup
    for root in (scope, soup):
        m = root.find(attrs={"itemprop": "datePublished"})
        if m:
            d = _to_iso(m.get("content") or m.get("datetime") or m.get_text())
            if d:
                return d
    for d in _jsonld_objects(soup):
        if d.get("datePublished"):
            r = _to_iso(str(d["datePublished"]))
            if r:
                return r
    for key in ("article:published_time", "og:published_time", "datePublished",
                "date", "DC.date.issued", "publish-date"):
        m = soup.find("meta", attrs={"property": key}) or soup.find("meta", attrs={"name": key})
        if m and m.get("content"):
            r = _to_iso(m["content"])
            if r:
                return r
    for t in scope.find_all("time"):
        if t.get("itemprop") == "dateModified" or "modif" in " ".join(t.get("class", [])).lower():
            continue
        r = _to_iso(t.get("datetime") or t.get_text())
        if r:
            return r
    for el in scope.find_all(class_=re.compile(r"date|published|posted", re.I)):
        if re.search(r"updat|modif|review", " ".join(el.get("class", [])), re.I):
            continue
        r = _to_iso(el.get_text())
        if r:
            return r
    return None


def _find_title(soup, article):
    scope = article or soup
    h = scope.find("h1") or soup.find("h1")
    if h:
        t = _clean(h.get_text())
        if t:
            return t
    m = soup.find("meta", attrs={"property": "og:title"})
    if m and m.get("content"):
        return _clean(m["content"])
    if soup.title:
        return _clean(re.split(r"\s+[|–—-]\s+", soup.title.get_text())[0])
    return None


def _split_names(text):
    text = re.sub(r"^\s*(written\s+)?by\s*:?\s+", "", text, flags=re.I)
    parts = re.split(r"\s*(?:,|;|&|\band\b)\s*", text)
    names = []
    for p in parts:
        p = _clean(p)
        if p and p not in names:
            names.append(p)
    return names


def _find_author(soup, article):
    scope = article or soup
    names = []
    for el in scope.find_all(attrs={"itemprop": "author"}):
        n = el.find(attrs={"itemprop": "name"})
        txt = _clean(n.get_text()) if n else _clean(el.get("content") or el.get_text())
        for x in _split_names(txt):
            if x not in names:
                names.append(x)
    if not names:
        for d in _jsonld_objects(soup):
            a = d.get("author")
            if not a:
                continue
            for x in (a if isinstance(a, list) else [a]):
                n = x.get("name") if isinstance(x, dict) else x
                if n:
                    for y in _split_names(str(n)):
                        if y not in names:
                            names.append(y)
    if not names:
        m = soup.find("meta", attrs={"name": "author"})
        if m and m.get("content"):
            names = _split_names(m["content"])
    if not names:
        el = scope.find(class_=re.compile(r"byline|author", re.I))
        if el:
            txt = _clean(el.get_text())
            m = re.search(r"\bby\s+(.+)$", txt, re.I)
            if m:
                names = _split_names(m.group(1))
    names = [n for n in names if n.lower() not in ("admin", "staff", "editor")]
    return " and ".join(names) if names else None


_BLOCKS = ["p", "li", "h2", "h3", "h4", "h5", "h6", "blockquote", "pre"]


def _find_body(soup, article):
    container = None
    for sel in ('[itemprop="articleBody"]', ".article-body", ".entry-content",
                ".post-content", ".release-body", ".news-body", ".content-body"):
        container = (article or soup).select_one(sel) or soup.select_one(sel)
        if container:
            break
    if container is None:
        container = article or soup.find("main") or soup.body or soup

    for el in container.find_all(["script", "style", "nav", "aside", "form", "button",
                                  "noscript", "iframe", "header", "footer"]):
        el.decompose()
    for el in list(container.find_all(True)):
        if el.decomposed if hasattr(el, "decomposed") else False:
            continue
        cls = " ".join(el.get("class", [])) + " " + (el.get("id") or "")
        if el is not container and _JUNK_CLASS.search(cls):
            el.decompose()
    for br in container.find_all("br"):
        br.replace_with(" ")

    paras = []
    for el in container.find_all(_BLOCKS):
        if el.find(_BLOCKS):
            continue
        if el.name in ("h2", "h3", "h4", "h5", "h6") and _STOP_HEADING.match(el.get_text()):
            break
        text = _clean(el.get_text())
        if not text:
            continue
        if re.match(r"^about the\b.*(federation|association)", text, re.I) and len(paras) > 0 \
                and el.name == "p" and False:
            continue
        paras.append(text)
    return "\n\n".join(paras)


def _parse_release(html, url):
    soup = _soup(html)
    article = soup.find(attrs={"itemtype": re.compile("NewsArticle|Article", re.I)}) \
        or soup.find("article")
    return {
        "url": url,
        "title": _find_title(soup, article),
        "date": _find_date(soup, article),
        "author": _find_author(soup, article),
        "body": _find_body(soup, article),
    }


# ---------------------------------------------------------------- entry

def extract(fetch, listing_url):
    seen_pages = set()
    queue = [_norm_url(listing_url)]
    urls = []
    first = True
    while queue and len(seen_pages) < 200:
        page = queue.pop(0)
        if page in seen_pages:
            continue
        seen_pages.add(page)
        try:
            html = fetch(page)
        except FetchError:
            if first:
                raise
            continue
        first = False
        soup = _soup(html)
        for u in _listing_items(soup, page, listing_url):
            if u not in urls:
                urls.append(u)
        for n in _page_links(soup, page, listing_url):
            if n not in seen_pages and n not in queue:
                queue.append(n)

    records = []
    for u in urls:
        try:
            html = fetch(u)
        except FetchError:
            continue
        rec = _parse_release(html, u)
        if rec["title"] and rec["date"]:
            records.append(rec)

    records.sort(key=lambda r: r["date"], reverse=True)
    return records
