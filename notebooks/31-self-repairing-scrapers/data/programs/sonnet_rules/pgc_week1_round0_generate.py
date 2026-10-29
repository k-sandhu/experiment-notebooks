import json
import re
from urllib.parse import urljoin, urlparse, urldefrag

from bs4 import BeautifulSoup
from dateutil import parser as dateparser

MONTHS = (r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|"
          r"Aug(?:ust)?|Sept?(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)")
DATE_MDY = re.compile(r"\b(" + MONTHS + r")\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})\b", re.I)
DATE_DMY = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(" + MONTHS + r")\.?,?\s+(\d{4})\b", re.I)
URL_DATE = re.compile(r"(?<!\d)(20\d{2})(\d{2})(\d{2})(?!\d)")

NOISE_CLASS = re.compile(
    r"about|contact|source|share|social|newsletter|subscribe|related|tags?\b|cookie|"
    r"boilerplate|breadcrumb|byline|dateline-meta|print|sidebar|promo|signup", re.I)
NOISE_TEXT = re.compile(
    r"^(about\s+\S+|media contact|media contacts|contact:|for more information|"
    r"source\b|share this|follow us|subscribe|related)", re.I)


def _soup(html):
    try:
        return BeautifulSoup(html, "lxml")
    except Exception:
        return BeautifulSoup(html, "html.parser")


def _clean(text):
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def _norm_month(s):
    return re.sub(r"^Sept?\b", "Sep", s, flags=re.I)


def _date_from_text(text):
    m = DATE_MDY.search(text)
    if m:
        try:
            return dateparser.parse("%s %s %s" % (_norm_month(m.group(1)), m.group(2), m.group(3))).strftime("%Y-%m-%d")
        except Exception:
            pass
    m = DATE_DMY.search(text)
    if m:
        try:
            return dateparser.parse("%s %s %s" % (m.group(1), _norm_month(m.group(2)), m.group(3))).strftime("%Y-%m-%d")
        except Exception:
            pass
    return None


def _iso(value):
    if not value:
        return None
    value = value.strip()
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", value)
    if m:
        return "%s-%s-%s" % m.groups()
    try:
        return dateparser.parse(value).strftime("%Y-%m-%d")
    except Exception:
        return _date_from_text(value)


def _jsonld(soup):
    out = []
    for s in soup.find_all("script", type=re.compile("ld\\+json", re.I)):
        try:
            data = json.loads(s.string or s.get_text())
        except Exception:
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


def _meta(soup, *names):
    for n in names:
        tag = soup.find("meta", attrs={"property": n}) or soup.find("meta", attrs={"name": n})
        if tag and tag.get("content"):
            return tag["content"].strip()
    return None


def _container(soup):
    for sel in ("div.pr-text", "[itemprop=articleBody]", "article", "main"):
        c = soup.select_one(sel)
        if c:
            return c
    return soup.body or soup


def _title(soup, container):
    h = soup.select_one("main h1") or soup.find("h1")
    if h and _clean(h.get_text()):
        return _clean(h.get_text())
    t = _meta(soup, "og:title")
    if t:
        return _clean(t)
    if soup.title:
        t = _clean(soup.title.get_text())
        return re.split(r"\s+[|\u2013\u2014-]\s+", t)[0]
    return ""


def _body_paragraphs(container):
    c = BeautifulSoup(str(container), "html.parser")
    for t in c.find_all(["script", "style", "nav", "aside", "form", "footer", "header",
                         "button", "noscript", "iframe", "figure"]):
        t.decompose()
    for t in c.find_all(True):
        if t.decomposed if hasattr(t, "decomposed") else False:
            continue
        cls = " ".join(t.get("class", []) or []) + " " + (t.get("id") or "")
        if t.name not in ("html", "body") and NOISE_CLASS.search(cls) and t is not c.contents[0:1] and t.name != "div" or \
                (t.name == "div" and NOISE_CLASS.search(cls) and "pr-text" not in cls):
            t.decompose()
    for br in c.find_all("br"):
        br.replace_with(" ")
    h1 = c.find("h1")
    if h1:
        h1.decompose()
    paras = []
    for el in c.find_all(["p", "h2", "h3", "h4", "h5", "h6", "li"]):
        txt = _clean(el.get_text())
        if not txt:
            continue
        if NOISE_TEXT.match(txt):
            continue
        paras.append(txt)
    return paras


def _authors(soup, container):
    names = []
    for d in _jsonld(soup):
        a = d.get("author")
        if a:
            for x in (a if isinstance(a, list) else [a]):
                n = x.get("name") if isinstance(x, dict) else x
                if isinstance(n, str) and n.strip():
                    names.append(n)
    if not names:
        m = _meta(soup, "author", "article:author")
        if m and not m.startswith("http"):
            names.append(m)
    if not names:
        for el in soup.select("[rel=author], [itemprop=author], .byline, .author, .pr-author"):
            t = _clean(el.get_text())
            if t:
                names.append(t)
                break
    result = []
    for n in names:
        n = re.sub(r"^\s*by\s+", "", n, flags=re.I)
        for part in re.split(r"\s*(?:,\s*and\s+|\band\b|&|;|\s+und\s+)\s*", n):
            part = re.split(r"\s*[,\u2013\u2014|]\s*|\s+-\s+", part)[0]
            part = re.sub(r"^\s*by\s+", "", part, flags=re.I).strip()
            if part and part.lower() not in [r.lower() for r in result]:
                result.append(part)
    return " and ".join(result) if result else None


def _date(soup, container, url, paras):
    for d in _jsonld(soup):
        v = d.get("datePublished") or d.get("dateCreated")
        if isinstance(v, str) and _iso(v):
            return _iso(v)
    v = _meta(soup, "article:published_time", "datePublished", "date", "DC.date.issued",
              "pubdate", "publish-date")
    if v and _iso(v):
        return _iso(v)
    t = soup.find("time", attrs={"datetime": True}) if soup else None
    if t and _iso(t["datetime"]):
        return _iso(t["datetime"])
    if paras:
        d = _date_from_text(paras[0][:200])
        if d:
            return d
    m = URL_DATE.search(urlparse(url).path)
    if m:
        return "%s-%s-%s" % m.groups()
    return None


def _is_release_href(href):
    path = urlparse(href).path
    return bool(re.search(r"/pr-[\w-]+\.html?$", path))


def _listing_links(soup, page_url):
    links = []
    anchors = soup.select("div.pr a[href], .pr-list a[href]")
    if not anchors:
        anchors = [a for a in soup.find_all("a", href=True) if _is_release_href(a["href"])]
    for a in anchors:
        u = urldefrag(urljoin(page_url, a["href"]))[0]
        if u not in links:
            links.append(u)
    return links


def _next_pages(soup, page_url):
    found = []
    for a in soup.find_all("a", href=True):
        rel = a.get("rel") or []
        txt = _clean(a.get_text()).lower()
        href = a["href"]
        if "next" in rel or re.match(r"^(next|older|more|load more)\b|^[\u203a\u00bb>]+$|^\d+$", txt) \
                or re.search(r"[?&](page|p|offset)=\d+", href) or re.search(r"/page/\d+", href):
            if _is_release_href(href):
                continue
            u = urldefrag(urljoin(page_url, href))[0]
            found.append(u)
    link = soup.find("link", rel="next")
    if link and link.get("href"):
        found.append(urldefrag(urljoin(page_url, link["href"]))[0])
    return found


def extract(fetch, listing_url):
    host = urlparse(listing_url).netloc
    seen_pages = set()
    queue = [listing_url]
    release_urls = []
    first = True
    while queue and len(seen_pages) < 100:
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
        for u in _listing_links(soup, page):
            if u not in release_urls:
                release_urls.append(u)
        for n in _next_pages(soup, page):
            if urlparse(n).netloc == host and n not in seen_pages and n not in queue \
                    and n not in release_urls:
                queue.append(n)

    records = []
    for idx, url in enumerate(release_urls):
        try:
            html = fetch(url)
        except Exception:
            continue
        soup = _soup(html)
        container = _container(soup)
        paras = _body_paragraphs(container)
        records.append((idx, {
            "url": url,
            "title": _title(soup, container),
            "date": _date(soup, container, url, paras),
            "author": _authors(soup, container),
            "body": "\n\n".join(paras),
        }))

    records.sort(key=lambda r: (r[1]["date"] or "", -r[0]), reverse=True)
    return [r[1] for r in records]
