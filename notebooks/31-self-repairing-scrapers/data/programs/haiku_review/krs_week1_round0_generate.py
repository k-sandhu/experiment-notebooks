import re
from datetime import date as _date
from urllib.parse import urljoin, urldefrag, urlsplit

from bs4 import BeautifulSoup, NavigableString
from dateutil import parser as _dateparser


_ISO_RE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
_DMY_RE = re.compile(r"\b(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{4})\b")
_LABEL_RE = re.compile(r"\s*(first\s+)?(published|date)\b", re.I)
_PUBLISHED_RE = re.compile(r"publish|issued", re.I)
_NOT_DATE_RE = re.compile(r"updat|revis|review|modif|effective|clos|event|expir|amend", re.I)
_SKIP_TAGS = {"script", "style", "noscript", "template", "nav", "aside", "form",
              "button", "input", "select", "textarea", "iframe", "svg", "header", "footer"}
_SKIP_CLASS_RE = re.compile(
    r"share|social|newsletter|related|tag|contact|cookie|breadcrumb|date|title|author|byline|about|pager",
    re.I,
)
_BLOCK_TAGS = {"p", "li", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote",
               "pre", "div", "section", "article", "table", "tr", "td", "th", "dl", "dt",
               "dd", "figure", "figcaption"}
_NOT_NAME_RE = re.compile(
    r"\b(director|manager|officer|head|chief|commissioner|deputy|senior|junior|analyst|"
    r"advis[eo]r|editor|spokes(?:person|man|woman)|minister|secretary|president|partner|"
    r"lead|principal|specialist|assistant|coordinator|executive|supervisor|writer|reporter|"
    r"team|unit|department|branch|office|policy|communications?|media|press|service|"
    r"revenue|kestria|author|posted|updated|published)\b",
    re.I,
)


def _clean(text):
    return " ".join((text or "").split())


def _class_text(el):
    return " ".join(el.get("class") or [])


def _to_iso(text):
    if not text:
        return None
    m = _ISO_RE.search(text)
    if m:
        y, mo, d = (int(g) for g in m.groups())
    else:
        m = _DMY_RE.search(text)
        if m:
            d, mo, y = (int(g) for g in m.groups())
        elif re.search(r"\b(?:19|20)\d{2}\b", text):
            try:
                return _dateparser.parse(text, dayfirst=True, fuzzy=True).date().isoformat()
            except (ValueError, OverflowError, TypeError):
                return None
        else:
            return None
    try:
        return _date(y, mo, d).isoformat()
    except ValueError:
        return None


def _published_date(soup):
    for sel in ('meta[property="article:published_time"]',
                'meta[name="DC.date.issued"]',
                'meta[name="dcterms.issued"]'):
        meta = soup.select_one(sel)
        iso = _to_iso(meta.get("content", "")) if meta else None
        if iso:
            return iso
    best = None
    for el in soup.find_all(True):
        if el.name in ("script", "style"):
            continue
        text = _clean(el.get_text(" "))
        classes = _class_text(el)
        if not text or len(text) > 120:
            continue
        if not (re.search(r"date|publish|issued", classes, re.I) or _LABEL_RE.match(text)):
            continue
        if _NOT_DATE_RE.search(classes) or _NOT_DATE_RE.search(text):
            continue
        iso = _to_iso(text)
        if not iso:
            continue
        rank = 0 if _PUBLISHED_RE.search(text + " " + classes) else 1
        if best is None or rank < best[0]:
            best = (rank, iso)
    return best[1] if best else None


def _clean_author(text):
    text = _clean(text)
    text = re.sub(r"^By\b\s*:?\s*", "", text, flags=re.I)
    text = re.sub(r"\([^)]*\)", " ", text)
    names = []
    for part in re.split(r"\s*(?:,|;|\||&|\band\b)\s*", text, flags=re.I):
        m = _NOT_NAME_RE.search(part)
        if m:
            part = part[:m.start()]
        part = part.strip(" .:-")
        if not part or re.search(r"\d", part):
            continue
        if part not in names:
            names.append(part)
    return " and ".join(names) or None


def _inside(el, container):
    return container is not None and any(p is container for p in el.parents)


def _author(soup, main, container):
    meta = soup.find("meta", attrs={"name": re.compile(r"^author$", re.I)})
    if meta and meta.get("content"):
        name = _clean_author(meta["content"])
        if name:
            return name
    for el in main.find_all(True):
        if el.name in _SKIP_TAGS or not re.search(r"author|byline", _class_text(el), re.I):
            continue
        text = _clean(el.get_text(" "))
        if 0 < len(text) <= 200:
            name = _clean_author(text)
            if name:
                return name
    for el in main.find_all(True):
        if el.name in _SKIP_TAGS or _inside(el, container):
            continue
        text = _clean(el.get_text(" "))
        if 0 < len(text) <= 150 and re.match(r"By\s+\S", text, re.I):
            name = _clean_author(text)
            if name:
                return name
    return None


def _body_paragraphs(root):
    paragraphs = []
    buf = []

    def flush():
        text = _clean("".join(buf))
        if text:
            paragraphs.append(text)
        buf.clear()

    def walk(node):
        for child in node.children:
            if isinstance(child, NavigableString):
                if type(child) is NavigableString:
                    buf.append(str(child))
                continue
            if child.name in _SKIP_TAGS:
                continue
            if child.name == "br":
                buf.append(" ")
            elif child.name in ("div", "section", "ul", "ol") and _SKIP_CLASS_RE.search(_class_text(child)):
                continue
            elif child.name in _BLOCK_TAGS:
                flush()
                walk(child)
                flush()
            else:
                walk(child)

    walk(root)
    flush()
    return paragraphs


def _listing_entries(fetch, listing_url):
    origin = urlsplit(listing_url).netloc
    path = urlsplit(listing_url).path
    queue = [listing_url]
    seen_pages = set()
    seen_urls = set()
    entries = []
    while queue:
        page_url = queue.pop(0)
        if page_url in seen_pages:
            continue
        seen_pages.add(page_url)
        soup = BeautifulSoup(fetch(page_url), "html.parser")
        for row in soup.select(".views-row"):
            link = row.select_one(".field-title a[href]") or row.select_one("h2 a[href], h3 a[href], h4 a[href]")
            if link is None:
                continue
            url = urldefrag(urljoin(page_url, link["href"])).url
            if url in seen_urls:
                continue
            seen_urls.add(url)
            when = row.select_one(".date-display-single, time, .field-date")
            entries.append({
                "url": url,
                "title": _clean(link.get_text()),
                "date": _to_iso(when.get_text(" ")) if when else None,
            })
        for a in soup.select(".pager a[href], a[rel~='next']"):
            nxt = urldefrag(urljoin(page_url, a["href"])).url
            parts = urlsplit(nxt)
            if parts.netloc == origin and parts.path == path and nxt not in seen_pages:
                queue.append(nxt)
    return entries


def extract(fetch, listing_url):
    records = []
    for entry in _listing_entries(fetch, listing_url):
        # FetchError is deliberately not caught: a missing release should fail the run, not drop silently.
        soup = BeautifulSoup(fetch(entry["url"]), "html.parser")
        main = soup.find("main") or soup
        container = soup.select_one(".field-body") or soup.select_one("article") or main
        h1 = main.find("h1") or soup.find("h1")
        title = _clean(h1.get_text()) if h1 else ""
        if not title:
            title = entry["title"]
        date = _published_date(soup) or entry["date"]
        records.append({
            "url": entry["url"],
            "title": title,
            "date": date,
            "author": _author(soup, main, container),
            "body": "\n\n".join(_body_paragraphs(container)),
        })
    records.sort(key=lambda r: r["date"] or "", reverse=True)
    return records
