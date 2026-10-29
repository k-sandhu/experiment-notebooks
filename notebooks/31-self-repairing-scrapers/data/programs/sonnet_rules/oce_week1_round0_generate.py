import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from dateutil import parser as dateparser

_BLOCK = ["p", "li", "h2", "h3", "h4", "h5", "h6", "blockquote", "pre"]
_DATE_RE = re.compile(r"\b(\d{1,2})[./](\d{1,2})[./](\d{4})\b")
_ISO_RE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
_TEXT_DATE_RE = re.compile(
    r"\b(\d{1,2}\s+[A-Za-z]{3,9}\.?\s+\d{4}|[A-Za-z]{3,9}\.?\s+\d{1,2},?\s+\d{4})\b"
)
_NOTICE_PATH = re.compile(r"/notices/[^/?#]+(?:/[^/?#]+)+/?$")


def _clean(s):
    return re.sub(r"\s+", " ", (s or "").replace("\xa0", " ")).strip()


def _parse_date(text):
    text = _clean(text)
    m = _ISO_RE.search(text)
    if m:
        return "%s-%s-%s" % m.groups()
    m = _DATE_RE.search(text)
    if m:
        d, mo, y = map(int, m.groups())
        try:
            return "%04d-%02d-%02d" % (y, mo, d)
        except Exception:
            return None
    m = _TEXT_DATE_RE.search(text)
    if m:
        try:
            return dateparser.parse(m.group(1), dayfirst=True).strftime("%Y-%m-%d")
        except Exception:
            return None
    return None


def _listing_items(soup, page_url):
    items = []
    seen = set()
    anchors = soup.select("a.notice-title")
    if not anchors:
        main = soup.find("main") or soup
        anchors = [
            a for a in main.find_all("a", href=True)
            if _NOTICE_PATH.search(urlparse(urljoin(page_url, a["href"])).path)
            and urlparse(urljoin(page_url, a["href"])).path.rstrip("/")
            != urlparse(page_url).path.rstrip("/")
        ]
    for a in anchors:
        if not a.get("href"):
            continue
        url = urljoin(page_url, a["href"]).split("#")[0]
        if url in seen:
            continue
        seen.add(url)
        date = None
        row = a.parent
        for _ in range(3):
            if row is None:
                break
            d = row.select_one(".notice-date, time, .date")
            if d:
                date = _parse_date(d.get("datetime") or d.get_text(" "))
                break
            row = row.parent
        items.append((url, _clean(a.get_text(" ")), date))
    return items


def _next_pages(soup, page_url):
    out = []
    for a in soup.find_all("a", href=True):
        rel = a.get("rel") or []
        txt = _clean(a.get_text(" ")).lower()
        href = a["href"]
        is_next = (
            "next" in rel
            or txt in ("next", "next page", "older", "›", "»", "next »", "older notices")
            or txt.startswith("next")
        )
        if not is_next and re.search(r"[?&]page=\d+", href) and a.find_parent(
            class_=re.compile("pag", re.I)
        ):
            is_next = True
        if is_next:
            out.append(urljoin(page_url, href).split("#")[0])
    link = soup.find("link", rel="next")
    if link and link.get("href"):
        out.append(urljoin(page_url, link["href"]))
    return out


def _release_date(soup, main):
    for m in soup.find_all("meta"):
        key = (m.get("property") or m.get("name") or "").lower()
        if key in ("article:published_time", "datepublished", "date", "dc.date",
                   "dc.date.issued", "pubdate", "publishdate"):
            d = _parse_date(m.get("content", ""))
            if d:
                return d
    t = main.find("time", attrs={"datetime": True}) if main else None
    if t:
        d = _parse_date(t["datetime"])
        if d:
            return d
    if main:
        for el in main.find_all(["p", "div", "span", "li"]):
            txt = _clean(el.get_text(" "))
            if len(txt) > 200:
                continue
            m = re.search(
                r"(date of issue|issued|published|publication date|date)\s*:?\s*(.*)",
                txt, re.I)
            if m and re.match(r"(?i)^(date of issue|issued|published|publication date|date)\b", txt):
                seg = re.split(r"[·|•]|\b(?:effective|updated|last updated|reviewed|closing)\b",
                               m.group(2), flags=re.I)[0]
                d = _parse_date(seg)
                if d:
                    return d
    return None


def _clean_author(text):
    text = _clean(text)
    text = re.split(r"\s[·|•]\s|\s-\s(?=\d)|\bon\s+\d", text)[0]
    text = re.sub(r"^(written\s+by|posted\s+by|author[s]?|by)\s*:?\s+", "", text, flags=re.I)
    parts = re.split(r",|&|;|\band\b", text)
    titles = re.compile(
        r"\b(director|manager|head|officer|chief|analyst|editor|president|"
        r"economist|strategist|ceo|cfo|coo|vp|vice|senior|lead|counsel|"
        r"operations|department|team|exchange)\b", re.I)
    names = [_clean(p) for p in parts if _clean(p) and not titles.search(p)]
    return " and ".join(names) if names else None


def _release_author(soup, main):
    for m in soup.find_all("meta", attrs={"name": re.compile("^author$", re.I)}):
        a = _clean_author(m.get("content", ""))
        if a:
            return a
    if main:
        el = main.select_one(".byline, .author, [rel=author], [itemprop=author]")
        if el:
            a = _clean_author(el.get_text(" "))
            if a:
                return a
        for p in main.find_all(["p", "div", "span"]):
            txt = _clean(p.get_text(" "))
            if len(txt) < 120 and re.match(r"^by\s+[A-Z]", txt):
                a = _clean_author(txt)
                if a:
                    return a
    return None


def _body(main):
    container = main.select_one(
        ".notice-text, .release-body, .article-body, .entry-content, .content-body, article"
    ) or main
    parts = []
    for el in container.find_all(_BLOCK):
        if any(p in container.find_all(_BLOCK) and p is not container
               for p in el.parents if p.name in _BLOCK and p is not el):
            continue
        if el.find_parent(["nav", "aside", "footer", "form"]):
            continue
        cls = " ".join(el.get("class") or [])
        if re.search(r"\b(ref|date|sig|byline|tags?|share|related|contact|about)\b", cls):
            continue
        txt = _clean(el.get_text(" "))
        if txt:
            parts.append(txt)
    if not parts:
        txt = container.get_text("\n")
        parts = [_clean(l) for l in txt.split("\n") if _clean(l)]
    return "\n\n".join(parts)


def _parse_release(html, url, list_title, list_date):
    soup = BeautifulSoup(html, "html.parser")
    for t in soup(["script", "style", "noscript"]):
        t.decompose()
    main = soup.find("main") or soup.body or soup
    h1 = main.find("h1")
    title = _clean(h1.get_text(" ")) if h1 else ""
    if not title:
        og = soup.find("meta", property="og:title")
        if og and og.get("content"):
            title = _clean(og["content"])
    if not title and soup.title:
        title = _clean(re.split(r"\s[|–-]\s", soup.title.get_text())[0])
    if not title:
        title = list_title
    date = _release_date(soup, main) or list_date
    return {
        "url": url,
        "title": title,
        "date": date,
        "author": _release_author(soup, main),
        "body": _body(main),
    }


def extract(fetch, listing_url):
    items = []
    seen_items = set()
    visited = set()
    queue = [listing_url]
    while queue and len(visited) < 100:
        page = queue.pop(0)
        if page in visited:
            continue
        visited.add(page)
        try:
            html = fetch(page)
        except FetchError:
            if page == listing_url:
                raise
            continue
        soup = BeautifulSoup(html, "html.parser")
        for it in _listing_items(soup, page):
            if it[0] not in seen_items:
                seen_items.add(it[0])
                items.append(it)
        for n in _next_pages(soup, page):
            if n not in visited and n not in queue:
                queue.append(n)

    records = []
    for url, ltitle, ldate in items:
        try:
            html = fetch(url)
        except FetchError:
            continue
        records.append(_parse_release(html, url, ltitle, ldate))

    indexed = list(enumerate(records))
    indexed.sort(key=lambda x: (x[1]["date"] or "", -x[0]), reverse=True)
    return [r for _, r in indexed]
