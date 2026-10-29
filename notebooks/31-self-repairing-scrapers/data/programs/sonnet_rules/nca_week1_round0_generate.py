import json
import re
from urllib.parse import urljoin, urlparse, urldefrag, parse_qs

from bs4 import BeautifulSoup
from dateutil import parser as dateparser

MAX_PAGES = 200

_NOISE_RE = re.compile(
    r"share|social|newsletter|subscribe|related|tags?$|tag-|contact|about|cookie|"
    r"breadcrumb|analyst-box|promo|sidebar|byline|authors?$|dateline|disclaimer-nav",
    re.I,
)
_TITLES_RE = re.compile(
    r",.*$|\s+[-–|]\s+.*$|\((.*?)\)", re.S
)
_ABOUT_RE = re.compile(r"^\s*(about|über|acerca de)\s+(northstar|us)\b", re.I)


def _soup(html):
    try:
        return BeautifulSoup(html, "lxml")
    except Exception:
        return BeautifulSoup(html, "html.parser")


def _clean(text):
    return re.sub(r"\s+", " ", (text or "").replace("\xa0", " ")).strip()


def _norm_url(u):
    return urldefrag(u)[0]


def _parse_date(text):
    text = _clean(text)
    if not text:
        return None
    m = re.search(r"\d{4}-\d{2}-\d{2}", text)
    if m:
        return m.group(0)
    try:
        return dateparser.parse(text, fuzzy=True, default=dateparser.parse("2000-01-01")).strftime("%Y-%m-%d")
    except Exception:
        return None


def _release_links(soup, page_url, listing_path):
    out = []
    seen = set()

    def add(href):
        if not href:
            return
        u = _norm_url(urljoin(page_url, href))
        if u not in seen:
            seen.add(u)
            out.append(u)

    for a in soup.select("a.card-link[href]"):
        add(a["href"])
    if out:
        return out
    scope = soup.find("main") or soup
    base = listing_path.rstrip("/") + "/"
    for a in scope.find_all("a", href=True):
        u = urljoin(page_url, a["href"])
        p = urlparse(u)
        if p.path.startswith(base) and len(p.path) > len(base) and not p.query:
            add(u)
    return out


def _next_pages(soup, page_url, listing_path):
    found = []
    for el in soup.find_all(["a", "link"], href=True):
        rel = el.get("rel") or []
        if "next" in [r.lower() for r in rel]:
            found.append(el["href"])
    scope = soup.find("main") or soup
    for a in scope.find_all("a", href=True):
        txt = _clean(a.get_text()).lower()
        label = (a.get("aria-label") or "").lower()
        if txt in ("next", "next page", "next ›", "›", "»", "next »", "older") or "next" in label:
            found.append(a["href"])
        else:
            u = urlparse(urljoin(page_url, a["href"]))
            q = parse_qs(u.query)
            if u.path.rstrip("/") == listing_path.rstrip("/") and ("page" in q or "p" in q):
                found.append(a["href"])
    return [_norm_url(urljoin(page_url, h)) for h in found]


def _jsonld(soup):
    items = []
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
                items.append(d)
                if "@graph" in d:
                    stack.append(d["@graph"])
    return items


def _title(soup):
    h1 = soup.select_one("main h1.headline") or soup.select_one("h1.headline")
    if not h1:
        main = soup.find("main") or soup
        h1 = main.find("h1")
    if h1 and _clean(h1.get_text()):
        return _clean(h1.get_text())
    og = soup.find("meta", property="og:title")
    if og and og.get("content"):
        return _clean(og["content"])
    t = soup.find("title")
    if t:
        return _clean(re.sub(r"\s*\|[^|]*$", "", t.get_text()))
    return ""


def _date(soup):
    for d in _jsonld(soup):
        v = d.get("datePublished")
        if isinstance(v, str) and _parse_date(v):
            return _parse_date(v)
    for attrs in ({"property": "article:published_time"}, {"name": "article:published_time"},
                  {"itemprop": "datePublished"}, {"name": "date"}, {"name": "publish-date"},
                  {"property": "og:published_time"}):
        m = soup.find("meta", attrs=attrs)
        if m and m.get("content") and _parse_date(m["content"]):
            return _parse_date(m["content"])
    el = soup.find(attrs={"itemprop": "datePublished"})
    if el:
        d = _parse_date(el.get("datetime") or el.get("content") or el.get_text())
        if d:
            return d
    for el in soup.select(".dateline, .date, .publish-date, .published, .post-date"):
        txt = _clean(el.get_text())
        if re.search(r"updated|reviewed|modified", txt, re.I) and not re.search(r"published", txt, re.I):
            continue
        d = _parse_date(txt)
        if d:
            return d
    main = soup.find("main") or soup
    for t in main.find_all("time"):
        ctx = _clean(t.parent.get_text()) if t.parent else ""
        if re.search(r"updated|reviewed|modified", ctx, re.I):
            continue
        d = _parse_date(t.get("datetime") or t.get_text())
        if d:
            return d
    return None


def _split_names(text):
    text = _clean(text)
    text = re.sub(r"^\s*(written\s+)?by\s*:?\s*", "", text, flags=re.I)
    parts = re.split(r",|;|\s+and\s+|\s*&\s*", text)
    names = []
    for p in parts:
        p = _clean(p)
        if p and p not in names:
            names.append(p)
    return names


def _author(soup):
    scope = soup.find("main") or soup
    names = []
    for a in scope.select('[rel~="author"]'):
        n = _clean(a.get_text())
        if n and n not in names:
            names.append(n)
    if not names:
        for el in scope.select('[itemprop="author"], .authors, .author, .byline'):
            txt = _clean(el.get_text())
            if txt:
                for n in _split_names(txt):
                    if n not in names:
                        names.append(n)
                if names:
                    break
    if not names:
        for d in _jsonld(soup):
            a = d.get("author")
            for x in (a if isinstance(a, list) else [a]):
                n = x.get("name") if isinstance(x, dict) else x
                if isinstance(n, str) and _clean(n) and _clean(n) not in names:
                    names.append(_clean(n))
    names = [n for n in names if n.lower() not in ("northstar credit analytics", "staff", "admin")]
    return " and ".join(names) if names else None


def _body(soup):
    cont = (soup.select_one(".article-body") or soup.select_one('[itemprop="articleBody"]')
            or soup.select_one("article .body, article .content") or soup.find("article"))
    if cont is None:
        cont = soup.find("main") or soup
    for t in cont.find_all(["script", "style", "noscript", "form", "button", "nav", "aside"]):
        t.decompose()
    for el in list(cont.find_all(True)):
        if el.decomposed if hasattr(el, "decomposed") else False:
            continue
        cls = " ".join(el.get("class") or []) + " " + (el.get("id") or "")
        if cls.strip() and _NOISE_RE.search(cls) and el is not cont:
            el.decompose()
    for br in cont.find_all("br"):
        br.replace_with(" ")
    paras = []
    for el in cont.find_all(["p", "h2", "h3", "h4", "h5", "h6", "li"]):
        if el.find(["p", "li"]):
            continue
        txt = _clean(el.get_text())
        if not txt or _ABOUT_RE.match(txt):
            continue
        paras.append(txt)
    return "\n\n".join(paras)


def extract(fetch, listing_url):
    listing_path = urlparse(listing_url).path
    queue = [_norm_url(listing_url)]
    visited = set()
    urls = []
    seen_urls = set()
    while queue and len(visited) < MAX_PAGES:
        page = queue.pop(0)
        if page in visited:
            continue
        visited.add(page)
        try:
            html = fetch(page)
        except FetchError:
            if page == _norm_url(listing_url):
                raise
            continue
        soup = _soup(html)
        for u in _release_links(soup, page, listing_path):
            if u not in seen_urls and u not in visited:
                seen_urls.add(u)
                urls.append(u)
        for n in _next_pages(soup, page, listing_path):
            if n not in visited and n not in queue:
                queue.append(n)

    records = []
    for u in urls:
        try:
            html = fetch(u)
        except FetchError:
            continue
        soup = _soup(html)
        title = _title(soup)
        if not title:
            continue
        records.append({
            "url": u,
            "title": title,
            "date": _date(soup),
            "author": _author(soup),
            "body": _body(soup),
        })

    records.sort(key=lambda r: r["date"] or "", reverse=True)
    return records
