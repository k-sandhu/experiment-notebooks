import json
import re
from urllib.parse import urljoin, urlparse, urldefrag, parse_qs

from bs4 import BeautifulSoup
from dateutil import parser as dateparser

MONTHS = (r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|"
          r"Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)")
DATE_RE = re.compile(
    r"\b(\d{4}-\d{2}-\d{2}|\d{1,2}(?:st|nd|rd|th)?\s+" + MONTHS + r"\.?,?\s+\d{4}|"
    + MONTHS + r"\.?\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})\b", re.I)
BAD_DATE_CTX = re.compile(r"updat|revis|review|modif|amend|effective|clos|deadline|event", re.I)
NOISE_RE = re.compile(
    r"share|social|related|newsletter|subscribe|cookie|consent|breadcrumb|tags?$|tag-|"
    r"contact|about|notes|promo|sidebar|print|pagination|skip|banner|download|"
    r"read-more|more-news|back-to", re.I)
BLOCKS = ("p", "li", "h2", "h3", "h4", "h5", "h6", "blockquote", "pre", "td", "th")


def _clean(text):
    return re.sub(r"\s+", " ", text or "").strip()


def _soup(html):
    return BeautifulSoup(html, "html.parser")


def _parse_date(text):
    if not text:
        return None
    m = DATE_RE.search(text)
    if not m:
        return None
    s = re.sub(r"(\d)(st|nd|rd|th)\b", r"\1", m.group(1))
    try:
        return dateparser.parse(s, dayfirst=True).strftime("%Y-%m-%d")
    except (ValueError, OverflowError):
        return None


def _iso_date(value):
    if not value:
        return None
    value = value.strip()
    m = re.match(r"(\d{4}-\d{2}-\d{2})", value)
    if m:
        return m.group(1)
    return _parse_date(value)


# ---------------------------------------------------------------- listing

def _norm(url):
    return urldefrag(url)[0]


def _is_release_link(url, listing_url):
    lp = urlparse(listing_url)
    up = urlparse(url)
    if up.netloc != lp.netloc:
        return False
    base = lp.path.rstrip("/") + "/"
    if not up.path.startswith(base) or up.path.rstrip("/") == base.rstrip("/"):
        return False
    rest = [s for s in up.path[len(base):].split("/") if s]
    if not rest:
        return False
    if rest[0].lower() in ("archive", "page", "feed", "rss", "search"):
        return False
    if re.fullmatch(r"\d{4}", rest[-1]) or re.fullmatch(r"\d{4}/\d{2}", "/".join(rest)):
        return False  # year / month index
    if up.query and "page" in parse_qs(up.query):
        return False
    return True


def _page_links(soup, page_url, listing_url):
    lp = urlparse(listing_url)
    found = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith(("javascript:", "mailto:", "#")):
            continue
        url = _norm(urljoin(page_url, href))
        up = urlparse(url)
        if up.netloc != lp.netloc:
            continue
        rel = a.get("rel") or []
        txt = _clean(a.get_text()).lower()
        q = parse_qs(up.query)
        is_page = False
        if "next" in rel:
            is_page = True
        elif up.path.rstrip("/") == lp.path.rstrip("/") and any(
                k in q for k in ("page", "p", "pg", "offset", "start")):
            is_page = True
        elif re.search(r"/page/\d+/?$", up.path) and up.path.startswith(lp.path.rstrip("/")):
            is_page = True
        elif re.fullmatch(r"(next|next page|older|older posts|›|»|>|more)\s*[›»>]?", txt) \
                and up.path.rstrip("/") == lp.path.rstrip("/"):
            is_page = True
        if is_page and url != _norm(page_url):
            found.append(("page", url, a))
        elif _is_release_link(url, listing_url):
            found.append(("release", url, a))
    return found


def _row_date(a):
    node = a
    for _ in range(5):
        node = node.parent
        if node is None:
            break
        if node.name in ("tr", "li", "article", "div"):
            t = node.find("time")
            if t is not None:
                d = _iso_date(t.get("datetime")) or _parse_date(t.get_text(" "))
                if d:
                    return d
            d = _parse_date(node.get_text(" "))
            if d:
                return d
            if node.name in ("tr", "li", "article"):
                break
    return None


def _collect_listing(fetch, listing_url):
    releases = {}
    order = []
    seen_pages = set()
    queue = [_norm(listing_url)]
    first = True
    while queue and len(seen_pages) < 200:
        page = queue.pop(0)
        if page in seen_pages:
            continue
        seen_pages.add(page)
        try:
            html = fetch(page)
        except Exception:
            if first:
                raise
            continue
        first = False
        soup = _soup(html)
        root = soup.find("main") or soup
        for kind, url, a in _page_links(root, page, listing_url):
            if kind == "page":
                if url not in seen_pages and url not in queue:
                    queue.append(url)
            else:
                if url not in releases:
                    releases[url] = None
                    order.append(url)
                d = _row_date(a)
                if d and not releases[url]:
                    releases[url] = d
        # pagination links outside <main>
        if root is not soup:
            for kind, url, a in _page_links(soup, page, listing_url):
                if kind == "page" and url not in seen_pages and url not in queue:
                    queue.append(url)
    return order, releases


# ---------------------------------------------------------------- release page

def _json_ld(soup):
    items = []
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
                items.append(d)
                if "@graph" in d:
                    stack.append(d["@graph"])
    return items


def _title(soup, main):
    h = main.find("h1") or soup.find("h1")
    if h is not None:
        t = _clean(h.get_text())
        if t:
            return t
    og = soup.find("meta", property="og:title")
    if og and og.get("content"):
        return _clean(og["content"])
    if soup.title:
        return _clean(re.split(r"\s+[|\u2013\u2014-]\s+", soup.title.get_text())[0])
    return None


def _date(soup, main, fallback):
    for attrs in ({"property": "article:published_time"}, {"name": "article:published_time"},
                  {"itemprop": "datePublished"}, {"name": "DC.date.issued"},
                  {"name": "dcterms.issued"}, {"name": "date"}, {"name": "publish-date"},
                  {"property": "og:published_time"}):
        m = soup.find("meta", attrs=attrs)
        if m and m.get("content"):
            d = _iso_date(m["content"])
            if d:
                return d
    for item in _json_ld(soup):
        d = _iso_date(item.get("datePublished") if isinstance(item.get("datePublished"), str) else None)
        if d:
            return d
    # explicit "Published ..." text
    text = main.get_text("\n")
    for m in re.finditer(r"(?:first\s+)?(?:published|issued|release date|date published|posted)"
                         r"(?:\s+on)?\s*[:\-]?\s*([^\n]{0,60})", text, re.I):
        d = _parse_date(m.group(1))
        if d:
            return d
    for t in main.find_all("time"):
        ctx = " ".join([_clean(t.parent.get_text(" ")) if t.parent else "",
                        " ".join(t.get("class") or [])])
        if BAD_DATE_CTX.search(ctx) and not re.search(r"publish", ctx, re.I):
            continue
        d = _iso_date(t.get("datetime")) or _parse_date(t.get_text(" "))
        if d:
            return d
    for el in main.find_all(class_=re.compile(r"date|meta|publish|posted|byline", re.I)):
        t = _clean(el.get_text(" "))
        if BAD_DATE_CTX.search(t):
            continue
        d = _parse_date(t)
        if d:
            return d
    return fallback


def _split_names(s):
    s = _clean(s)
    s = re.sub(r"^(?:written\s+)?by\s*:?\s+", "", s, flags=re.I)
    s = re.split(r"\s+(?:on|\|)\s+|\s+[\u2013\u2014]\s+|\s+(?=\d{1,2}\s+" + MONTHS + r")", s)[0]
    parts = re.split(r"\s*(?:,|;|&|\band\b|\+)\s*", s)
    names = []
    title_words = re.compile(
        r"\b(governor|deputy|director|chief|head|officer|economist|manager|senior|analyst|"
        r"spokesperson|president|chair|chairman|adviser|advisor|secretary|editor|press|"
        r"communications|department|division|team)\b", re.I)
    for p in parts:
        p = p.strip(" .")
        if not p or title_words.search(p) and len(p.split()) > 3:
            continue
        if title_words.fullmatch(p) or re.match(r"^(?:the\s+)?(?:head|chief|deputy)\b", p, re.I):
            continue
        names.append(p)
    return names


def _author(soup, main):
    names = []
    for item in _json_ld(soup):
        a = item.get("author")
        for x in (a if isinstance(a, list) else [a]):
            if isinstance(x, dict) and x.get("@type", "Person") == "Person" and x.get("name"):
                names.append(_clean(x["name"]))
            elif isinstance(x, str):
                names.extend(_split_names(x))
    if names:
        return " and ".join(dict.fromkeys(names))
    for el in main.select('[rel="author"], [itemprop="author"], .byline, .author, '
                          '.article-author, .post-author, [class*="byline"], [class*="author"]'):
        sub = el.select('[itemprop="name"], .name, .author-name')
        if sub:
            cand = [_clean(s.get_text()) for s in sub]
        else:
            cand = _split_names(el.get_text(" "))
        names.extend(c for c in cand if c)
        if names:
            break
    if not names:
        for p in main.find_all(["p", "span", "div"]):
            t = _clean(p.get_text(" "))
            if len(t) < 120 and re.match(r"^(?:written\s+)?by\s+\S", t, re.I) and not p.find(["p", "div"]):
                names = _split_names(t)
                if names:
                    break
    if not names:
        m = soup.find("meta", attrs={"name": "author"})
        if m and m.get("content") and not re.search(r"bank of kestria", m["content"], re.I):
            names = _split_names(m["content"])
    names = list(dict.fromkeys(n for n in names if n))
    return " and ".join(names) if names else None


def _body_root(main):
    for sel in ("div.rte", '[itemprop="articleBody"]', ".article-body", ".article__body",
                ".release-body", ".press-release-body", ".content-body", ".body-text",
                ".entry-content", ".post-content", "article .content", "article"):
        el = main.select_one(sel)
        if el is not None and _clean(el.get_text()):
            return el
    return main


def _body(main, title):
    root = _body_root(main)
    for el in list(root.find_all(["script", "style", "noscript", "nav", "aside", "footer",
                                  "form", "button", "header", "iframe", "svg"])):
        el.decompose()
    for el in list(root.find_all(class_=NOISE_RE)):
        if el is not root and not el.decomposed if hasattr(el, "decomposed") else True:
            try:
                el.decompose()
            except Exception:
                pass
    if root is main:
        for el in list(root.select(".page-head, .meta, .kicker, h1, .byline, .date")):
            el.decompose()
    for br in root.find_all("br"):
        br.replace_with(" ")
    paras = []
    for el in root.find_all(BLOCKS):
        if el.find(BLOCKS):
            continue
        t = _clean(el.get_text())
        if not t:
            continue
        if title and t == title:
            continue
        paras.append(t)
    if not paras:
        t = _clean(root.get_text(" "))
        return t
    return "\n\n".join(paras)


def _parse_release(html, url, fallback_date):
    soup = _soup(html)
    main = soup.find("main") or soup.body or soup
    title = _title(soup, main)
    date = _date(soup, main, fallback_date)
    author = _author(soup, main)
    body = _body(main, title)
    return {"url": url, "title": title, "date": date, "author": author, "body": body}


def extract(fetch, listing_url):
    order, list_dates = _collect_listing(fetch, listing_url)
    records = []
    for url in order:
        try:
            html = fetch(url)
        except Exception:
            continue
        try:
            records.append(_parse_release(html, url, list_dates.get(url)))
        except Exception:
            continue
    indexed = list(enumerate(records))
    indexed.sort(key=lambda p: (p[1]["date"] or "", -p[0]), reverse=True)
    return [r for _, r in indexed]
