import json
import re
from urllib.parse import urljoin, urlparse, urldefrag

from bs4 import BeautifulSoup
from dateutil import parser as dtparser

NOISE_RE = re.compile(
    r"(share|social|newsletter|subscribe|related|tags?|topics|contact|cookie|consent|"
    r"breadcrumb|about|boilerplate|sidebar|nav|byline|author|dateline|press-date|"
    r"meta|print|download|promo|banner|more-stories|pagination)",
    re.I,
)
BLOCKS = ["p", "h2", "h3", "h4", "h5", "h6", "li", "blockquote", "pre"]
NON_PERSON_RE = re.compile(
    r"(press office|communications|newsroom|media relations|corporate|team|"
    r"lumen home retail|staff|editor(ial)?$|admin)", re.I)
TITLE_WORD_RE = re.compile(
    r"\b(director|manager|head of|officer|editor|chief|president|vice|correspondent|"
    r"reporter|senior|lead|analyst|spokes\w*|writer|journalist|ceo|cfo|coo)\b", re.I)
BY_PREFIX_RE = re.compile(
    r"^\s*(?:(?:written|words|story|text|reported|posted|article|report|photos?)\s+)?"
    r"by\b\s*[:\-]?\s*", re.I)


def _soup(html):
    try:
        return BeautifulSoup(html, "lxml")
    except Exception:
        return BeautifulSoup(html, "html.parser")


def _clean(text):
    return re.sub(r"\s+", " ", (text or "").replace("\xa0", " ")).strip()


def _norm_path(u):
    return urlparse(u).path.rstrip("/")


def _is_page_link(url):
    p = urlparse(url)
    return bool(re.search(r"(^|[?&])(page|p|paged|offset|start)=\d+", p.query)
                or re.search(r"/(page|p)/\d+/?$", p.path))


def _listing_links(soup, page_url, listing_url):
    base_path = _norm_path(listing_url)
    root = soup.find("main") or soup.body or soup
    releases, pages = [], []
    for a in root.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(("#", "mailto:", "javascript:", "tel:")):
            continue
        url = urldefrag(urljoin(page_url, href))[0]
        if urlparse(url).netloc != urlparse(listing_url).netloc:
            continue
        rel = a.get("rel") or []
        text = _clean(a.get_text()).lower()
        cls = " ".join(a.get("class") or []).lower()
        is_next = ("next" in rel or "next" in cls or
                   re.match(r"^(next|older|more|load more|show more|›|»|>|→)", text))
        path = _norm_path(url)
        if is_next or _is_page_link(url):
            if _norm_path(url) == base_path or path.startswith(base_path):
                pages.append(url)
            continue
        if path.startswith(base_path + "/") and path != base_path:
            releases.append(url)
    return releases, pages


def _jsonld(soup):
    out = []
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
                out.append(d)
                if "@graph" in d:
                    stack.append(d["@graph"])
    return out


def _meta(soup, **attrs):
    tag = soup.find("meta", attrs=attrs)
    if tag and tag.get("content"):
        return tag["content"].strip()
    return None


def _to_date(value):
    if not value:
        return None
    value = value.strip()
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", value)
    if m:
        return "%s-%s-%s" % m.groups()
    try:
        return dtparser.parse(value, fuzzy=True).date().isoformat()
    except Exception:
        return None


def _find_container(soup):
    for sel in ["div.press-content", "[itemprop=articleBody]", ".article-body",
                ".release-body", ".entry-content", ".post-content", ".article-content"]:
        c = soup.select_one(sel)
        if c:
            return c
    art = soup.find("article")
    if art:
        return art
    return soup.find("main") or soup.body or soup


def _get_title(soup):
    h1 = None
    scope = soup.select_one(".press-article") or soup.find("article") or soup.find("main") or soup
    h1 = scope.find("h1") or soup.find("h1")
    if h1 and _clean(h1.get_text()):
        return _clean(h1.get_text())
    og = _meta(soup, property="og:title")
    if og:
        return _clean(og)
    for d in _jsonld(soup):
        if d.get("headline"):
            return _clean(str(d["headline"]))
    t = soup.find("title")
    if t:
        return _clean(re.split(r"\s+[|\u2013\u2014-]\s+(?=[^|]*$)", t.get_text())[0])
    return ""


def _get_date(soup):
    for kw in [dict(property="article:published_time"), dict(itemprop="datePublished"),
               dict(name="date"), dict(name="publish-date"), dict(name="pubdate"),
               dict(property="og:published_time"), dict(name="DC.date.issued")]:
        d = _to_date(_meta(soup, **kw))
        if d:
            return d
    for d in _jsonld(soup):
        v = d.get("datePublished")
        if v:
            r = _to_date(str(v))
            if r:
                return r
    for t in soup.find_all("time"):
        if t.get("itemprop") == "dateModified":
            continue
        r = _to_date(t.get("datetime") or t.get_text())
        if r:
            return r
    for el in soup.find_all(class_=re.compile(r"(press-date|publish|posted|release-date|article-date|\bdate\b)", re.I)):
        txt = _clean(el.get_text())
        if re.search(r"updated|reviewed|modified", txt, re.I):
            continue
        r = _to_date(txt)
        if r:
            return r
    return None


def _split_names(s):
    s = BY_PREFIX_RE.sub("", s)
    parts = re.split(r"\s*(?:,|;|&|\||\s[\u2013\u2014-]\s|\band\b|\+)\s*", s)
    names = []
    for p in parts:
        p = _clean(p)
        if not p or NON_PERSON_RE.search(p) or TITLE_WORD_RE.search(p):
            continue
        if p not in names:
            names.append(p)
    return names


def _get_author(soup):
    cands = []
    for kw in [dict(name="author"), dict(property="article:author"), dict(name="DC.creator"),
               dict(itemprop="author")]:
        v = _meta(soup, **kw)
        if v and not v.startswith("http"):
            cands.append(v)
    for d in _jsonld(soup):
        a = d.get("author")
        if not a:
            continue
        items = a if isinstance(a, list) else [a]
        names = []
        for it in items:
            if isinstance(it, dict):
                if it.get("@type") == "Organization":
                    continue
                n = it.get("name")
            else:
                n = it
            if n:
                names.append(str(n))
        if names:
            cands.append(" and ".join(names))
    for el in soup.select('[rel=author], [itemprop=author], .byline, .author, .press-author, '
                          '.article-author, [class*=byline], [class*=author]'):
        txt = _clean(el.get_text())
        if txt and len(txt) < 200:
            cands.append(txt)
    for c in cands:
        names = _split_names(c)
        if names:
            return " and ".join(names)
    return None


def _get_body(soup):
    cont = _find_container(soup)
    for t in cont.find_all(["script", "style", "noscript", "form", "button", "nav",
                            "aside", "iframe", "svg", "footer", "header"]):
        t.decompose()
    for el in list(cont.find_all(True)):
        if el.decomposed if hasattr(el, "decomposed") else False:
            continue
        if el.attrs is None:
            continue
        ident = " ".join((el.get("class") or []) + [el.get("id") or ""])
        if ident.strip() and NOISE_RE.search(ident):
            el.decompose()
    for h1 in cont.find_all("h1"):
        h1.decompose()
    paras = []
    for el in cont.find_all(BLOCKS):
        if el.find(BLOCKS):
            continue
        txt = _clean(el.get_text(" "))
        txt = re.sub(r"\s+([,.;:!?])", r"\1", txt)
        if not txt:
            continue
        if re.match(r"^about\s+(us\b|the company\b|lumen\b)", txt, re.I):
            continue
        paras.append(txt)
    if not paras:
        txt = _clean(cont.get_text(" "))
        return txt
    return "\n\n".join(paras)


def _parse_release(html, url):
    soup = _soup(html)
    title = _get_title(soup)
    date = _get_date(soup)
    author = _get_author(soup)
    body = _get_body(_soup(html))
    return {"url": url, "title": title, "date": date, "author": author, "body": body}


def extract(fetch, listing_url):
    seen_pages = set()
    queue = [listing_url]
    release_urls = []
    while queue:
        page = queue.pop(0)
        key = page.rstrip("/")
        if key in seen_pages or len(seen_pages) > 200:
            continue
        seen_pages.add(key)
        try:
            html = fetch(page)
        except FetchError:
            continue
        soup = _soup(html)
        rels, pages = _listing_links(soup, page, listing_url)
        for u in rels:
            if u not in release_urls:
                release_urls.append(u)
        for p in pages:
            if p.rstrip("/") not in seen_pages:
                queue.append(p)

    records = []
    for url in release_urls:
        try:
            html = fetch(url)
        except FetchError:
            continue
        try:
            rec = _parse_release(html, url)
        except Exception:
            continue
        records.append(rec)

    order = {r["url"]: i for i, r in enumerate(records)}
    records.sort(key=lambda r: (r["date"] or "", -order[r["url"]]), reverse=True)
    return records
