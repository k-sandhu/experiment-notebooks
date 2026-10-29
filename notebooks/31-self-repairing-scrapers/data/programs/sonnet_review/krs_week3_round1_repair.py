import json
import re
from urllib.parse import urljoin, urldefrag, urlsplit, urlunsplit, parse_qsl, urlencode

from bs4 import BeautifulSoup
from dateutil import parser as dateparser

_NOISE_RE = re.compile(
    r"share|social|newsletter|subscribe|related|tags|topics|contact|about|cookie|"
    r"breadcrumb|pager|print|sidebar|promo|banner|signup|disclaimer",
    re.I,
)
_BLOCKS = ["p", "li", "h2", "h3", "h4", "h5", "h6", "blockquote", "pre"]
_STOP_HEADING = re.compile(r"^(about\b|media contact|contacts?\b|notes to editors)", re.I)
_STOP_PARA = re.compile(r"^(about the kestria revenue service|media contacts?\b|notes to editors)", re.I)
_DATE_LABEL = re.compile(r"(updated|modified|reviewed|revised|closing|closes|effective|deadline)", re.I)


def _soup(html):
    return BeautifulSoup(html, "html.parser")


def _clean(text):
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def _parse_date(text):
    if not text:
        return None
    text = _clean(str(text))
    m = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", text)
    if m:
        return "%s-%s-%s" % m.groups()
    m = re.search(r"\b(\d{1,2})[/.](\d{1,2})[/.](\d{4})\b", text)
    if m:
        d, mo, y = map(int, m.groups())
        if 1 <= mo <= 12 and 1 <= d <= 31:
            return "%04d-%02d-%02d" % (y, mo, d)
        return None
    m = re.search(
        r"\b(\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]{3,9}\.?,?\s+\d{4}|[A-Za-z]{3,9}\.?\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})",
        text,
    )
    if m:
        try:
            return dateparser.parse(m.group(1), dayfirst=True).strftime("%Y-%m-%d")
        except Exception:
            return None
    return None


def _listing_items(soup, base):
    items = []
    rows = soup.select(".views-row")
    for row in rows:
        a = row.select_one("h1 a, h2 a, h3 a, h4 a, a[href]")
        if not a or not a.get("href"):
            continue
        url = urldefrag(urljoin(base, a["href"]))[0]
        d = row.select_one(".date-display-single, time")
        date = None
        if d:
            date = _parse_date(d.get("datetime") or d.get_text(" "))
        items.append((url, date))
    return items


def _next_page(soup, base):
    a = soup.select_one('a[rel~="next"]')
    if a and a.get("href"):
        return urldefrag(urljoin(base, a["href"]))[0]
    for a in soup.select(".pager a[href]"):
        if re.search(r"next|›|»", a.get_text(), re.I) and a.get("href"):
            return urldefrag(urljoin(base, a["href"]))[0]
    return None


def _load_more_endpoint(soup, base):
    el = soup.select_one("[data-endpoint]")
    if el and el.get("data-endpoint"):
        return urljoin(base, el["data-endpoint"])
    return None


def _json_list(data):
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for k in ("items", "results", "data", "releases", "news", "rows"):
            v = data.get(k)
            if isinstance(v, list):
                return v
            if isinstance(v, dict):
                r = _json_list(v)
                if r:
                    return r
    return []


def _json_items(data, base):
    out = []
    for it in _json_list(data):
        url = None
        date = None
        if isinstance(it, str):
            s = _soup(it)
            a = s.find("a", href=True)
            if a:
                url = a["href"]
            d = s.select_one(".date-display-single, time")
            if d:
                date = _parse_date(d.get("datetime") or d.get_text(" "))
        elif isinstance(it, dict):
            for k in ("url", "href", "link", "path", "alias", "permalink"):
                if isinstance(it.get(k), str) and it[k].strip():
                    url = it[k].strip()
                    break
            for k in ("date", "published", "published_at", "created", "pubDate", "date_display"):
                if it.get(k):
                    date = _parse_date(it[k])
                    if date:
                        break
            if url is None:
                for v in it.values():
                    if isinstance(v, str) and "<a" in v:
                        a = _soup(v).find("a", href=True)
                        if a:
                            url = a["href"]
                            break
        if url:
            out.append((urldefrag(urljoin(base, url))[0], date))
    return out


def _json_next(data, endpoint, count):
    if isinstance(data, dict):
        for k in ("next", "next_url", "nextUrl", "next_page"):
            v = data.get(k)
            if isinstance(v, str) and v:
                return urljoin(endpoint, v)
        if data.get("has_more") is False or data.get("hasMore") is False:
            return None
    parts = urlsplit(endpoint)
    q = parse_qsl(parts.query, keep_blank_values=True)
    cur = 0
    found = False
    new_q = []
    for k, v in q:
        if k == "offset":
            found = True
            try:
                cur = int(v)
            except ValueError:
                cur = 0
            new_q.append((k, str(cur + count)))
        else:
            new_q.append((k, v))
    if not found:
        return None
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(new_q), ""))


def _title(soup):
    h = soup.select_one("main h1") or soup.find("h1")
    if h:
        t = _clean(h.get_text(" "))
        if t:
            return t
    og = soup.find("meta", property="og:title")
    if og and og.get("content"):
        return _clean(og["content"])
    if soup.title:
        t = _clean(soup.title.get_text())
        return re.sub(r"\s*[|–-]\s*Kestria Revenue Service\s*$", "", t)
    return None


def _page_date(soup, fallback):
    for sel in (".field-date", ".date-display-single", ".published", ".publish-date",
                ".release-date", ".post-date", "time[datetime]", "time"):
        for el in soup.select(sel):
            raw = el.get("datetime") or el.get_text(" ")
            if _DATE_LABEL.search(raw) and not re.search(r"publish|posted|released", raw, re.I):
                continue
            d = _parse_date(raw)
            if d:
                return d
    for key in ("article:published_time", "datePublished", "date", "DC.date.issued"):
        m = soup.find("meta", attrs={"property": key}) or soup.find("meta", attrs={"name": key})
        if m and m.get("content"):
            d = _parse_date(m["content"])
            if d:
                return d
    return fallback


def _author(soup):
    raw = None
    for sel in (".field-author", ".byline", ".author", '[rel="author"]', '[itemprop="author"]'):
        el = soup.select_one(sel)
        if el and _clean(el.get_text()):
            raw = _clean(el.get_text(" "))
            break
    if raw is None:
        m = soup.find("meta", attrs={"name": "author"})
        if m and m.get("content"):
            raw = _clean(m["content"])
    if not raw:
        return None
    raw = re.sub(r"^(written\s+)?(by|author|authors)\s*:?\s*", "", raw, flags=re.I)
    names = []
    for part in re.split(r"\s+and\s+|\s*&\s*|;", raw):
        part = re.split(r",|\s[-–|]\s", part)[0]
        part = _clean(part)
        if part and not re.search(r"\b(service|department|office|team|press)\b", part, re.I):
            names.append(part)
    return " and ".join(names) if names else None


def _body(soup):
    container = None
    for sel in (".field-body", ".field--name-body", "[itemprop=articleBody]", ".release-body",
                ".article-body", "article", "main"):
        container = soup.select_one(sel)
        if container:
            break
    if container is None:
        container = soup.body or soup
    for el in container.find_all(["script", "style", "nav", "aside", "form", "footer", "header",
                                  "noscript", "button", "iframe"]):
        el.decompose()
    for el in list(container.find_all(True)):
        if getattr(el, "decomposed", False) or el.attrs is None:
            continue
        cls = " ".join(el.get("class") or []) + " " + (el.get("id") or "")
        if el is not container and _NOISE_RE.search(cls) and not re.search(r"field-body", cls):
            el.decompose()
    for br in container.find_all("br"):
        br.replace_with(" ")
    h1 = container.find("h1")
    if h1:
        h1.decompose()
    paras = []
    for el in container.find_all(_BLOCKS):
        if el.find(_BLOCKS):
            continue
        text = _clean(el.get_text())
        if not text:
            continue
        if el.name.startswith("h") and _STOP_HEADING.match(text):
            break
        if _STOP_PARA.match(text):
            break
        paras.append(text)
    return "\n\n".join(paras)


def extract(fetch, listing_url):
    items = []
    seen_urls = set()

    def add(found):
        new = 0
        for url, date in found:
            if url not in seen_urls:
                seen_urls.add(url)
                items.append((url, date))
                new += 1
        return new

    seen_pages = set()
    page = listing_url
    endpoint = None
    while page and page not in seen_pages:
        seen_pages.add(page)
        try:
            html = fetch(page)
        except FetchError:
            if page == listing_url:
                raise
            break
        soup = _soup(html)
        new = add(_listing_items(soup, page))
        ep = _load_more_endpoint(soup, page)
        if ep:
            endpoint = ep
        if new == 0:
            break
        page = _next_page(soup, page)

    # "Load more" JSON endpoint
    seen_eps = set()
    while endpoint and endpoint not in seen_eps:
        seen_eps.add(endpoint)
        try:
            data = json.loads(fetch(endpoint))
        except (FetchError, ValueError):
            break
        found = _json_items(data, endpoint)
        if not found or add(found) == 0:
            break
        endpoint = _json_next(data, endpoint, len(_json_list(data)))

    records = []
    for url, list_date in items:
        try:
            soup = _soup(fetch(url))
        except FetchError:
            continue
        records.append({
            "url": url,
            "title": _title(soup),
            "date": _page_date(soup, list_date),
            "author": _author(soup),
            "body": _body(soup),
        })
    records.sort(key=lambda r: r["date"] or "", reverse=True)
    return records
