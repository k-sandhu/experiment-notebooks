import json
import re
from urllib.parse import urljoin, urlparse, urldefrag

from bs4 import BeautifulSoup
from dateutil import parser as dateparser

_BLOCKS = ["p", "h2", "h3", "h4", "h5", "h6", "li", "blockquote", "pre"]
_EXCLUDE_TOKENS = {
    "share", "sharing", "social", "newsletter", "subscribe", "subscription",
    "related", "tags", "tag", "contact", "cookie", "cookies", "breadcrumb",
    "breadcrumbs", "byline", "nav", "navigation", "about", "boilerplate",
    "print", "signup", "promo", "ir",
}
_UPDATED_RE = re.compile(r"updat|modif|revis|review|effective|closing|event", re.I)


def _ws(text):
    return re.sub(r"\s+", " ", text or "").strip()


def _soup(html):
    try:
        return BeautifulSoup(html, "lxml")
    except Exception:
        return BeautifulSoup(html, "html.parser")


def _tokens(el):
    vals = []
    cls = el.get("class") or []
    if isinstance(cls, str):
        cls = cls.split()
    vals.extend(cls)
    if el.get("id"):
        vals.append(el.get("id"))
    toks = set()
    for v in vals:
        for t in re.split(r"[-_\s]+", v.lower()):
            if t:
                toks.add(t)
    return toks


def _norm_url(url):
    url, _ = urldefrag(url)
    return url


# ---------------------------------------------------------------- listing

def _listing_links(soup, page_url, base_dir):
    found = []
    root = soup.find("main") or soup.body or soup
    anchors = root.find_all("a", href=True)
    for a in anchors:
        absu = _norm_url(urljoin(page_url, a["href"].strip()))
        p = urlparse(absu)
        if p.query:
            continue
        bp = urlparse(base_dir)
        if p.netloc != bp.netloc or not p.path.startswith(bp.path):
            continue
        rest = p.path[len(bp.path):].strip("/")
        if not rest:
            continue
        first = rest.split("/")[0]
        if first.lower() in ("page", "p", "feed", "rss") or first.isdigit():
            continue
        if absu not in found:
            found.append(absu)
    return found


def _next_pages(soup, page_url, listing_url):
    out = []
    for tag in soup.find_all(["a", "link"], href=True):
        rel = tag.get("rel") or []
        if isinstance(rel, str):
            rel = rel.split()
        text = _ws(tag.get_text()).lower()
        href = tag["href"].strip()
        is_next = "next" in [r.lower() for r in rel] or text in (
            "next", "next page", "older", "older news", "›", "»", "next »", "next ›", "more")
        absu = _norm_url(urljoin(page_url, href))
        p = urlparse(absu)
        lp = urlparse(listing_url)
        paged = bool(re.search(r"(^|[?&])(page|p|offset|start)=\d+", p.query)) or \
            bool(re.search(r"/page/\d+/?$", p.path))
        if p.netloc == lp.netloc and (is_next or (paged and tag.name == "a")):
            if absu not in out:
                out.append(absu)
    return out


# ---------------------------------------------------------------- release

def _title(soup):
    main = soup.find("main") or soup
    h1 = main.find("h1") or soup.find("h1")
    if h1:
        t = _ws(h1.get_text(" "))
        if t:
            return t
    og = soup.find("meta", attrs={"property": "og:title"})
    if og and og.get("content"):
        return _ws(og["content"])
    if soup.title:
        t = _ws(soup.title.get_text())
        return re.split(r"\s+[|\u2013\u2014-]\s+", t)[0]
    return ""


def _to_date(s):
    s = _ws(s)
    if not s:
        return None
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return "%s-%s-%s" % m.groups()
    try:
        return dateparser.parse(s, dayfirst=True).strftime("%Y-%m-%d")
    except Exception:
        return None


def _jsonld_items(soup):
    for sc in soup.find_all("script", attrs={"type": re.compile("ld\\+json", re.I)}):
        try:
            data = json.loads(sc.string or sc.get_text())
        except Exception:
            continue
        stack = [data]
        while stack:
            d = stack.pop()
            if isinstance(d, list):
                stack.extend(d)
            elif isinstance(d, dict):
                yield d
                stack.extend(v for v in d.values() if isinstance(v, (dict, list)))


def _date(soup):
    for d in _jsonld_items(soup):
        if d.get("datePublished"):
            r = _to_date(str(d["datePublished"]))
            if r:
                return r
    for attrs in ({"property": "article:published_time"},
                  {"itemprop": "datePublished"},
                  {"name": "date"}, {"name": "publish-date"},
                  {"name": "pubdate"}, {"property": "og:published_time"}):
        m = soup.find("meta", attrs=attrs)
        if m and m.get("content"):
            r = _to_date(m["content"])
            if r:
                return r
    main = soup.find("main") or soup
    cands = []
    for t in main.find_all("time"):
        ctx = _ws((t.parent.get_text(" ") if t.parent else "")[:200])
        own = _ws(t.get_text()) + " " + " ".join(t.get("class") or [])
        label = _ws(t.previous_sibling if isinstance(t.previous_sibling, str) else "")
        if _UPDATED_RE.search(own) or _UPDATED_RE.search(label):
            continue
        if re.search(r"(updated|modified|revised|reviewed)\s*:?\s*" + re.escape(_ws(t.get_text())), ctx, re.I):
            continue
        cands.append(t)
    pub = [t for t in cands if t.get("itemprop") == "datePublished"] or cands
    for t in pub:
        txt = _ws(t.get_text())
        r = _to_date(t.get("datetime", "")) if t.get("datetime") else None
        v = _to_date(txt) if re.search(r"\d{4}", txt) else None
        if v:
            return v
        if r:
            return r
    text = _ws(main.get_text(" "))
    m = re.search(r"(?:published|posted|released|date)\s*:?\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})", text, re.I)
    if m:
        return _to_date(m.group(1))
    return None


def _clean_names(raw):
    raw = _ws(raw)
    raw = re.sub(r"^(written\s+)?by\s*:?\s+", "", raw, flags=re.I)
    parts = re.split(r"\s*(?:,|;|&|\band\b|\+)\s*", raw)
    names = []
    title_words = re.compile(
        r"\b(ceo|cfo|coo|cto|chief|director|head|manager|president|officer|editor|"
        r"spokes\w*|analyst|correspondent|vp|vice|chair\w*|communications|relations|"
        r"reporter|journalist)\b", re.I)
    for p in parts:
        p = re.split(r"\s+[\u2013\u2014|]\s+|\s+-\s+", p)[0]
        p = _ws(p)
        if not p or title_words.search(p):
            continue
        if p not in names:
            names.append(p)
    return names


def _author(soup):
    main = soup.find("main") or soup
    raw = None
    for el in main.find_all(True):
        toks = _tokens(el)
        if (toks & {"byline", "author", "authors"}) or el.get("itemprop") == "author" \
                or "author" in (el.get("rel") or []):
            if el.find(True, attrs={"class": re.compile("byline|author", re.I)}):
                continue
            raw = el.get_text(" ")
            if _ws(raw):
                break
            raw = None
    if raw is None:
        for d in _jsonld_items(soup):
            a = d.get("author")
            if a:
                items = a if isinstance(a, list) else [a]
                ns = []
                for i in items:
                    if isinstance(i, dict) and i.get("name") and i.get("@type", "Person") == "Person":
                        ns.append(i["name"])
                    elif isinstance(i, str):
                        ns.append(i)
                if ns:
                    raw = " and ".join(ns)
                    break
    if raw is None:
        m = soup.find("meta", attrs={"name": "author"})
        if m and m.get("content"):
            raw = m["content"]
    if not raw:
        return None
    names = _clean_names(raw)
    return " and ".join(names) if names else None


def _container(soup):
    main = soup.find("main") or soup.body or soup
    for sel in (".news-body", "[itemprop=articleBody]", ".release-body", ".article-body",
                ".entry-content", ".post-content", ".news-content", "article .body",
                "article"):
        try:
            el = main.select_one(sel) or soup.select_one(sel)
        except Exception:
            el = None
        if el:
            return el
    return main


def _body(soup):
    cont = _container(soup)
    cont = _soup(str(cont)).find(True) if cont else cont
    for el in list(cont.find_all(["script", "style", "nav", "form", "aside", "button",
                                  "noscript", "iframe", "footer", "header"])):
        el.decompose()
    for el in list(cont.find_all(True)):
        if el.parent is None:
            continue
        if _tokens(el) & _EXCLUDE_TOKENS:
            el.decompose()
    for h in list(cont.find_all(["h1"])):
        h.decompose()
    paras = []
    for el in cont.find_all(_BLOCKS):
        if el.find(_BLOCKS):
            continue
        t = _ws(el.get_text(" "))
        t = re.sub(r"\s+([,.;:!?])", r"\1", t)
        if not t:
            continue
        if re.match(r"^about\s+\w", t, re.I) and (el.name.startswith("h") or len(t) < 40
                                                 or re.match(r"^about\s+(us|the company|bramble)", t, re.I)):
            break
        paras.append(t)
    if not paras:
        t = _ws(cont.get_text(" "))
        return t
    return "\n\n".join(paras)


def _parse_release(html, url):
    soup = _soup(html)
    return {
        "url": url,
        "title": _title(soup),
        "date": _date(soup),
        "author": _author(soup),
        "body": _body(soup),
    }


# ---------------------------------------------------------------- entry

def extract(fetch, listing_url):
    p = urlparse(listing_url)
    path = p.path if p.path.endswith("/") else p.path.rsplit("/", 1)[0] + "/"
    base_dir = "%s://%s%s" % (p.scheme, p.netloc, path)

    release_urls = []
    seen_pages = set()
    queue = [_norm_url(listing_url)]
    while queue and len(seen_pages) < 200:
        page = queue.pop(0)
        if page in seen_pages:
            continue
        seen_pages.add(page)
        try:
            html = fetch(page)
        except FetchError:
            if page == _norm_url(listing_url):
                raise
            continue
        soup = _soup(html)
        for u in _listing_links(soup, page, base_dir):
            if u not in release_urls:
                release_urls.append(u)
        for n in _next_pages(soup, page, listing_url):
            if n not in seen_pages and n not in queue:
                queue.append(n)

    records = []
    for u in release_urls:
        try:
            html = fetch(u)
        except FetchError:
            continue
        rec = _parse_release(html, u)
        if rec["title"] and rec["date"]:
            records.append(rec)

    order = {r["url"]: i for i, r in enumerate(records)}
    records.sort(key=lambda r: (r["date"], -order[r["url"]]), reverse=True)
    return records
