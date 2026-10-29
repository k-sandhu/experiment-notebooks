import json
import re
from urllib.parse import urljoin, urlparse, parse_qs

from bs4 import BeautifulSoup
from dateutil import parser as dateparser

MONTH_RE = re.compile(
    r"\b(January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+(\d{4})\b", re.I)
NOISE_RE = re.compile(
    r"share|social|related|newsletter|subscribe|cookie|breadcrumb|tags?\b|contact|"
    r"about|boilerplate|sidebar|promo|print|byline|author|dateline|meta|back-to|"
    r"pagination|comment", re.I)
TITLE_WORDS = re.compile(
    r"\b(head|director|chief|officer|manager|executive|chair|chairman|chairperson|"
    r"spokesperson|spokesman|editor|correspondent|adviser|advisor|analyst|lead|"
    r"senior|deputy|press|communications|policy|ceo|cfo|coo|head of|secretary|"
    r"professor|dr|team|office|department)\b", re.I)


def _soup(html):
    return BeautifulSoup(html, "html.parser")


def _text(el):
    return re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip()


def _clean_inline(s):
    s = re.sub(r"\s+([,.;:!?])", r"\1", s)
    return re.sub(r"\s+", " ", s).strip()


def _parse_date(s):
    try:
        return dateparser.parse(s, fuzzy=True, default=None).strftime("%Y-%m-%d")
    except Exception:
        return None


# ---------------------------------------------------------------- listing

def _is_release_link(href, listing_url):
    p = urlparse(href)
    lp = urlparse(listing_url)
    if p.netloc != lp.netloc:
        return False
    base = lp.path.rstrip("/")
    path = p.path
    if not path.startswith(base + "/"):
        return False
    slug = path[len(base) + 1:].strip("/")
    if not slug or "/" in slug and re.match(r"^(page/)?\d+$", slug):
        return False
    if re.match(r"^(page/\d+|\d+)$", slug):
        return False
    return True


def _next_pages(soup, page_url, listing_url):
    out = []
    lp = urlparse(listing_url)
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith("#") or href.lower().startswith(("javascript:", "mailto:")):
            continue
        absu = urljoin(page_url, href)
        p = urlparse(absu)
        if p.netloc != lp.netloc:
            continue
        txt = _text(a).lower()
        rel = a.get("rel") or []
        is_page = False
        if "next" in rel:
            is_page = True
        elif re.search(r"\b(next|older|more)\b|[›»>]", txt) and p.path.rstrip("/").startswith(lp.path.rstrip("/")):
            is_page = True
        elif "page" in parse_qs(p.query) and p.path.rstrip("/") == lp.path.rstrip("/"):
            is_page = True
        elif re.match(r"^" + re.escape(lp.path.rstrip("/")) + r"/page/\d+/?$", p.path):
            is_page = True
        if is_page:
            out.append(absu.split("#")[0])
    return out


def _parse_listing(html, page_url, listing_url):
    soup = _soup(html)
    root = soup.find("main") or soup.body or soup
    items = []
    cur_month = None
    cur_year = None
    for el in root.descendants:
        name = getattr(el, "name", None)
        if name in ("h2", "h3", "h4"):
            m = MONTH_RE.search(_text(el))
            if m:
                cur_month, cur_year = m.group(1), m.group(2)
        elif name == "a" and el.get("href"):
            href = urljoin(page_url, el["href"].strip()).split("#")[0]
            if not _is_release_link(href, listing_url):
                continue
            title = _text(el)
            if not title:
                continue
            container = el.find_parent(["li", "article", "tr", "div"]) or el.parent
            date = None
            t = container.find("time") if container else None
            if t is not None:
                date = _parse_date(t.get("datetime") or _text(t))
            if not date and container is not None:
                d = container.find(class_=re.compile(r"day|date", re.I))
                dtxt = _text(d) if d else ""
                if re.fullmatch(r"\d{1,2}", dtxt) and cur_month:
                    date = _parse_date("%s %s %s" % (dtxt, cur_month, cur_year))
                elif dtxt:
                    date = _parse_date(dtxt)
            if not date and container is not None and cur_month:
                m = re.match(r"\s*(\d{1,2})\b", _text(container))
                if m:
                    date = _parse_date("%s %s %s" % (m.group(1), cur_month, cur_year))
            items.append({"url": href, "title": title, "date": date})
    return soup, items


# ---------------------------------------------------------------- release

def _page_date(soup):
    for sc in soup.find_all("script", type=re.compile("ld\\+json", re.I)):
        try:
            data = json.loads(sc.string or sc.get_text())
        except Exception:
            continue
        stack = [data]
        while stack:
            d = stack.pop()
            if isinstance(d, dict):
                if d.get("datePublished"):
                    r = _parse_date(str(d["datePublished"]))
                    if r:
                        return r
                stack.extend(d.values())
            elif isinstance(d, list):
                stack.extend(d)
    for key in ("article:published_time", "datePublished", "date", "DC.date.issued",
                "dcterms.created", "publishdate", "pubdate"):
        m = soup.find("meta", attrs={"property": key}) or soup.find("meta", attrs={"name": key}) \
            or soup.find("meta", attrs={"itemprop": key})
        if m and m.get("content"):
            r = _parse_date(m["content"])
            if r:
                return r
    for t in soup.find_all("time"):
        ctx = " ".join(filter(None, [_text(t.parent) if t.parent else "",
                                     " ".join(t.get("class") or [])])).lower()
        if re.search(r"updated|modified|reviewed", ctx):
            continue
        v = t.get("datetime") or _text(t)
        r = _parse_date(v)
        if r:
            return r
    main = soup.find("main") or soup
    for el in main.find_all(["p", "span", "div", "li"]):
        txt = _text(el)
        if len(txt) < 80:
            m = re.match(r"(?:first\s+)?(?:published|date|released|posted)(?: on)?\s*:?\s*(.+)$", txt, re.I)
            if m:
                r = _parse_date(m.group(1))
                if r:
                    return r
    return None


def _split_authors(s):
    s = re.sub(r"^\s*(written|words|posted|text|story|report(?:ed)?|article)?\s*by\s*:?\s*", "", s, flags=re.I)
    s = re.sub(r"\s*[|·•]\s*.*$", "", s) if re.search(r"[|·•]", s) else s
    parts = re.split(r"\s+and\s+|\s*&\s*|;|\s*,\s*", s)
    names = []
    for p in parts:
        p = re.split(r"\s+[–—-]\s+", p)[0].strip(" .")
        if not p or TITLE_WORDS.search(p):
            continue
        if re.search(r"\d", p) or len(p.split()) > 5:
            continue
        names.append(p)
    return names


def _find_author(soup, root):
    m = soup.find("meta", attrs={"name": "author"}) or soup.find("meta", attrs={"property": "article:author"})
    cands = []
    for el in (root or soup).find_all(True, class_=re.compile(r"author|byline", re.I)):
        if el.find(True, class_=re.compile(r"author|byline", re.I)) is not None and not el.find("a", rel="author"):
            continue
        cands.append(el)
    for el in cands:
        txt = _text(el)
        if txt and len(txt) < 150:
            names = _split_authors(txt)
            if names:
                return names, el
    for el in (root or soup).find_all(["p", "div", "span"]):
        txt = _text(el)
        if len(txt) < 120 and re.match(r"^(written |words |posted )?by\s+\S", txt, re.I):
            names = _split_authors(txt)
            if names:
                return names, el
    if m and m.get("content"):
        names = _split_authors(m["content"])
        if names:
            return names, None
    return [], None


BLOCKS = ["p", "h2", "h3", "h4", "h5", "h6", "li", "blockquote", "pre"]


def _body(soup, title_el, author_el):
    root = (soup.select_one(".article-text, .article-body, .release-body, .entry-content, "
                            "[itemprop=articleBody], .content-body")
            or soup.find("article") or soup.find("main") or soup.body)
    root = BeautifulSoup(str(root), "html.parser")
    for t in root.find_all(["script", "style", "nav", "aside", "form", "header", "footer",
                            "noscript", "button", "iframe", "svg"]):
        t.decompose()
    for t in root.find_all(True):
        if t.decomposed if hasattr(t, "decomposed") else False:
            continue
        cls = " ".join((t.get("class") or []) + [t.get("id") or ""])
        if cls.strip() and NOISE_RE.search(cls) and t.name not in ("html", "body", "[document]"):
            if t.parent is not None and not re.search(r"article-text|article-body|entry-content", cls):
                t.decompose()
    for h in root.find_all("h1"):
        h.decompose()
    paras = []
    for el in root.find_all(BLOCKS):
        if el.find(BLOCKS):
            continue
        txt = _clean_inline(_text(el))
        if not txt:
            continue
        if re.match(r"^(share this|follow us|subscribe|sign up|tags?:|related|read more|"
                    r"media enquiries|for more information,? contact|notes to editors?$)", txt, re.I):
            continue
        if re.match(r"^about (the )?(pensions oversight authority|us)\b", txt, re.I):
            continue
        if re.match(r"^(written |words )?by\s+[A-Z]", txt) and len(txt) < 100 and _split_authors(txt):
            continue
        if re.match(r"^(published|last updated|updated|date)\s*:", txt, re.I) and len(txt) < 60:
            continue
        paras.append(txt)
    return "\n\n".join(paras)


def _parse_release(html):
    soup = _soup(html)
    main = soup.find("main") or soup.find("article") or soup.body or soup
    h1 = main.find("h1") or soup.find("h1")
    title = _text(h1) if h1 else None
    if not title:
        og = soup.find("meta", attrs={"property": "og:title"})
        if og and og.get("content"):
            title = og["content"].strip()
        elif soup.title:
            title = re.split(r"\s+[|–—]\s+", _text(soup.title))[0]
    names, author_el = _find_author(soup, main)
    date = _page_date(soup)
    body = _body(soup, h1, author_el)
    author = " and ".join(dict.fromkeys(names)) if names else None
    return {"title": title, "date": date, "author": author, "body": body}


# ---------------------------------------------------------------- entry

def extract(fetch, listing_url):
    items = []
    seen_pages = set()
    queue = [listing_url]
    seen_urls = set()
    while queue and len(seen_pages) < 100:
        page = queue.pop(0)
        if page in seen_pages:
            continue
        seen_pages.add(page)
        try:
            html = fetch(page)
        except FetchError:
            if page == listing_url:
                raise
            continue
        soup, found = _parse_listing(html, page, listing_url)
        for it in found:
            if it["url"] not in seen_urls:
                seen_urls.add(it["url"])
                items.append(it)
        for n in _next_pages(soup, page, listing_url):
            if n not in seen_pages and n not in queue:
                queue.append(n)

    records = []
    for it in items:
        try:
            rel = _parse_release(fetch(it["url"]))
        except FetchError:
            continue
        records.append({
            "url": it["url"],
            "title": rel["title"] or it["title"],
            "date": rel["date"] or it["date"],
            "author": rel["author"],
            "body": rel["body"],
        })
    order = {id(r): i for i, r in enumerate(records)}
    records.sort(key=lambda r: (r["date"] or "", -order[id(r)]), reverse=True)
    return records
