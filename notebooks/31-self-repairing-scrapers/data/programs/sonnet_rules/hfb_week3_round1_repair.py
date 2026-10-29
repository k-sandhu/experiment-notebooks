import json
import re
from urllib.parse import urljoin, urlencode, urlparse, parse_qsl, urlunparse

from bs4 import BeautifulSoup, NavigableString, Tag
from dateutil import parser as dateparser

API_PATH = "/api/v3/newsroom/items"
PAGE_LIMIT = 8
MAX_PAGES = 200
ARTICLE_PATH = "/about/newsroom/article/%s"

BLOCK_TAGS = {
    "p", "div", "section", "article", "ul", "ol", "li", "blockquote", "pre",
    "h1", "h2", "h3", "h4", "h5", "h6", "table", "tr", "figure", "figcaption",
    "dl", "dt", "dd", "header", "footer", "aside", "main",
}
DROP_TAGS = {"script", "style", "noscript", "form", "button", "iframe", "svg",
             "nav", "aside", "template"}
BOILER_RE = re.compile(
    r"share|social|related|newsletter|subscribe|cookie|breadcrumb|"
    r"(^|[-_ ])tags?([-_ ]|$)|contact|about-us|aboutus|boilerplate|"
    r"media-enquir|print|disclaimer|promo|signup|sign-up",
    re.I,
)
ABOUT_RE = re.compile(r"^\s*(about|über)\s+(harrow|us\b)", re.I)


def _norm(k):
    return re.sub(r"[^a-z0-9]", "", str(k).lower())


def _loads(text):
    try:
        return json.loads(text)
    except (ValueError, TypeError):
        return None


def _plain(s):
    if s is None:
        return ""
    s = str(s)
    if "<" in s or "&" in s:
        s = BeautifulSoup(s, "html.parser").get_text(" ")
    return re.sub(r"\s+", " ", s).strip()


def _g(d, *names):
    """Case/underscore-insensitive lookup of the first non-empty key."""
    if not isinstance(d, dict):
        return None
    m = {}
    for k, v in d.items():
        m.setdefault(_norm(k), v)
    for n in names:
        v = m.get(_norm(n))
        if v not in (None, "", [], {}):
            return v
    return None


def _flat(item):
    """Merge a JSON:API-style item (id + attributes) into one dict."""
    out = {}
    if not isinstance(item, dict):
        return out
    for k, v in item.items():
        if k != "attributes":
            out[k] = v
    attrs = item.get("attributes")
    if isinstance(attrs, dict):
        out.update(attrs)
    return out


def _find_items(data):
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for k in ("data", "items", "results", "news", "articles", "releases"):
            v = data.get(k)
            if isinstance(v, list):
                return v
            if isinstance(v, dict):
                r = _find_items(v)
                if r:
                    return r
    return []


def _next_link(data):
    if not isinstance(data, dict):
        return None
    cands = [data]
    for k in ("links", "pagination", "meta", "_links", "paging"):
        if isinstance(data.get(k), dict):
            cands.append(data[k])
            for k2 in ("pagination",):
                if isinstance(data[k].get(k2), dict):
                    cands.append(data[k][k2])
    for c in cands:
        for k in ("next", "next_url", "nextUrl", "next_page_url", "next_link"):
            v = c.get(k)
            if isinstance(v, dict):
                v = v.get("href") or v.get("url")
            if isinstance(v, str) and v.strip():
                return v.strip()
    return None


def _more_expected(data, collected, page):
    if not isinstance(data, dict):
        return False
    cands = [data]
    for k in ("pagination", "meta", "paging", "links"):
        if isinstance(data.get(k), dict):
            cands.append(data[k])
            if isinstance(data[k].get("pagination"), dict):
                cands.append(data[k]["pagination"])
    for c in cands:
        if c.get("has_more") is True or c.get("hasMore") is True or c.get("has_next") is True:
            return True
        total = _g(c, "total", "total_count", "totalItems", "totalResults")
        if isinstance(total, int) and total > collected:
            return True
        tp = _g(c, "total_pages", "pages", "totalPages", "page_count", "pageCount")
        if isinstance(tp, int) and tp > page:
            return True
    return False


def _with_params(url, **params):
    p = urlparse(url)
    q = dict(parse_qsl(p.query))
    q.update({k: str(v) for k, v in params.items()})
    return urlunparse(p._replace(query=urlencode(q)))


def _item_key(it):
    f = _flat(it)
    return str(_g(f, "id", "slug", "url", "uuid") or json.dumps(it, sort_keys=True, default=str))


def _list_items(fetch, listing_url):
    base = urljoin(listing_url, API_PATH)
    url = _with_params(base, pageSize=PAGE_LIMIT)
    seen, items = set(), []
    page = 1
    while url and page <= MAX_PAGES:
        try:
            data = _loads(fetch(url))
        except Exception:
            if page == 1:
                raise
            break
        got = _find_items(data)
        new = 0
        for it in got:
            if not isinstance(it, dict):
                continue
            k = _item_key(it)
            if k in seen:
                continue
            seen.add(k)
            items.append(it)
            new += 1
        if not got or not new:
            break
        nxt = _next_link(data)
        if nxt:
            url = urljoin(url, nxt)
        elif _more_expected(data, len(items), page) or len(got) >= PAGE_LIMIT:
            page += 1
            url = _with_params(base, pageSize=PAGE_LIMIT, page=page)
            continue
        else:
            break
        page += 1
    return items


def _article_url(listing_url, f):
    u = _g(f, "url", "link", "permalink", "href", "path")
    if isinstance(u, str) and "/api/" not in u:
        return urljoin(listing_url, u)
    slug = _g(f, "slug")
    if slug:
        return urljoin(listing_url, ARTICLE_PATH % slug)
    return None


# ---------- text extraction ----------

def _is_boiler(tag):
    if not isinstance(tag, Tag) or tag.attrs is None:
        return False
    cls = tag.get("class") or []
    if isinstance(cls, str):
        cls = [cls]
    ident = " ".join(
        [" ".join(cls), tag.get("id") or "",
         tag.get("role") or "", tag.get("data-component") or ""]
    )
    return bool(ident.strip() and BOILER_RE.search(ident))


def _html_to_text(html):
    soup = BeautifulSoup(html or "", "html.parser")
    for t in list(soup.find_all(True)):
        if t.parent is None:
            continue
        if t.name in DROP_TAGS or _is_boiler(t):
            t.decompose()
    for br in soup.find_all("br"):
        br.replace_with("\n")

    paras = []
    buf = []

    def flush():
        txt = re.sub(r"[ \t\r\f\v\u00a0]+", " ", "".join(buf))
        txt = re.sub(r" ?\n ?", "\n", txt).strip()
        buf.clear()
        if txt:
            paras.append(txt)

    def walk(node):
        for ch in node.children:
            if isinstance(ch, NavigableString):
                if type(ch).__name__ in ("Comment", "Doctype", "CData"):
                    continue
                s = str(ch)
                buf.append(s)
            elif isinstance(ch, Tag):
                if ch.name in BLOCK_TAGS:
                    flush()
                    walk(ch)
                    flush()
                else:
                    walk(ch)

    walk(soup)
    flush()
    out = []
    for p in paras:
        if ABOUT_RE.match(p):
            break
        out.append(p)
    return "\n\n".join(out)


def _body_text(v):
    if isinstance(v, str):
        if "<" not in v:
            parts = [p.strip() for p in re.split(r"\n\s*\n|\r\n\s*\r\n", v) if p.strip()]
            return "\n\n".join(parts)
        return _html_to_text(v)
    if isinstance(v, list):
        parts = []
        for x in v:
            t = _body_text(x if not isinstance(x, dict) else
                           (_g(x, "html", "text", "body", "content", "value") or ""))
            if t:
                parts.append(t)
        return "\n\n".join(parts)
    if isinstance(v, dict):
        return _body_text(_g(v, "html", "text", "body", "content", "value") or "")
    return ""


# ---------- fields ----------

def _author(a):
    names = []

    def add(x):
        if x is None:
            return
        if isinstance(x, str):
            n = _plain(x)
        elif isinstance(x, dict):
            if "data" in x and not _g(x, "name", "displayName"):
                add(x["data"])
                return
            if isinstance(x.get("attributes"), dict):
                add(x["attributes"])
                return
            n = _plain(_g(x, "displayName", "name", "fullName"))
            if not n:
                fn = _g(x, "firstName", "givenName")
                ln = _g(x, "lastName", "familyName", "surname")
                n = _plain("%s %s" % (fn or "", ln or ""))
        elif isinstance(x, list):
            for y in x:
                add(y)
            return
        else:
            return
        n = re.sub(r"^\s*by\s+", "", n, flags=re.I).strip()
        if n and n not in names:
            names.append(n)

    add(a)
    return " and ".join(names) if names else None


def _date(v):
    if v is None or v == "":
        return None
    try:
        if isinstance(v, (int, float)):
            from datetime import datetime, timezone
            if v > 1e11:
                v = v / 1000.0
            return datetime.fromtimestamp(v, timezone.utc).strftime("%Y-%m-%d")
        return dateparser.parse(str(v)).date().isoformat()
    except (ValueError, OverflowError, TypeError):
        return None


DATE_KEYS = ("publishedAt", "publishedOn", "publishDate", "publicationDate",
             "datePublished", "firstPublishedAt", "firstPublished",
             "releaseDate", "date")


def _page_item_id(fetch, page_url):
    try:
        html = fetch(page_url)
    except Exception:
        return None
    soup = BeautifulSoup(html, "html.parser")
    art = soup.find(attrs={"data-item": True})
    if art:
        return art["data-item"]
    m = re.search(r"/api/v\d+/newsroom/items/([\w-]+)", html)
    return m.group(1) if m else None


def _fetch_detail(fetch, api_base, aid):
    try:
        d = _loads(fetch("%s/%s" % (api_base, aid)))
    except Exception:
        return None
    if isinstance(d, dict) and isinstance(d.get("data"), dict):
        d = d["data"]
    elif isinstance(d, dict) and isinstance(d.get("item"), dict):
        d = d["item"]
    return _flat(d) if isinstance(d, dict) else None


def extract(fetch, listing_url):
    items = _list_items(fetch, listing_url)
    api_base = urljoin(listing_url, API_PATH)
    records = []
    for it in items:
        lf = _flat(it)
        url = _article_url(listing_url, lf)
        aid = _g(lf, "id", "uuid")
        detail = _fetch_detail(fetch, api_base, aid) if aid is not None else None
        if detail is None and url:
            pid = _page_item_id(fetch, url)
            if pid:
                detail = _fetch_detail(fetch, api_base, pid)
        if detail is None:
            detail = {}
        merged = dict(lf)
        merged.update({k: v for k, v in detail.items() if v not in (None, "", [], {})})
        if not url:
            url = _article_url(listing_url, merged)
        if not url:
            continue
        title = _plain(_g(detail, "headline", "title")) or _plain(_g(lf, "headline", "title"))
        date = _date(_g(detail, *DATE_KEYS)) or _date(_g(lf, *DATE_KEYS))
        body_raw = _g(detail, "bodyHtml", "body", "contentHtml", "content", "html", "text")
        if body_raw is None:
            body_raw = _g(lf, "bodyHtml", "body", "contentHtml", "content", "html", "text")
        author = _g(merged, "author", "authors", "byline", "writtenBy")
        records.append({
            "url": url,
            "title": title,
            "date": date,
            "author": _author(author),
            "body": _body_text(body_raw),
        })
    records.sort(key=lambda r: r["date"] or "", reverse=True)
    return records
