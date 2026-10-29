import json
import re
from urllib.parse import urljoin, urlencode, urlparse, parse_qsl, urlunparse

from bs4 import BeautifulSoup, NavigableString, Tag
from dateutil import parser as dateparser

API_PATH = "/api/v2/news"
PAGE_LIMIT = 8
MAX_PAGES = 200

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


def _find_items(data):
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for k in ("items", "results", "data", "news", "articles", "releases"):
            v = data.get(k)
            if isinstance(v, list):
                return v
            if isinstance(v, dict):
                r = _find_items(v)
                if r:
                    return r
    return []


def _get(d, *keys):
    for k in keys:
        if isinstance(d, dict) and d.get(k) not in (None, ""):
            return d[k]
    return None


def _next_link(data):
    if not isinstance(data, dict):
        return None
    cands = [data]
    for k in ("links", "pagination", "meta", "_links", "paging"):
        if isinstance(data.get(k), dict):
            cands.append(data[k])
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
    for c in cands:
        if c.get("has_more") is True or c.get("hasMore") is True or c.get("has_next") is True:
            return True
        total = _get(c, "total", "total_count", "totalItems", "count_total")
        if isinstance(total, int) and total > collected:
            return True
        tp = _get(c, "total_pages", "pages", "totalPages", "page_count")
        if isinstance(tp, int) and tp > page:
            return True
    return False


def _with_params(url, **params):
    p = urlparse(url)
    q = dict(parse_qsl(p.query))
    q.update({k: str(v) for k, v in params.items()})
    return urlunparse(p._replace(query=urlencode(q)))


def _item_key(it):
    return str(_get(it, "id", "slug", "url", "path", "uuid") or json.dumps(it, sort_keys=True))


def _list_items(fetch, listing_url):
    base = urljoin(listing_url, API_PATH)
    url = _with_params(base, limit=PAGE_LIMIT)
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
            url = _with_params(base, limit=PAGE_LIMIT, page=page,
                               offset=len(items))
            if not _more_expected(data, len(items), page - 1) and len(got) < PAGE_LIMIT:
                break
            continue
        else:
            break
        page += 1
    return items


def _article_url(listing_url, it):
    u = _get(it, "url", "link", "permalink", "href")
    if isinstance(u, str) and "/api/" not in u:
        return urljoin(listing_url, u)
    slug = _get(it, "slug")
    if slug:
        return urljoin(listing_url, "/about/newsroom/article/%s" % slug)
    return None


# ---------- text extraction ----------

def _is_boiler(tag):
    if not isinstance(tag, Tag) or tag.attrs is None:
        return False
    ident = " ".join(
        [" ".join(tag.get("class") or []), tag.get("id") or "",
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
                buf.append(str(ch).replace("\n", " ") if "\n" not in str(ch) else str(ch).replace("\n", " "))
            elif isinstance(ch, Tag):
                if ch.name in BLOCK_TAGS:
                    flush()
                    walk(ch)
                    flush()
                else:
                    walk(ch)

    walk(soup)
    flush()
    # trim trailing standard "About ..." boilerplate paragraphs
    out = []
    skipping = False
    for p in paras:
        if ABOUT_RE.match(p):
            skipping = True
        if skipping:
            continue
        out.append(p)
    return "\n\n".join(out)


# ---------- fields ----------

def _author(a):
    names = []

    def add(x):
        if x is None:
            return
        if isinstance(x, str):
            n = _plain(x)
        elif isinstance(x, dict):
            n = _plain(_get(x, "display_name", "name", "full_name", "fullName"))
            if not n:
                fn = _get(x, "first_name", "firstName")
                ln = _get(x, "last_name", "lastName")
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


def _article_id(fetch, page_url):
    html = fetch(page_url)
    soup = BeautifulSoup(html, "html.parser")
    art = soup.find(attrs={"data-id": True})
    if art:
        return art["data-id"], soup
    m = re.search(r"/api/v\d+/news/([\w-]+)", html)
    return (m.group(1) if m else None), soup


def extract(fetch, listing_url):
    items = _list_items(fetch, listing_url)
    api_base = urljoin(listing_url, API_PATH)
    records = []
    for it in items:
        url = _article_url(listing_url, it)
        aid = None
        if url:
            try:
                aid, _ = _article_id(fetch, url)
            except Exception:
                aid = None
        if not aid:
            aid = _get(it, "id", "uuid")
        detail = None
        if aid is not None:
            try:
                detail = _loads(fetch("%s/%s" % (api_base, aid)))
            except Exception:
                detail = None
        if isinstance(detail, dict) and isinstance(detail.get("item"), dict):
            detail = detail["item"]
        elif isinstance(detail, dict) and isinstance(detail.get("data"), dict):
            detail = detail["data"]
        if not isinstance(detail, dict):
            continue
        if not url:
            slug = _get(detail, "slug")
            if not slug:
                continue
            url = urljoin(listing_url, "/about/newsroom/article/%s" % slug)
        title = _plain(_get(detail, "title", "headline")) or _plain(_get(it, "title", "headline"))
        date = _date(_get(detail, "published_at", "publishedAt", "publish_date",
                          "date_published", "first_published_at", "date")) \
            or _date(_get(it, "published_at", "publishedAt", "date"))
        body_html = _get(detail, "body_html", "body", "content_html", "content", "html")
        records.append({
            "url": url,
            "title": title,
            "date": date,
            "author": _author(detail.get("author", detail.get("authors", detail.get("byline")))),
            "body": _html_to_text(body_html if isinstance(body_html, str) else ""),
        })
    records.sort(key=lambda r: r["date"] or "", reverse=True)
    return records
