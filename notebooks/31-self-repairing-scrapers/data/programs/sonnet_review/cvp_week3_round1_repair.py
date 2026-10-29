import json
import re
from urllib.parse import urljoin, urlparse, urldefrag

from bs4 import BeautifulSoup
from dateutil import parser as dateparser

MONTHS = (r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|"
          r"Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)")
DATE_RES = [
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
    re.compile(r"\b" + MONTHS + r"\.?\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}\b", re.I),
    re.compile(r"\b\d{1,2}(?:st|nd|rd|th)?\s+" + MONTHS + r"\.?,?\s+\d{4}\b", re.I),
]
BAD_LABEL = re.compile(r"(updated|modified|reviewed|revised|effective|closing|closes|event)\W*$", re.I)
GOOD_LABEL = re.compile(r"(published|posted|released|date)\W*$", re.I)
TITLE_WORDS = re.compile(r"\b(officer|director|manager|head|president|chief|vice|vp|ceo|cfo|coo|cto|"
                         r"editor|spokes\w*|lead|communications|relations|analyst|counsel|founder|"
                         r"partner|executive|sales|marketing|press)\b", re.I)
JUNK_SEL = ("script, style, noscript, form, nav, aside, header, footer, button, iframe, svg, "
            ".share-bar, .share, .social, .newsletter-box, .newsletter, .related-posts, .related, "
            ".tags, .tag-list, .post-tags, .contact-box, .contact, .about, .about-us, .boilerplate, "
            ".cvp-cookie, .breadcrumb, .breadcrumbs, .post-meta, .byline, "
            "[class*=related], [class*=share], [class*=newsletter]")
LINK_LABEL = re.compile(r"^\s*(related(?:\s+(?:articles?|links?|posts?|stories|news|reading|releases?))?"
                        r"|see\s+also|read\s+more|read\s+also|further\s+reading|more\s+news|"
                        r"tags?|share|filed\s+under)\s*:\s*", re.I)


def _soup(html):
    return BeautifulSoup(html, "html.parser")


def _clean(text):
    return re.sub(r"\s+", " ", (text or "").replace("\xa0", " ")).strip()


def _norm_url(u):
    return urldefrag(u)[0]


def _path(u):
    return urlparse(u).path


def _is_page_link(url, listing_url):
    """True if url looks like pagination of the listing."""
    p = urlparse(url)
    lp = urlparse(listing_url)
    if p.netloc != lp.netloc:
        return False
    base = lp.path.rstrip("/") + "/"
    if p.path.rstrip("/") + "/" == base and re.search(r"(^|&)(page|p|paged)=\d+", p.query):
        return True
    rest = p.path[len(base):] if p.path.startswith(base) else None
    if rest is not None and re.fullmatch(r"(page/)?\d+/?", rest):
        return True
    return False


def _listing_links(soup, page_url, listing_url):
    lp = urlparse(listing_url)
    base = lp.path.rstrip("/") + "/"
    root = soup.find("main") or soup.body or soup
    links = []
    cards = root.select(".post-card a[href], article a[href]")
    anchors = cards if cards else root.find_all("a", href=True)
    for a in anchors:
        url = _norm_url(urljoin(page_url, a["href"]))
        p = urlparse(url)
        if p.netloc != lp.netloc or not p.path.startswith(base):
            continue
        if p.path.rstrip("/") + "/" == base or _is_page_link(url, listing_url):
            continue
        if url not in links:
            links.append(url)
    return links


def _next_pages(soup, page_url, listing_url):
    out = []
    for a in soup.find_all("a", href=True):
        url = _norm_url(urljoin(page_url, a["href"]))
        rel = a.get("rel") or []
        if "next" in rel or _is_page_link(url, listing_url):
            out.append(url)
    for l in soup.find_all("link", href=True):
        if "next" in (l.get("rel") or []):
            out.append(_norm_url(urljoin(page_url, l["href"])))
    return out


def _to_iso(s):
    try:
        return dateparser.parse(s, fuzzy=False).strftime("%Y-%m-%d")
    except (ValueError, OverflowError, TypeError):
        return None


def _iter_jsonld(soup):
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
                yield d
                stack.extend(v for v in d.values() if isinstance(v, (dict, list)))


def _date_from_text(text):
    cands = []
    for rx in DATE_RES:
        for m in rx.finditer(text):
            cands.append((m.start(), m.group(0), text[:m.start()]))
    cands.sort()
    good = [c for c in cands if GOOD_LABEL.search(c[2])]
    ok = [c for c in cands if not BAD_LABEL.search(c[2])]
    for c in good + ok:
        d = _to_iso(c[1])
        if d:
            return d
    return None


def _meta_node(art, soup):
    for sel in (".post-meta", ".byline", ".entry-meta", ".article-meta", ".meta", "[class*=meta]",
                "[class*=byline]"):
        n = (art or soup).select_one(sel)
        if n:
            return n
    return None


def _find_date(soup, art, meta):
    for d in _iter_jsonld(soup):
        v = d.get("datePublished")
        if isinstance(v, str) and _to_iso(v):
            return _to_iso(v)
    for name in ("article:published_time", "datePublished", "date", "DC.date.issued",
                 "og:published_time", "pubdate", "publish_date"):
        m = soup.find("meta", attrs={"property": name}) or soup.find("meta", attrs={"name": name}) \
            or soup.find("meta", attrs={"itemprop": name})
        if m and m.get("content") and _to_iso(m["content"]):
            return _to_iso(m["content"])
    scope = art or soup
    for t in scope.find_all("time"):
        label = _clean(t.parent.get_text(" ")) if t.parent else ""
        before = label.split(_clean(t.get_text()))[0] if _clean(t.get_text()) in label else ""
        if BAD_LABEL.search(before) or t.find_parent(class_=re.compile("updated|modified", re.I)):
            continue
        v = t.get("datetime") or t.get_text()
        if _to_iso(v):
            return _to_iso(v)
    if meta is not None:
        d = _date_from_text(_clean(meta.get_text(" ")))
        if d:
            return d
    return _date_from_text(_clean((art or soup).get_text(" "))[:600])


def _split_names(seg):
    seg = re.sub(r"^\s*(?:written\s+)?by\b[:\s]*", "", seg, flags=re.I)
    seg = re.sub(r"^\s*(?:authors?|posted by)\s*:\s*", "", seg, flags=re.I)
    names = []
    for part in re.split(r",|;|&|\band\b|\+", seg):
        part = _clean(part)
        if not part or TITLE_WORDS.search(part):
            continue
        names.append(part)
    return names


def _find_author(soup, art, meta):
    names = []
    if meta is not None:
        el = meta.select_one("[rel=author], .author, [itemprop=author], .byline-author")
        if el:
            names = _split_names(_clean(el.get_text(" ")))
        else:
            text = _clean(meta.get_text(" "))
            for seg in re.split(r"[·•|—–]", text):
                seg = seg.strip()
                if re.match(r"(written\s+)?by\b|authors?\s*:", seg, re.I):
                    for rx in DATE_RES:
                        seg = rx.sub("", seg)
                    names = _split_names(seg)
                    break
    if not names:
        for d in _iter_jsonld(soup):
            a = d.get("author")
            if a:
                for x in (a if isinstance(a, list) else [a]):
                    n = x.get("name") if isinstance(x, dict) else x
                    if isinstance(n, str) and n.strip():
                        names.append(_clean(n))
                if names:
                    break
    if not names:
        m = soup.find("meta", attrs={"name": "author"})
        if m and m.get("content"):
            names = _split_names(m["content"])
    seen = []
    for n in names:
        if n.lower() not in ("staff", "admin", "corvel packaging") and n not in seen:
            seen.append(n)
    return " and ".join(seen) if seen else None


BLOCKS = ["p", "h2", "h3", "h4", "h5", "h6", "li", "blockquote", "pre"]


def _is_link_para(el, text):
    """A 'Related: <link>' style paragraph: a label followed only by links."""
    m = LINK_LABEL.match(text)
    if not m:
        return False
    anchors = el.find_all("a")
    if not anchors:
        return False
    rest = text[m.end():]
    for a in anchors:
        rest = rest.replace(_clean(a.get_text(" ")), "", 1)
    return not re.search(r"\w", rest)


def _body(content):
    for j in content.select(JUNK_SEL):
        j.decompose()
    paras = []
    for el in content.find_all(BLOCKS):
        if any(p.name in BLOCKS for p in el.parents if p is not content and content in p.parents):
            continue
        for br in el.find_all("br"):
            br.replace_with(" ")
        t = _clean(el.get_text(" "))
        if _is_link_para(el, t):
            continue
        t = re.sub(r"\s+([,.;:!?%)])", r"\1", t)
        t = re.sub(r"([(])\s+", r"\1", t)
        if t:
            paras.append(t)
    if not paras:
        t = _clean(content.get_text(" "))
        if t:
            paras.append(t)
    while paras and re.match(r"^(about|media contact|contact|for more information)\b", paras[-1], re.I) \
            and len(paras) > 1:
        paras.pop()
    return "\n\n".join(paras)


def _parse_release(html, url):
    soup = _soup(html)
    art = soup.find("article") or soup.find("main") or soup.body or soup
    h1 = art.find("h1") or soup.find("h1")
    title = _clean(h1.get_text(" ")) if h1 else ""
    if not title:
        m = soup.find("meta", attrs={"property": "og:title"})
        title = _clean(m["content"]) if m and m.get("content") else _clean(
            (soup.title.get_text() if soup.title else "").split("|")[0])
    meta = _meta_node(art, soup)
    date = _find_date(soup, art, meta)
    author = _find_author(soup, art, meta)
    content = (art.select_one(".post-content, .entry-content, .article-body, .post-body, "
                              ".article-content, [itemprop=articleBody]")
               or art)
    if content is art and h1 is not None:
        h1.decompose()
    body = _body(content)
    return {"url": url, "title": title, "date": date, "author": author, "body": body}


def extract(fetch, listing_url):
    release_urls = []
    visited = set()
    queue = [_norm_url(listing_url)]
    while queue and len(visited) < 100:
        page = queue.pop(0)
        if page in visited:
            continue
        visited.add(page)
        try:
            html = fetch(page)
        except FetchError:
            if page == _norm_url(listing_url):
                raise
            continue
        soup = _soup(html)
        for u in _listing_links(soup, page, listing_url):
            if u not in release_urls:
                release_urls.append(u)
        for n in _next_pages(soup, page, listing_url):
            if n not in visited and n not in queue:
                queue.append(n)

    records = []
    for u in release_urls:
        try:
            html = fetch(u)
        except FetchError:
            continue
        rec = _parse_release(html, u)
        if rec["title"] and rec["date"]:
            records.append(rec)

    order = {r["url"]: i for i, r in enumerate(records)}
    records.sort(key=lambda r: (r["date"], -order[r["url"]]), reverse=True)
    return records
