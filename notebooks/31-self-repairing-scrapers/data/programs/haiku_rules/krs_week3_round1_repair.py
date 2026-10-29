import json
import re
from datetime import date as _date
from urllib.parse import parse_qsl, urlencode, urljoin, urldefrag, urlsplit, urlunsplit

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
    r"\b(share|social|newsletter|related|tags?|contact|cookie|breadcrumb|date|title|"
    r"author|byline|about|pager)",
    re.I,
)
_BLOCK_TAGS = {"p", "li", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote",
               "pre", "div", "section", "article", "table", "tr", "td", "th", "dl", "dt",
               "dd", "figure", "figcaption"}
_HEADING_TAGS = ["h1", "h2", "h3", "h4", "h5", "h6"]
_NOT_NAME_RE = re.compile(
    r"\b(director|manager|officer|head|chief|commissioner|deputy|senior|junior|analyst|"
    r"advis[eo]r|editor|spokes(?:person|man|woman)|minister|secretary|president|partner|"
    r"lead|principal|specialist|assistant|coordinator|executive|supervisor|writer|reporter|"
    r"team|unit|department|branch|office|policy|communications?|media|press|service|"
    r"revenue|kestria|author|posted|updated|published)\b",
    re.I,
)
_URL_LIKE_RE = re.compile(r"^(?:https?://|/)\S+$")
_MAX_REQUESTS = 500


def _clean(text):
    return " ".join((text or "").split())


def _class_text(el):
    return " ".join(el.get("class") or [])


def _inside(el, container):
    # The document root is never treated as a container.
    if container is None or container.name == "[document]":
        return False
    return any(p is container for p in el.parents)


def _in_chrome(el):
    return el.find_parent(["header", "footer", "nav", "aside", "form"]) is not None


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


def _published_date(soup, container):
    for sel in ('meta[property="article:published_time"]',
                'meta[name="DC.date.issued"]',
                'meta[name="dcterms.issued"]'):
        meta = soup.select_one(sel)
        iso = _to_iso(meta.get("content", "")) if meta else None
        if iso:
            return iso
    best = None
    for el in soup.find_all(True):
        if el.name in ("script", "style", "head", "title") or _in_chrome(el) or _inside(el, container):
            continue
        text = _clean(el.get_text(" "))
        classes = _class_text(el)
        if not text or len(text) > 120:
            continue
        if not (el.name == "time" or re.search(r"date|publish|issued", classes, re.I)
                or _LABEL_RE.match(text)):
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
        if el.name in _SKIP_TAGS or _inside(el, container) or _in_chrome(el):
            continue
        text = _clean(el.get_text(" "))
        if 0 < len(text) <= 150 and re.match(r"By\s+\S", text, re.I):
            name = _clean_author(text)
            if name:
                return name
    return None


def _drop_boilerplate(container):
    # Remove "About us" sections and standard about paragraphs from the body.
    for heading in container.find_all(_HEADING_TAGS):
        if not re.match(r"about\b", _clean(heading.get_text()), re.I):
            continue
        for sib in list(heading.find_next_siblings()):
            if sib.name in _HEADING_TAGS:
                break
            sib.decompose()
        heading.decompose()
    for p in list(container.find_all("p")):
        if re.match(r"about\s+(us|the\s+kestria|kestria)\b", _clean(p.get_text()), re.I):
            p.decompose()


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
            elif child.name in _BLOCK_TAGS and _SKIP_CLASS_RE.search(_class_text(child)):
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


def _release_url(href, page_url, base):
    href = (href or "").strip()
    if not _URL_LIKE_RE.match(href):
        return None
    url = urldefrag(urljoin(page_url, href)).url
    parts = urlsplit(url)
    if parts.netloc != base.netloc or parts.query:
        return None
    prefix = base.path.rstrip("/") + "/"
    path = parts.path.rstrip("/")
    if not path.startswith(prefix) or "/api/" in path + "/":
        return None
    return url


def _listing_rows(soup, page_url, base, fragment=False):
    # Returns (url, listing_title, listing_date) for each release found.
    rows = soup.select(".views-row")
    if not rows and fragment:
        rows = soup.select("a[href]")
    found = []
    for row in rows:
        if row.name == "a":
            anchors = [row]
            when = None
        else:
            anchors = row.select(".field-title a[href]") or row.select("a[href]")
            when = row.select_one(".date-display-single, time, .field-date")
        for a in anchors:
            url = _release_url(a.get("href"), page_url, base)
            if url:
                found.append((url, _clean(a.get_text()), _to_iso(when.get_text(" ")) if when else None))
                break
    return found


def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from _strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from _strings(v)


def _load_json(body):
    try:
        return json.loads(body)
    except (TypeError, ValueError):
        return None


def _payload_items(payload):
    if isinstance(payload, dict):
        payload = payload.get("items") or []
    return payload if isinstance(payload, list) else []


def _item_rows(item, source, base):
    fragments = [s for s in _strings(item) if "<" in s]
    if fragments:
        soup = BeautifulSoup("\n".join(fragments), "html.parser")
        return _listing_rows(soup, source, base, fragment=True)
    rows = []
    for s in _strings(item):
        url = _release_url(s, source, base) if _URL_LIKE_RE.match(s.strip()) else None
        if url:
            rows.append((url, None, None))
    return rows


def _next_offset(endpoint, count):
    parts = urlsplit(endpoint)
    query = dict(parse_qsl(parts.query))
    if "offset" not in query:
        return None
    try:
        offset = int(query["offset"])
    except ValueError:
        return None
    query["offset"] = str(offset + count)
    return urlunsplit(parts._replace(query=urlencode(query)))


def _listing_entries(fetch, listing_url):
    base = urlsplit(listing_url)
    base_path = base.path.rstrip("/")
    queue = [("page", listing_url)]
    visited = set()
    entries = {}
    while queue and len(visited) < _MAX_REQUESTS:
        kind, source = queue.pop(0)
        if source in visited:
            continue
        visited.add(source)
        body = fetch(source)
        items = []
        if kind == "page":
            soup = BeautifulSoup(body, "html.parser")
            rows = _listing_rows(soup, source, base)
            for a in soup.select(".pager a[href], a[rel~='next']"):
                nxt = urldefrag(urljoin(source, a["href"])).url
                parts = urlsplit(nxt)
                if parts.netloc == base.netloc and parts.path.rstrip("/") == base_path:
                    queue.append(("page", nxt))
            # The "Load more" button pages through a JSON endpoint.
            for button in soup.select("[data-endpoint]"):
                queue.append(("items", urljoin(source, button["data-endpoint"])))
        else:
            payload = _load_json(body)
            items = _payload_items(payload)
            rows = []
            for item in items:
                rows.extend(_item_rows(item, source, base))
        fresh = 0
        for url, title, date in rows:
            if url not in entries:
                entries[url] = {"url": url, "title": title, "date": date}
                fresh += 1
        if kind == "items" and items and fresh:
            following = _next_offset(source, len(items))
            if following:
                queue.append(("items", following))
    return list(entries.values())


def extract(fetch, listing_url):
    records = []
    for entry in _listing_entries(fetch, listing_url):
        # FetchError is deliberately not caught: a missing release should fail the run, not drop silently.
        soup = BeautifulSoup(fetch(entry["url"]), "html.parser")
        main = soup.find("main") or soup
        container = soup.select_one(".field-body") or soup.select_one("article") or main
        _drop_boilerplate(container)
        h1 = main.find("h1") or soup.find("h1")
        title = _clean(h1.get_text()) if h1 else ""
        if not title:
            title = entry["title"] or ""
        date = _published_date(soup, container) or entry["date"]
        records.append({
            "url": entry["url"],
            "title": title,
            "date": date,
            "author": _author(soup, main, container),
            "body": "\n\n".join(_body_paragraphs(container)),
        })
    records.sort(key=lambda r: r["date"] or "", reverse=True)
    return records
