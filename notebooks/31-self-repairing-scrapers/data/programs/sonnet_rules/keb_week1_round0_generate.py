import json
import re
from urllib.parse import urljoin, urlparse, urldefrag

from bs4 import BeautifulSoup
from dateutil import parser as dateparser

DATE_RE = re.compile(
    r"\d{4}-\d{2}-\d{2}"
    r"|\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]{3,9}\.?,?\s+\d{4}"
    r"|[A-Za-z]{3,9}\.?\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}"
)
PUB_LABEL_RE = re.compile(
    r"^\s*(?:first\s+)?(published|posted|issued|released|release date|publication date|date published|date)\b\s*(?:on)?\s*[:\-–]?\s*(.*)$",
    re.I,
)
SKIP_DATE_RE = re.compile(r"updated|modified|reviewed|closes|closing|effective|event", re.I)
NOISE_CLASS_RE = re.compile(
    r"share|social|related|newsletter|subscribe|cookie|consent|breadcrumb|tags?\b|tag-|"
    r"contact|about|sidebar|promo|print|pagination|skip|banner|signup|sign-up|"
    r"keywords|topics|download|back-to|more-news|metadata|byline|author|published|"
    r"\blabel\b|dateline|release-date",
    re.I,
)
BLOCK_TAGS = ["p", "li", "h2", "h3", "h4", "h5", "h6", "blockquote", "pre"]


def _norm(s):
    return re.sub(r"\s+", " ", (s or "").replace("\xa0", " ")).strip()


def _parse_date(text):
    if not text:
        return None
    m = DATE_RE.search(text)
    if not m:
        return None
    frag = re.sub(r"(\d)(st|nd|rd|th)\b", r"\1", m.group(0))
    try:
        return dateparser.parse(frag, dayfirst=True).strftime("%Y-%m-%d")
    except (ValueError, OverflowError, TypeError):
        return None


def _is_release_label(text):
    return _norm(text).lower().rstrip(":") in ("news release", "news releases", "media release", "press release")


# ---------------------------------------------------------------- listing

def _listing_items(soup, page_url):
    items = []
    seen = set()
    root = soup.find("main") or soup
    for lab in root.find_all(True, class_=re.compile(r"label|tag|type|category|badge", re.I)):
        if not _is_release_label(lab.get_text()):
            continue
        container = lab.parent
        link = None
        for _ in range(4):
            if container is None:
                break
            link = container.find("a", href=True)
            if link:
                break
            container = container.parent
        if not link:
            continue
        url = urldefrag(urljoin(page_url, link["href"]))[0]
        if url in seen:
            continue
        seen.add(url)
        dt = None
        dnode = container.find(class_=re.compile(r"date|time", re.I))
        if dnode and not SKIP_DATE_RE.search(dnode.get_text()):
            dt = _parse_date(dnode.get_text())
        else:
            t = container.find("time")
            if t:
                dt = _parse_date(t.get("datetime", "") or t.get_text())
        items.append((url, dt))
    if not items:
        # fallback: no labels present, use URL path
        for a in root.find_all("a", href=True):
            url = urldefrag(urljoin(page_url, a["href"]))[0]
            path = urlparse(url).path
            if re.search(r"/news-release/[^/]+", path) and url not in seen:
                seen.add(url)
                items.append((url, None))
    return items


def _next_pages(soup, page_url, listing_url):
    out = []
    base_path = urlparse(listing_url).path.rstrip("/")
    for a in soup.find_all("a", href=True):
        txt = _norm(a.get_text()).lower()
        rel = a.get("rel") or []
        if isinstance(rel, str):
            rel = [rel]
        in_pager = False
        for p in a.parents:
            if p.name in ("nav", "ul", "div", "li") and p.get("class") or p.get("aria-label"):
                sig = " ".join(p.get("class", [])) + " " + (p.get("aria-label") or "")
                if re.search(r"pagin|pager|page-nav", sig, re.I):
                    in_pager = True
                    break
        is_next = "next" in rel or re.match(r"^(next|older|more)\b", txt) or txt in ("›", "»", ">", "→")
        is_num = in_pager and re.fullmatch(r"\d+", txt)
        if not (is_next or is_num or (in_pager and txt)):
            continue
        url = urldefrag(urljoin(page_url, a["href"]))[0]
        u = urlparse(url)
        if u.netloc != urlparse(listing_url).netloc:
            continue
        if not u.path.rstrip("/").startswith(base_path):
            continue
        if "/news-release/" in u.path:
            continue
        out.append(url)
    for link in soup.find_all("link", href=True):
        rel = link.get("rel") or []
        if "next" in rel:
            out.append(urldefrag(urljoin(page_url, link["href"]))[0])
    return out


# ---------------------------------------------------------------- release

def _find_title(soup):
    main = soup.find("main") or soup
    h1 = main.find("h1") or soup.find("h1")
    if h1:
        t = _norm(h1.get_text(" "))
        if t:
            return t
    og = soup.find("meta", property="og:title")
    if og and og.get("content"):
        return _norm(og["content"])
    if soup.title:
        return _norm(re.split(r"\s+[|\u2013\u2014-]\s+(?=[^|]*$)", soup.title.get_text())[0])
    return None


def _jsonld(soup):
    for s in soup.find_all("script", type=re.compile("ld\\+json", re.I)):
        try:
            data = json.loads(s.string or s.get_text())
        except ValueError:
            continue
        stack = [data]
        while stack:
            d = stack.pop()
            if isinstance(d, list):
                stack.extend(d)
            elif isinstance(d, dict):
                if "@graph" in d:
                    stack.append(d["@graph"])
                yield d


def _find_date(soup):
    main = soup.find("main") or soup
    for el in main.find_all(True):
        if el.name in ("script", "style") or el.find(["p", "div", "ul"]):
            continue
        txt = _norm(el.get_text(" "))
        if not txt or len(txt) > 80:
            continue
        m = PUB_LABEL_RE.match(txt)
        if m and not SKIP_DATE_RE.search(txt.split(":")[0]):
            d = _parse_date(m.group(2))
            if d:
                return d
    for el in main.find_all(class_=re.compile(r"publish|posted|release-date|dateline", re.I)):
        txt = _norm(el.get_text(" "))
        if len(txt) < 80 and not SKIP_DATE_RE.search(txt):
            d = _parse_date(txt)
            if d:
                return d
    for d in _jsonld(soup):
        v = d.get("datePublished")
        if isinstance(v, str) and _parse_date(v):
            return _parse_date(v)
    for key in ("article:published_time", "datePublished", "og:published_time"):
        m = soup.find("meta", attrs={"property": key}) or soup.find("meta", attrs={"name": key}) \
            or soup.find("meta", attrs={"itemprop": key})
        if m and m.get("content") and _parse_date(m["content"]):
            return _parse_date(m["content"])
    t = main.find("time", attrs={"datetime": True})
    if t and not SKIP_DATE_RE.search(_norm(t.parent.get_text(" ")) if t.parent else ""):
        d = _parse_date(t["datetime"])
        if d:
            return d
    return None


TITLE_WORDS = re.compile(
    r"\b(chief|director|manager|head|officer|chair|chairman|chairperson|president|spokes\w*|"
    r"commissioner|secretary|executive|editor|analyst|adviser|advisor|press|media|communications)\b",
    re.I,
)


def _clean_names(text):
    text = _norm(text)
    text = re.sub(r"^\s*(written\s+)?by\b\s*:?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*[|•·]\s*.*$", "", text)
    names = []
    for part in re.split(r"\s+and\s+|\s*&\s*|;|\s*,\s*", text):
        part = _norm(part)
        part = re.sub(r"\s+[–—-]\s+.*$", "", part)
        if not part or TITLE_WORDS.search(part) or DATE_RE.search(part):
            continue
        if len(part) > 60:
            continue
        names.append(part)
    return names


def _find_author(soup):
    main = soup.find("main") or soup
    cands = []
    for el in main.find_all(True, attrs={"itemprop": "author"}):
        cands.append(el)
    for el in main.find_all(True, class_=re.compile(r"author|byline", re.I)):
        cands.append(el)
    for el in main.find_all("a", rel=True):
        if "author" in (el.get("rel") or []):
            cands.append(el)
    for el in cands:
        # prefer inner name element
        inner = el.find(True, class_=re.compile(r"name", re.I)) or el.find(attrs={"itemprop": "name"})
        txt = _norm((inner or el).get_text(" "))
        names = _clean_names(txt)
        if names:
            return " and ".join(dict.fromkeys(names))
    for el in main.find_all(["p", "div", "span"]):
        if el.find(["p", "div"]):
            continue
        txt = _norm(el.get_text(" "))
        if re.match(r"^by\s+[A-Z]", txt) and len(txt) < 120:
            names = _clean_names(txt)
            if names:
                return " and ".join(dict.fromkeys(names))
    for d in _jsonld(soup):
        a = d.get("author")
        if isinstance(a, dict):
            a = [a]
        if isinstance(a, list):
            nm = []
            for x in a:
                if isinstance(x, dict) and x.get("@type") in (None, "Person") and x.get("name"):
                    nm.extend(_clean_names(x["name"]))
            if nm:
                return " and ".join(dict.fromkeys(nm))
    return None


def _find_body(soup, title):
    main = soup.find("main") or soup.find("article") or soup.body or soup
    container = None
    for sel in (
        {"class_": re.compile(r"^(text|body|content|article-body|entry-content|release-body|rich-?text)$|release-text|article-text|post-content", re.I)},
    ):
        container = main.find(["div", "section", "article"], **sel)
    if container is None:
        container = main.find("article") or main
    container = BeautifulSoup(str(container), "html.parser")
    for t in container.find_all(["script", "style", "nav", "aside", "form", "footer", "header",
                                 "noscript", "button", "iframe", "svg", "select"]):
        t.decompose()
    for h in container.find_all("h1"):
        h.decompose()
    for t in container.find_all(True):
        if t.attrs is None:
            continue
        sig = " ".join(t.get("class", [])) + " " + (t.get("id") or "")
        if sig.strip() and NOISE_CLASS_RE.search(sig) and not re.fullmatch(r"\s*text\s*", sig):
            # do not delete the body wrapper itself
            if t.find_all(BLOCK_TAGS) and len(t.find_all("p")) > 3 and not re.search(r"share|related|about|contact|newsletter|cookie", sig, re.I):
                continue
            t.decompose()
    paras = []
    for el in container.find_all(BLOCK_TAGS):
        if el.find_parent(["blockquote", "li"]) and el.name != "li" and el.name != "blockquote":
            if el.find_parent(["blockquote", "li"]):
                continue
        if el.name == "li" and el.find_parent("li"):
            continue
        if el.name == "blockquote" and el.find(["p"]):
            continue
        txt = _norm(el.get_text(" "))
        txt = re.sub(r"\s+([,.;:!?])", r"\1", txt)
        if txt:
            paras.append((el.name, txt))
    out = []
    for name, txt in paras:
        if name in ("h2", "h3", "h4", "h5", "h6") and re.match(r"^(about|contact|media contact|related|share|notes to editors?|more information)\b", txt, re.I):
            break
        if re.match(r"^about the\b.{0,80}$", txt, re.I) and name != "p":
            break
        if re.match(r"^(share( this)?|related (links|news|articles)|tags?:|sign up|subscribe|media contact|for media (enquiries|inquiries))\b", txt, re.I):
            continue
        if txt == title:
            continue
        out.append(txt)
    return "\n\n".join(out)


def _parse_release(html, url, listing_date):
    soup = BeautifulSoup(html, "html.parser")
    title = _find_title(soup)
    if not title:
        return None
    date = _find_date(soup) or listing_date
    return {
        "url": url,
        "title": title,
        "date": date,
        "author": _find_author(soup),
        "body": _find_body(soup, title),
    }


# ---------------------------------------------------------------- entry

def extract(fetch, listing_url):
    items = []
    seen_items = set()
    seen_pages = set()
    queue = [listing_url]
    first = True
    while queue and len(seen_pages) < 200:
        page = queue.pop(0)
        key = page.rstrip("/")
        if key in seen_pages:
            continue
        seen_pages.add(key)
        try:
            html = fetch(page)
        except FetchError:
            if first:
                raise
            continue
        first = False
        soup = BeautifulSoup(html, "html.parser")
        for url, dt in _listing_items(soup, page):
            if url not in seen_items:
                seen_items.add(url)
                items.append((url, dt))
        for nxt in _next_pages(soup, page, listing_url):
            if nxt.rstrip("/") not in seen_pages:
                queue.append(nxt)

    records = []
    for url, ldate in items:
        try:
            html = fetch(url)
        except FetchError:
            continue
        rec = _parse_release(html, url, ldate)
        if rec:
            records.append(rec)

    indexed = list(enumerate(records))
    indexed.sort(key=lambda p: (p[1]["date"] or "", -p[0]), reverse=True)
    return [r for _, r in indexed]
