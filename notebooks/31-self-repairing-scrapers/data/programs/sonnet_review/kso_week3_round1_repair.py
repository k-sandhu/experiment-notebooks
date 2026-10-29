import json
import re
from urllib.parse import urljoin, urldefrag, urlparse

from bs4 import BeautifulSoup
from dateutil import parser as dateparser

_TITLE_WORDS = re.compile(
    r"\b(head|director|editor|chief|manager|analyst|statistician|officer|economist|"
    r"lead|senior|deputy|researcher|correspondent|adviser|advisor|principal|"
    r"professor|dr|team|office|department|division|press|communications)\b", re.I)
_STOP_HEAD = re.compile(
    r"^\s*(about|contact|media|related|further|share|tags?|downloads?|notes? to editors|"
    r"newsletter|more (news|releases)|subscribe|follow)\b", re.I)
_NOISE_CLASS = re.compile(
    r"share|social|related|newsletter|subscribe|cookie|consent|tags?$|tag-|breadcrumb|"
    r"contact|about|download|byline|pubdate|meta|print|pagination|sidebar|banner|"
    r"promo|signup|sign-up|footer|header|toolbar", re.I)
_BLOCKS = ["p", "h2", "h3", "h4", "h5", "h6", "li", "blockquote", "pre"]
_UPDATE_CTX = re.compile(r"updat|modif|revis|review|amend|correct", re.I)


def _clean(s):
    return re.sub(r"\s+", " ", (s or "").replace("\xa0", " ")).strip()


def _norm_url(base, href):
    return urldefrag(urljoin(base, href))[0]


def _soup(html):
    try:
        return BeautifulSoup(html, "lxml")
    except Exception:
        return BeautifulSoup(html, "html.parser")


# ---------------------------------------------------------------- listing

def _release_links(soup, page_url, listing_url):
    out = []
    links = soup.select(".news-item a[href], a.news-link[href]")
    if not links:
        base_path = urlparse(listing_url).path.rstrip("/") + "/"
        scope = soup.find("main") or soup
        links = []
        for a in scope.find_all("a", href=True):
            u = _norm_url(page_url, a["href"])
            p = urlparse(u)
            if (p.netloc == urlparse(listing_url).netloc and p.path.startswith(base_path)
                    and p.path.rstrip("/") != base_path.rstrip("/") and not p.query):
                links.append(a)
    for a in links:
        u = _norm_url(page_url, a["href"])
        if u != _norm_url(page_url, page_url):
            out.append((u, a))
    return out


def _listing_date(a):
    node = a.parent
    for _ in range(3):
        if node is None:
            break
        t = node.find("time")
        if t is not None:
            return _parse_date(t.get("datetime") or t.get_text())
        el = node.find(class_=re.compile(r"date", re.I))
        if el is not None:
            d = _parse_date(el.get("datetime") or el.get_text())
            if d:
                return d
        node = node.parent
    return None


def _pagination_links(soup, page_url, listing_url):
    found = []
    host = urlparse(listing_url).netloc
    for a in soup.find_all("a", href=True):
        rel = a.get("rel") or []
        cls = " ".join(a.get("class") or [])
        pp = a.find_parent(class_=re.compile("pagina|pager", re.I))
        parent_cls = " ".join(pp.get("class", []) or []) if pp is not None else ""
        text = _clean(a.get_text()).lower()
        u = _norm_url(page_url, a["href"])
        if urlparse(u).netloc != host:
            continue
        is_page = False
        if "next" in rel or re.search(r"next", cls, re.I):
            is_page = True
        elif parent_cls:
            is_page = True
        elif text in ("next", "next page", "older", "›", "»", "next »", "older releases"):
            is_page = True
        elif re.search(r"[?&](page|p|offset|start)=\d+", u) and urlparse(u).path == urlparse(listing_url).path:
            is_page = True
        if is_page:
            found.append(u)
    return found


# ---------------------------------------------------------------- dates

def _parse_date(value):
    value = _clean(value)
    if not value:
        return None
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", value)
    if m:
        return "%s-%s-%s" % m.groups()
    try:
        return dateparser.parse(value, dayfirst=True, fuzzy=True).strftime("%Y-%m-%d")
    except Exception:
        return None


def _jsonld(soup):
    items = []
    for s in soup.find_all("script", type=re.compile("ld\\+json", re.I)):
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


def _find_date(soup):
    for sel in ["time.pubdate", "time[itemprop=datePublished]", "[itemprop=datePublished]",
                "time.published", "time.date", "time.release-date"]:
        el = soup.select_one(sel)
        if el is not None:
            d = _parse_date(el.get("datetime") or el.get("content") or el.get_text())
            if d:
                return d
    for name in ["article:published_time", "datePublished", "date", "DC.date.issued",
                 "publication_date", "pubdate"]:
        el = soup.find("meta", attrs={"property": name}) or soup.find("meta", attrs={"name": name})
        if el is not None and el.get("content"):
            d = _parse_date(el["content"])
            if d:
                return d
    for item in _jsonld(soup):
        if item.get("datePublished"):
            d = _parse_date(str(item["datePublished"]))
            if d:
                return d
    art = soup.find("article") or soup.find("main") or soup
    for t in art.find_all("time"):
        ctx = " ".join(t.get("class") or []) + " " + _clean(t.parent.get_text())[:80]
        if _UPDATE_CTX.search(ctx):
            continue
        d = _parse_date(t.get("datetime") or t.get_text())
        if d:
            return d
    # elements whose class mentions a date / publication
    for el in art.find_all(class_=re.compile(r"date|publish|pubdate|released", re.I)):
        cls = " ".join(el.get("class") or [])
        if _UPDATE_CTX.search(cls):
            continue
        txt = _clean(el.get_text(" "))
        if _UPDATE_CTX.search(txt[:30]):
            continue
        if not re.search(r"\d", txt):
            continue
        d = _parse_date(el.get("datetime") or txt)
        if d:
            return d
    m = re.search(r"(?:published|released|date)[:\s]+(\d{1,2} \w+ \d{4})", art.get_text(" "), re.I)
    if m:
        return _parse_date(m.group(1))
    return None


# ---------------------------------------------------------------- title

def _find_title(soup):
    art = soup.find("article") or soup.find("main") or soup
    h = art.find("h1") or soup.find("h1")
    if h is not None and _clean(h.get_text()):
        return _clean(h.get_text())
    el = soup.find("meta", attrs={"property": "og:title"})
    if el is not None and el.get("content"):
        return _clean(el["content"])
    if soup.title is not None:
        t = _clean(soup.title.get_text())
        return re.split(r"\s+[|\u2013\u2014-]\s+(?=[^|]*$)", t)[0]
    return ""


# ---------------------------------------------------------------- author

def _split_names(text):
    text = _clean(text)
    text = re.sub(r"^(written\s+)?by[:\s]+", "", text, flags=re.I)
    text = re.sub(r"\s*[|\u2022\u00b7].*$", "", text)
    parts = re.split(r",|;|\s+and\s+|\s+&\s+|\s+with\s+", text)
    names = []
    for p in parts:
        p = _clean(p)
        if not p or _TITLE_WORDS.search(p):
            continue
        if not re.match(r"^[A-Z\u00C0-\u024F][\w.'\u2019\-]*(\s+[\w.'\u2019\-]+){0,4}$", p):
            continue
        if p not in names:
            names.append(p)
    return names


def _find_author(soup):
    art = soup.find("article") or soup.find("main") or soup
    cands = art.select("[rel=author], [itemprop=author], .byline, .author, .release-author, "
                       ".post-author")
    cands += [e for e in art.find_all(class_=re.compile(r"author|byline", re.I))
              if e not in cands and not re.search(r"role|title|job|position",
                                                  " ".join(e.get("class") or []), re.I)]
    for el in cands:
        names = _split_names(el.get_text(" "))
        if names:
            return " and ".join(names)
    for item in _jsonld(soup):
        a = item.get("author")
        if a:
            lst = a if isinstance(a, list) else [a]
            names = []
            for x in lst:
                n = x.get("name") if isinstance(x, dict) else x
                if n and not _TITLE_WORDS.search(str(n)):
                    names.append(_clean(str(n)))
            if names:
                return " and ".join(names)
    el = soup.find("meta", attrs={"name": "author"})
    if el is not None and el.get("content"):
        names = _split_names(el["content"])
        if names:
            return " and ".join(names)
    return None


# ---------------------------------------------------------------- body

def _find_body(soup, title):
    container = None
    for sel in [".release-body", "[itemprop=articleBody]", ".content__body", ".article-body",
                ".entry-content", ".post-content", ".news-body", ".content-body",
                "article", "main"]:
        container = soup.select_one(sel)
        if container is not None:
            break
    if container is None:
        container = soup.body or soup
    for t in container.find_all(["script", "style", "nav", "aside", "form", "button",
                                 "noscript", "header", "footer", "iframe", "svg"]):
        t.decompose()
    if container.name in ("article", "main"):
        for t in container.find_all(True, class_=_NOISE_CLASS):
            if t is not container and t.parent is not None:
                t.decompose()
        for t in container.find_all("time"):
            t.decompose()
    for h in container.find_all("h1"):
        h.decompose()
    paras = []
    for el in container.find_all(_BLOCKS):
        if el.find(_BLOCKS):
            continue
        txt = _clean(el.get_text(" "))
        txt = re.sub(r"\s+([,.;:!?])", r"\1", txt)
        if not txt:
            continue
        if el.name in ("h2", "h3", "h4", "h5", "h6") and _STOP_HEAD.match(txt):
            break
        if re.match(r"^(share( this)?|tags?:|related:|subscribe|sign up)\b", txt, re.I):
            continue
        if re.match(r"^about (the )?\w+( \w+){0,4}$", txt, re.I) and el.name != "p":
            break
        paras.append(txt)
    if not paras:
        txt = _clean(container.get_text(" "))
        return txt
    return "\n\n".join(paras)


# ---------------------------------------------------------------- main

def extract(fetch, listing_url):
    queue = [_norm_url(listing_url, listing_url)]
    seen_pages = set()
    entries = []
    seen_urls = set()
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
        for u, a in _release_links(soup, page, listing_url):
            if u in seen_urls:
                continue
            seen_urls.add(u)
            entries.append((u, _listing_date(a)))
        for p in _pagination_links(soup, page, listing_url):
            if p not in seen_pages and p not in queue:
                queue.append(p)

    records = []
    for u, ldate in entries:
        try:
            html = fetch(u)
        except FetchError:
            continue
        soup = _soup(html)
        date = _find_date(soup) or ldate
        title = _find_title(soup)
        author = _find_author(soup)
        body = _find_body(soup, title)
        records.append({"url": u, "title": title, "date": date,
                        "author": author, "body": body})

    order = {r["url"]: i for i, r in enumerate(records)}
    records.sort(key=lambda r: (r["date"] or "", -order[r["url"]]), reverse=True)
    return records
