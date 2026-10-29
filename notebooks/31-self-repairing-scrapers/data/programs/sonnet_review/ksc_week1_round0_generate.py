import json
import re
from urllib.parse import urljoin, urlparse, urldefrag

from bs4 import BeautifulSoup
from dateutil import parser as dateparser

_BLOCK_TAGS = ["p", "h2", "h3", "h4", "h5", "h6", "li", "blockquote", "pre", "figcaption"]
_NOISE_TAGS = ["script", "style", "noscript", "nav", "aside", "form", "header", "footer",
               "button", "iframe", "svg", "select"]
_NOISE_RE = re.compile(
    r"share|social|newsletter|subscribe|related|cookie|consent|breadcrumb|\btags?\b|"
    r"contact|about-us|about_us|boilerplate|print|sidebar|promo|signup|sign-up|"
    r"pagination|skip|back-to|download",
    re.I)
_TITLE_WORDS = re.compile(
    r"\b(director|head|officer|manager|chief|counsel|analyst|editor|spokesperson|"
    r"spokesman|commissioner|secretary|lead|senior|adviser|advisor|press|communications|"
    r"team|office|department|division|president|chair|chairman|chairperson|executive|"
    r"deputy|assistant|general|specialist|coordinator|writer|reporter)\b", re.I)
_DATE_RE = re.compile(
    r"\b(\d{1,2}\s+[A-Za-z]{3,9}\.?\s+\d{4}|[A-Za-z]{3,9}\.?\s+\d{1,2},?\s+\d{4}|\d{4}-\d{2}-\d{2})\b")


def _ws(text):
    return re.sub(r"\s+", " ", text or "").strip()


def _parse_date(text):
    if not text:
        return None
    text = _ws(text)
    m = re.match(r"^\d{4}-\d{2}-\d{2}", text)
    if m:
        return m.group(0)
    m = _DATE_RE.search(text)
    candidate = m.group(0) if m else text
    try:
        return dateparser.parse(candidate, dayfirst=True, fuzzy=True).strftime("%Y-%m-%d")
    except (ValueError, OverflowError, TypeError):
        return None


def _in_noise(tag):
    for p in tag.parents:
        if getattr(p, "name", None) in ("nav", "header", "footer", "aside"):
            return True
    return False


def _is_pagination(a):
    if "next" in (a.get("rel") or []):
        return True
    for p in a.parents:
        cls = " ".join(p.get("class") or []) + " " + (p.get("id") or "") if hasattr(p, "get") else ""
        if re.search(r"pagina|pager|page-nav|paging", cls, re.I):
            return True
    return False


def _listing_page(html, page_url, listing_url):
    soup = BeautifulSoup(html, "html.parser")
    root = soup.find("main") or soup.body or soup
    base_path = urlparse(listing_url).path.rstrip("/") + "/"
    items, pages = [], []
    for a in root.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(("mailto:", "javascript:", "tel:")):
            continue
        url = urldefrag(urljoin(page_url, href))[0]
        parsed = urlparse(url)
        if _is_pagination(a) or re.fullmatch(
                r"(next|next page|older|more|load more|›|»|>|\d{1,3})", _ws(a.get_text()), re.I):
            if parsed.netloc == urlparse(listing_url).netloc and \
                    parsed.path.rstrip("/") == base_path.rstrip("/"):
                pages.append(url)
                continue
            if "page" in parsed.query.lower() or "next" in (a.get("rel") or []):
                pages.append(url)
                continue
        if _in_noise(a):
            continue
        if parsed.netloc != urlparse(listing_url).netloc:
            continue
        if not parsed.path.startswith(base_path) or parsed.path.rstrip("/") + "/" == base_path:
            continue
        if re.search(r"(^|&)(page|p)=", parsed.query):
            continue
        # listing date fallback
        container = a.find_parent("article") or a.find_parent("li") or a.parent
        ldate = _parse_date(container.get_text(" ")) if container else None
        items.append((url, ldate))
    return items, pages


def _meta_content(soup, *names):
    for n in names:
        t = soup.find("meta", attrs={"property": n}) or soup.find("meta", attrs={"name": n})
        if t and t.get("content"):
            return t["content"].strip()
    return None


def _jsonld(soup):
    out = []
    for s in soup.find_all("script", type=re.compile("ld\\+json", re.I)):
        try:
            data = json.loads(s.string or s.get_text())
        except (ValueError, TypeError):
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


def _meta_pairs(root):
    pairs = {}
    for dt in root.find_all("dt"):
        dd = dt.find_next_sibling("dd")
        if dd is not None:
            pairs.setdefault(_ws(dt.get_text()).lower().rstrip(":"), dd)
    return pairs


def _clean_authors(raw):
    raw = _ws(raw)
    raw = re.sub(r"^(written\s+)?by\s*:?\s+", "", raw, flags=re.I)
    raw = re.sub(r"\([^)]*\)", "", raw)
    parts = re.split(r"\s*(?:,|;|&|\band\b|\|)\s*", raw)
    names = []
    for p in parts:
        p = re.split(r"\s+[–—-]\s+", p)[0]
        p = re.sub(r"^by\s+", "", _ws(p), flags=re.I)
        if not p or _TITLE_WORDS.search(p):
            continue
        if p not in names:
            names.append(p)
    return " and ".join(names) if names else None


def _find_author(soup, root, pairs):
    for key in ("author", "authors", "written by", "by", "byline"):
        if key in pairs:
            return _clean_authors(pairs[key].get_text(" "))
    el = root.find(attrs={"rel": "author"}) or root.find(class_=re.compile(r"byline|author", re.I))
    if el is not None and not el.find(["p", "div"]):
        txt = _ws(el.get_text(" "))
        txt = re.sub(r"^authors?\s*:?\s*", "", txt, flags=re.I)
        if txt:
            return _clean_authors(txt)
    for d in _jsonld(soup):
        a = d.get("author")
        if a:
            lst = a if isinstance(a, list) else [a]
            names = []
            for x in lst:
                n = x.get("name") if isinstance(x, dict) else x
                if isinstance(n, str) and n.strip():
                    names.append(_ws(n))
            if names:
                return _clean_authors(" and ".join(names))
    m = _meta_content(soup, "author", "article:author")
    if m and not m.startswith("http"):
        return _clean_authors(m)
    return None


def _find_date(soup, root, pairs):
    for key in ("published", "date published", "published on", "publication date",
                "release date", "date", "first published", "issued"):
        if key in pairs:
            d = _parse_date(pairs[key].get_text(" "))
            if d:
                return d
    d = _parse_date(_meta_content(soup, "article:published_time", "datePublished",
                                  "date", "dcterms.created", "DC.date.issued", "og:published_time"))
    if d:
        return d
    for dd in _jsonld(soup):
        d = _parse_date(dd.get("datePublished"))
        if d:
            return d
    for t in root.find_all("time"):
        ctx = _ws((t.parent.get_text(" ") if t.parent else "")).lower()
        if "updated" in ctx or "modified" in ctx or "reviewed" in ctx:
            continue
        d = _parse_date(t.get("datetime") or t.get_text())
        if d:
            return d
    m = re.search(r"(?:published|posted|released)\s*(?:on)?\s*:?\s*" + _DATE_RE.pattern,
                  root.get_text(" "), re.I)
    if m:
        return _parse_date(m.group(0))
    return None


def _find_title(soup, root):
    h = root.find("h1") or soup.find("h1")
    if h and _ws(h.get_text()):
        return _ws(h.get_text(" "))
    t = _meta_content(soup, "og:title")
    if t:
        return _ws(t)
    if soup.title:
        return _ws(re.split(r"\s+[|–—]\s+", soup.title.get_text())[0])
    return None


def _body_container(root):
    for sel in (lambda r: r.find(class_=re.compile(r"^(body|article-body|entry-content|post-content|"
                                                  r"release-body|news-body|content-body)$", re.I)),
                lambda r: r.find(attrs={"itemprop": "articleBody"}),
                lambda r: r.find("article"),
                lambda r: r.find(class_=re.compile(r"body|content|text", re.I))):
        el = sel(root)
        if el is not None:
            return el
    return root


def _extract_body(root):
    container = _body_container(root)
    # work on a copy-free basis: decompose noise inside container
    for t in container.find_all(_NOISE_TAGS):
        t.decompose()
    for el in list(container.find_all(True)):
        if el.decomposed if hasattr(el, "decomposed") else False:
            continue
        cls = " ".join(el.get("class") or []) + " " + (el.get("id") or "")
        if cls.strip() and _NOISE_RE.search(cls):
            el.decompose()
    for h in container.find_all(["h1"]):
        h.decompose()
    paras = []
    for el in container.find_all(_BLOCK_TAGS):
        if el.find(_BLOCK_TAGS):
            continue
        text = _ws(el.get_text(" "))
        text = re.sub(r"\s+([,.;:!?)])", r"\1", text)
        text = re.sub(r"\(\s+", "(", text)
        if not text:
            continue
        if el.name in ("h2", "h3", "h4", "h5", "h6") and re.match(r"^about\b", text, re.I):
            break
        if re.match(r"^(about (us|the (commission|ksc|kestria)))\b", text, re.I) and len(text) < 60:
            break
        if re.match(r"^(media contact|contact:|for more information|share this|tags?:|"
                    r"related (news|links)|subscribe)", text, re.I):
            continue
        paras.append(text)
    if not paras:
        text = container.get_text("\n")
        paras = [_ws(x) for x in re.split(r"\n\s*\n", text) if _ws(x)]
    return "\n\n".join(paras)


def _parse_release(html, url):
    soup = BeautifulSoup(html, "html.parser")
    full_soup = BeautifulSoup(html, "html.parser")
    root = soup.find("main") or soup.body or soup
    title = _find_title(full_soup, root)
    pairs = _meta_pairs(root)
    date = _find_date(full_soup, root, pairs)
    author = _find_author(full_soup, root, pairs)
    body = _extract_body(root)
    return {"url": url, "title": title, "date": date, "author": author, "body": body}


def extract(fetch, listing_url):
    queue = [listing_url]
    seen_pages = set()
    found = {}
    order = []
    while queue and len(seen_pages) < 200:
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
        items, pages = _listing_page(html, page, listing_url)
        for url, ldate in items:
            if url not in found:
                found[url] = ldate
                order.append(url)
        for p in pages:
            if p not in seen_pages and p not in queue:
                queue.append(p)

    records = []
    for idx, url in enumerate(order):
        try:
            html = fetch(url)
        except FetchError:
            continue
        rec = _parse_release(html, url)
        if not rec["date"]:
            rec["date"] = found[url]
        if not rec["title"]:
            continue
        records.append((rec, idx))
    records.sort(key=lambda r: (r[0]["date"] or "", -r[1]), reverse=True)
    return [r for r, _ in records]
