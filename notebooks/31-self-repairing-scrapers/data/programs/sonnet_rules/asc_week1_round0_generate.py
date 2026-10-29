import json
import re
from urllib.parse import urljoin, urlparse, urldefrag

from bs4 import BeautifulSoup
from dateutil import parser as dateparser

try:
    FetchError
except NameError:  # pragma: no cover
    class FetchError(Exception):
        status = None

MAX_PAGES = 100

BLOCK_TAGS = ["p", "h2", "h3", "h4", "h5", "h6", "li", "blockquote", "pre", "dt", "dd", "figcaption"]
NOISE_RE = re.compile(
    r"(^|[\s_-])(share|sharing|social|related|newsletter|subscribe|cookie|consent|tags?|"
    r"contact|about|boilerplate|breadcrumbs?|feedback|byline|author|page-meta|meta|"
    r"pagination|sidebar|nav|menu|toc|print|promo|banner|footer|header|disclaimer|"
    r"notes-to-editors|media-contact|read-more|more-news|download)([\s_-]|$)",
    re.I,
)
TITLE_WORDS = re.compile(
    r"\b(director|head|manager|officer|chair|chairman|chairwoman|editor|secretary|analyst|counsel|"
    r"lead|president|vice|senior|principal|spokes\w*|adviser|advisor|partner|technical|communications|"
    r"policy|executive|member|professor|dr)\b",
    re.I,
)


def _clean(text):
    return re.sub(r"\s+", " ", (text or "").replace("\xa0", " ")).strip()


def _soup(html):
    try:
        return BeautifulSoup(html, "lxml")
    except Exception:
        return BeautifulSoup(html, "html.parser")


def _same_site(a, b):
    return urlparse(a).netloc.lower() == urlparse(b).netloc.lower()


def _norm(url):
    return urldefrag(url)[0]


# ---------------------------------------------------------------- listing

def _release_links(soup, page_url, listing_url):
    base_path = urlparse(listing_url).path
    if not base_path.endswith("/"):
        base_path = base_path.rsplit("/", 1)[0] + "/"
    found = []
    scope = soup.select(".news-card a[href]")
    if not scope:
        main = soup.find("main") or soup
        scope = main.find_all("a", href=True)
    for a in scope:
        href = a["href"].strip()
        if not href or href.startswith(("mailto:", "tel:", "javascript:")):
            continue
        url = _norm(urljoin(page_url, href))
        if not _same_site(url, listing_url):
            continue
        path = urlparse(url).path
        if path.startswith(base_path) and path != base_path and len(path) > len(base_path):
            rest = path[len(base_path):]
            if rest.startswith("page/") or re.fullmatch(r"(index|page-?\d+)(\.html?)?", rest):
                continue
            if not re.search(r"/(page|tag|category|archive)/", path) and "page=" not in url:
                found.append(url)
    return found


def _next_pages(soup, page_url, listing_url):
    out = []
    for el in soup.select("a[rel~=next][href], link[rel~=next][href]"):
        out.append(el["href"])
    for a in soup.find_all("a", href=True):
        label = _clean(a.get_text()) + " " + (a.get("aria-label") or "") + " " + " ".join(a.get("class") or [])
        if re.search(r"\b(next|older)\b|^[›»>]+|[›»]\s*$", label.strip(), re.I) and "prev" not in label.lower():
            out.append(a["href"])
    for cont in soup.select(".pagination, .pager, nav[aria-label*=agination], [class*=pagination]"):
        for a in cont.find_all("a", href=True):
            out.append(a["href"])
    res = []
    for h in out:
        if h.startswith(("mailto:", "javascript:", "#")):
            continue
        u = _norm(urljoin(page_url, h))
        if _same_site(u, listing_url):
            res.append(u)
    return res


# ---------------------------------------------------------------- release page

def _ld_objects(soup):
    objs = []

    def walk(o):
        if isinstance(o, list):
            for i in o:
                walk(i)
        elif isinstance(o, dict):
            objs.append(o)
            for v in o.get("@graph", []) if isinstance(o.get("@graph"), list) else []:
                walk(v)

    for s in soup.find_all("script", type=re.compile("ld\\+json", re.I)):
        try:
            walk(json.loads(s.string or s.get_text()))
        except Exception:
            continue
    return objs


def _meta(soup, *names):
    for n in names:
        el = soup.find("meta", attrs={"property": n}) or soup.find("meta", attrs={"name": n}) \
            or soup.find("meta", attrs={"itemprop": n})
        if el and el.get("content"):
            return el["content"].strip()
    return None


def _to_date(s):
    if not s:
        return None
    s = s.strip()
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return "%s-%s-%s" % m.groups()
    try:
        return dateparser.parse(s, dayfirst=True).strftime("%Y-%m-%d")
    except Exception:
        return None


def _find_date(soup, ld):
    for o in ld:
        d = _to_date(o.get("datePublished") if isinstance(o.get("datePublished"), str) else None)
        if d:
            return d
    d = _to_date(_meta(soup, "article:published_time", "datePublished", "date", "DC.date.issued",
                       "og:published_time", "publish_date", "pubdate"))
    if d:
        return d
    el = soup.find(attrs={"itemprop": "datePublished"})
    if el:
        d = _to_date(el.get("content") or el.get("datetime") or el.get_text())
        if d:
            return d
    for t in soup.find_all("time"):
        ctx = " ".join(
            [" ".join(t.get("class") or []), t.get("itemprop") or "", _clean(t.parent.get_text())[:80] if t.parent else ""]
        ).lower()
        if re.search(r"modif|updated|review|effective|closing", ctx):
            continue
        d = _to_date(t.get("datetime") or t.get_text())
        if d:
            return d
    text = _clean((soup.find("main") or soup).get_text(" "))
    m = re.search(r"(?:published|posted|issued|released|date)[:\s]+(\d{1,2}\s+\w+\s+\d{4}|\w+\s+\d{1,2},?\s+\d{4}|\d{4}-\d{2}-\d{2})",
                  text, re.I)
    if m:
        return _to_date(m.group(1))
    return None


def _split_names(text):
    text = _clean(text)
    text = re.sub(r"^(written\s+)?by[:\s]+", "", text, flags=re.I)
    text = re.split(r"\s+[|·•]\s+|\s+-\s+|\s+—\s+|\s+–\s+", text)[0]
    parts = re.split(r",|\s+and\s+|\s*&\s*|;", text)
    names = []
    for p in parts:
        p = _clean(p)
        if not p or TITLE_WORDS.search(p):
            continue
        p = re.sub(r"^by\s+", "", p, flags=re.I)
        if p and p not in names:
            names.append(p)
    return names


def _ld_author_names(a):
    names = []
    if isinstance(a, list):
        for i in a:
            names += _ld_author_names(i)
    elif isinstance(a, dict):
        t = a.get("@type")
        if t and "organization" in str(t).lower():
            return []
        n = a.get("name")
        if isinstance(n, str) and n.strip():
            names.append(_clean(n))
    elif isinstance(a, str) and a.strip():
        names += _split_names(a)
    return names


def _find_author(soup, ld):
    names = []
    for o in ld:
        if "author" in o:
            names = _ld_author_names(o["author"])
            if names:
                break
    if not names:
        m = _meta(soup, "author", "article:author", "DC.creator")
        if m and not m.startswith("http"):
            names = _split_names(m)
    if not names:
        for el in soup.select("[rel=author], [itemprop=author], .byline, .author, .post-author, .article-author"):
            sub = el.select_one("[itemprop=name]")
            txt = _clean((sub or el).get_text(" "))
            txt = re.sub(r"^(authors?|written)\s*:\s*", "", txt, flags=re.I)
            names = _split_names(txt)
            if names:
                break
    seen = []
    for n in names:
        if n and n not in seen and n.lower() not in ("admin", "staff", "editor"):
            seen.append(n)
    return " and ".join(seen) if seen else None


def _find_title(soup, ld):
    root = soup.find("article") or soup.find("main") or soup
    h1 = root.find("h1") or soup.find("h1")
    if h1 and _clean(h1.get_text()):
        return _clean(h1.get_text(" "))
    for o in ld:
        if isinstance(o.get("headline"), str) and o["headline"].strip():
            return _clean(o["headline"])
    m = _meta(soup, "og:title", "twitter:title")
    if m:
        return _clean(m)
    if soup.title:
        return _clean(re.split(r"\s+[|–—]\s+", soup.title.get_text())[0])
    return ""


def _find_body(soup, title):
    container = None
    for sel in ["[itemprop=articleBody]", ".prose", ".article-body", ".entry-content", ".post-content",
                ".release-body", ".news-body", ".content-body", "article", "main"]:
        container = soup.select_one(sel)
        if container:
            break
    if container is None:
        container = soup.body or soup
    for t in container.find_all(["script", "style", "noscript", "nav", "aside", "form", "button",
                                 "header", "footer", "iframe", "svg"]):
        t.decompose()
    for h1 in container.find_all("h1"):
        h1.decompose()
    for el in list(container.find_all(True)):
        if el.decomposed if hasattr(el, "decomposed") else False:
            continue
        if el is container:
            continue
        ident = " ".join((el.get("class") or []) + [el.get("id") or ""])
        if ident.strip() and NOISE_RE.search(ident) and "prose" not in ident and "body" not in ident.lower().split():
            el.decompose()
    for br in container.find_all("br"):
        br.replace_with(" ")
    blocks = container.find_all(BLOCK_TAGS)
    paras = []
    for b in blocks:
        if b.find(BLOCK_TAGS):
            continue
        txt = _clean(b.get_text())
        if txt:
            paras.append(txt)
    if not paras:
        txt = _clean(container.get_text(" "))
        paras = [txt] if txt else []
    paras = [p for p in paras if p != title]
    paras = [p for p in paras if not re.match(r"^about\s+(the\s+)?(accounting standards council|asck|us)\b", p, re.I)]
    return "\n\n".join(paras)


def _parse_release(html, url):
    soup = _soup(html)
    ld = [o for o in _ld_objects(soup)
          if any(k in o for k in ("headline", "datePublished", "author"))]
    title = _find_title(soup, ld)
    date = _find_date(soup, ld)
    author = _find_author(soup, ld)
    body = _find_body(soup, title)
    return {"url": url, "title": title, "date": date, "author": author, "body": body}


# ---------------------------------------------------------------- main

def extract(fetch, listing_url):
    queue = [_norm(listing_url)]
    visited = set()
    urls = []
    while queue and len(visited) < MAX_PAGES:
        page = queue.pop(0)
        if page in visited:
            continue
        visited.add(page)
        try:
            html = fetch(page)
        except FetchError:
            if page == _norm(listing_url):
                raise
            continue
        soup = _soup(html)
        for u in _release_links(soup, page, listing_url):
            if u not in urls:
                urls.append(u)
        for n in _next_pages(soup, page, listing_url):
            if n not in visited and n not in queue:
                queue.append(n)

    records = []
    for u in urls:
        try:
            html = fetch(u)
        except FetchError:
            continue
        try:
            rec = _parse_release(html, u)
        except Exception:
            continue
        records.append(rec)

    order = {r["url"]: i for i, r in enumerate(records)}
    records.sort(key=lambda r: (r["date"] or "", -order[r["url"]]), reverse=True)
    return records
