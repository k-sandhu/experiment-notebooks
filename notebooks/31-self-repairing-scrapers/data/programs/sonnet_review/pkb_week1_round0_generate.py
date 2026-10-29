import json
import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from dateutil import parser as dateparser

NOISE_TOKENS = {
    "share", "sharing", "social", "newsletter", "subscribe", "signup", "related",
    "tags", "tag", "contact", "contacts", "about", "cookie", "cookies", "breadcrumb",
    "breadcrumbs", "meta", "byline", "nav", "navigation", "promo", "boilerplate",
    "print", "button", "pagination", "pager", "sidebar", "footer", "banner",
}
BLOCK_TAGS = ["p", "h2", "h3", "h4", "h5", "h6", "li", "blockquote", "pre"]
STRIP_TAGS = ["script", "style", "noscript", "button", "form", "nav", "aside",
              "footer", "header", "iframe", "svg", "template"]


def _ws(text):
    return re.sub(r"\s+", " ", text or "").strip()


def _soup(html):
    return BeautifulSoup(html, "html.parser")


def _tokens(el):
    vals = []
    for a in ("class", "id"):
        v = el.get(a)
        if not v:
            continue
        vals.extend(v if isinstance(v, list) else [v])
    toks = set()
    for v in vals:
        toks.update(t for t in re.split(r"[^a-z0-9]+", v.lower()) if t)
    return toks


def _get(fetch, url):
    try:
        return fetch(url)
    except FetchError:
        return None


# ---------------------------------------------------------------- listing

def _release_links(soup, page_url, listing_url):
    links = []
    teasers = soup.select("[class*=teaser] a[href], [class*=news-item] a[href], "
                          "[class*=news-list] a[href], article a[href]")
    if not teasers:
        base = urlparse(listing_url).path.rstrip("/")
        for a in soup.find_all("a", href=True):
            p = urlparse(urljoin(page_url, a["href"])).path
            if p.startswith(base + "/") and len(p.strip("/").split("/")) > len(base.strip("/").split("/")):
                teasers.append(a)
    for a in teasers:
        href = a.get("href", "")
        if href.startswith(("#", "mailto:", "javascript:")):
            continue
        url = urljoin(page_url, href).split("#")[0]
        if url not in links:
            links.append(url)
    return links


def _next_pages(soup, page_url):
    found = []
    for a in soup.find_all("a", href=True):
        rel = a.get("rel") or []
        text = _ws(a.get_text()).lower()
        if "next" in rel or text in ("next", "next »", "next ›", "»", "›", "older", "older news", "next page"):
            found.append(urljoin(page_url, a["href"]))
    for l in soup.find_all("link", rel=True, href=True):
        if "next" in (l.get("rel") or []):
            found.append(urljoin(page_url, l["href"]))
    return found


def _collect_listing(fetch, listing_url):
    seen_pages = set()
    queue = [listing_url]
    urls = []
    while queue and len(seen_pages) < 200:
        page = queue.pop(0)
        if page in seen_pages:
            continue
        seen_pages.add(page)
        html = _get(fetch, page)
        if html is None:
            continue
        soup = _soup(html)
        for u in _release_links(soup, page, listing_url):
            if u not in urls and u.rstrip("/") != listing_url.rstrip("/"):
                urls.append(u)
        for n in _next_pages(soup, page):
            if n not in seen_pages:
                queue.append(n)
    return urls


# ---------------------------------------------------------------- release

def _jsonld(soup):
    out = []
    for s in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(s.string or s.get_text())
        except Exception:
            continue
        stack = [data]
        while stack:
            d = stack.pop()
            if isinstance(d, list):
                stack.extend(d)
            elif isinstance(d, dict):
                out.append(d)
                stack.extend(v for v in d.values() if isinstance(v, (list, dict)))
    return out


def _parse_date(text):
    text = _ws(text)
    if not text:
        return None
    try:
        return dateparser.parse(text, dayfirst=True, fuzzy=True).strftime("%Y-%m-%d")
    except (ValueError, OverflowError, TypeError):
        return None


def _find_date(soup, root):
    for d in _jsonld(soup):
        v = d.get("datePublished")
        if isinstance(v, str) and _parse_date(v):
            return _parse_date(v)
    m = soup.find("meta", attrs={"property": "article:published_time"})
    if m and m.get("content") and _parse_date(m["content"]):
        return _parse_date(m["content"])
    skip = re.compile(r"updated|modified|reviewed|effective|closing|event", re.I)
    cands = root.select("[class*=date], time") if root else []
    for el in cands:
        ctx = " ".join(el.get("class", [])) + " " + (el.parent.get_text(" ") if False else "")
        prev = _ws(el.previous_sibling.get_text() if hasattr(el.previous_sibling, "get_text")
                   else (el.previous_sibling or ""))
        if skip.search(ctx) or skip.search(prev[-30:]):
            continue
        val = el.get("datetime") or el.get_text()
        d = _parse_date(val)
        if d:
            return d
    return None


def _clean_name(name):
    name = _ws(name)
    name = re.sub(r"^(written\s+)?by\s*:?\s+", "", name, flags=re.I)
    name = name.split(",")[0].split(" | ")[0].split(" - ")[0].split(" – ")[0]
    return _ws(name)


def _find_author(soup, root):
    names = []
    els = root.select("[class*=author], [rel=author], [itemprop=author]") if root else []
    for el in els:
        if el.find(attrs={"class": re.compile("author")}) and el.name not in ("a", "span"):
            pass
        t = _ws(el.get_text(" "))
        if t:
            for part in re.split(r"\s+and\s+|\s*&\s*|;|\s*/\s*", t):
                n = _clean_name(part)
                if n and n not in names:
                    names.append(n)
        if names:
            break
    if not names:
        for d in _jsonld(soup):
            a = d.get("author")
            for x in (a if isinstance(a, list) else [a]):
                n = x.get("name") if isinstance(x, dict) else x
                if isinstance(n, str) and _clean_name(n) and _clean_name(n) not in names:
                    names.append(_clean_name(n))
        m = soup.find("meta", attrs={"name": "author"})
        if not names and m and m.get("content"):
            names.append(_clean_name(m["content"]))
    names = [n for n in names if n]
    return " and ".join(names) if names else None


def _blocks(container):
    out = []
    for el in container.find_all(BLOCK_TAGS):
        if el.find(BLOCK_TAGS):
            continue
        for br in el.find_all("br"):
            br.replace_with(" ")
        t = _ws(el.get_text())
        if not t:
            continue
        if el.name in ("h2", "h3", "h4", "h5", "h6") and re.match(r"(about|contact|related|share|more from)\b", t, re.I):
            break
        out.append(t)
    if not out:
        for line in container.get_text("\n").split("\n"):
            line = _ws(line)
            if line:
                out.append(line)
    return out


def _parse_release(fetch, url):
    html = _get(fetch, url)
    if html is None:
        return None
    soup = _soup(html)
    root = soup.find("article") or soup.find("main") or soup.body or soup

    h1 = root.find("h1") or soup.find("h1")
    title = _ws(h1.get_text()) if h1 else None
    if not title:
        t = soup.find("title")
        title = _ws(t.get_text()).split(" | ")[0] if t else ""

    date = _find_date(soup, root)
    author = _find_author(soup, root)

    # Load lazily-injected fragments
    for el in root.find_all(attrs={"data-src": True}):
        frag = _get(fetch, urljoin(url, el["data-src"]))
        if frag is None:
            continue
        fs = _soup(frag)
        for b in el.find_all("button"):
            b.decompose()
        el.append(fs)

    for t in root.find_all(STRIP_TAGS):
        if t.name == "header" and t.find("h1"):
            continue
        t.decompose()
    for el in list(root.find_all(True)):
        if el.decomposed if hasattr(el, "decomposed") else False:
            continue
        if _tokens(el) & NOISE_TOKENS:
            el.decompose()
    if h1 and h1.parent is not None:
        h1.decompose()

    body = "\n\n".join(_blocks(root))
    return {"url": url, "title": title, "date": date, "author": author, "body": body}


def extract(fetch, listing_url):
    records = []
    for url in _collect_listing(fetch, listing_url):
        rec = _parse_release(fetch, url)
        if rec:
            records.append(rec)
    records.sort(key=lambda r: r["date"] or "", reverse=True)
    return records
