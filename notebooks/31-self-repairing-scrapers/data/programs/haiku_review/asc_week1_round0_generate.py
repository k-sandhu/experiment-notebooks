import json
import re
from urllib.parse import urldefrag, urljoin, urlparse

from bs4 import BeautifulSoup
from bs4.element import NavigableString
from dateutil import parser as date_parser


MAX_LISTING_PAGES = 500

BLOCK_TAGS = ("h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "dt", "dd", "td", "th",
              "blockquote", "pre", "figcaption", "table", "div", "section")
EXCLUDED_TAGS = {"nav", "aside", "footer", "header", "form", "button", "script",
                 "style", "noscript", "iframe", "svg", "select", "input", "textarea"}
EXCLUDED_CLASS_RE = re.compile(
    r"(?:^|[\s_-])(?:share|sharing|social|newsletter|subscribe|related|tags?|contact|"
    r"feedback|page-meta|meta|cookies?|breadcrumbs?|byline|about-us|boilerplate|"
    r"nav|menu|sidebar|promo|advert)(?=[\s_-]|$)",
    re.I,
)
NEXT_LABELS = {"next", "next page", "next »", "next ›", "older", "older posts",
               "older articles", "»", "›", ">"}


def _clean(text):
    return " ".join(str(text).split())


def _listing_links(soup, page_url, listing_url):
    root = urlparse(listing_url)
    prefix = root.path if root.path.endswith("/") else root.path + "/"
    scope = soup.find("main") or soup
    found = []
    for a in scope.find_all("a", href=True):
        absolute = urldefrag(urljoin(page_url, a["href"]))[0]
        link = urlparse(absolute)
        if link.scheme not in ("http", "https") or link.netloc.lower() != root.netloc.lower():
            continue
        if not link.path.startswith(prefix) or link.path.endswith("/"):
            continue
        if re.search(r"/page/\d+$", link.path) or re.search(r"(^|&)page=\d+", link.query):
            continue
        found.append(absolute)
    return found


def _next_page(soup, page_url):
    link = soup.select_one("link[rel~=next][href], a[rel~=next][href]")
    if link is None:
        for a in soup.find_all("a", href=True):
            label = _clean(a.get_text()).lower()
            aria = (a.get("aria-label") or "").lower()
            if label in NEXT_LABELS or "next" in aria:
                link = a
                break
    return urldefrag(urljoin(page_url, link["href"]))[0] if link is not None else None


def _news_json_ld(soup):
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or script.get_text() or "")
        except ValueError:
            continue
        for node in _ld_nodes(data):
            if _is_article(node):
                return node
    return None


def _ld_nodes(data):
    if isinstance(data, list):
        for item in data:
            yield from _ld_nodes(item)
    elif isinstance(data, dict):
        yield data
        if "@graph" in data:
            yield from _ld_nodes(data["@graph"])


def _is_article(node):
    types = node.get("@type")
    if isinstance(types, str):
        types = [types]
    if not isinstance(types, list):
        return False
    return any(isinstance(t, str) and "Article" in t for t in types)


def _title(soup, article, ld):
    h1 = article.find("h1") or soup.find("h1")
    if h1 is not None:
        text = _clean(h1.get_text())
        if text:
            return text
    if ld and isinstance(ld.get("headline"), str):
        return _clean(ld["headline"])
    og = soup.find("meta", property="og:title")
    if og and og.get("content"):
        return _clean(og["content"])
    if soup.title and soup.title.string:
        return _clean(soup.title.string.split(" | ")[0])
    return None


def _published_date(soup, ld):
    values = []
    if ld and isinstance(ld.get("datePublished"), str):
        values.append(ld["datePublished"])
    for selector in ('meta[property="article:published_time"]',
                     'meta[name="article:published_time"]',
                     'meta[itemprop="datePublished"]',
                     'meta[name="DC.date.issued"]',
                     'meta[name="date"]',
                     'time[itemprop="datePublished"]'):
        tag = soup.select_one(selector)
        if tag is not None:
            values.append(tag.get("content") or tag.get("datetime") or tag.get_text())
    for value in values:
        try:
            return date_parser.parse(str(value).strip()).date().isoformat()
        except (ValueError, OverflowError, TypeError):
            continue
    return None


def _ld_names(value):
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        out = []
        for item in value:
            out.extend(_ld_names(item))
        return out
    if isinstance(value, dict):
        types = value.get("@type")
        types = [types] if isinstance(types, str) else (types or [])
        if types and "Person" not in types:
            return []
        name = value.get("name")
        return [name] if isinstance(name, str) else []
    return []


def _split_names(text):
    return [part for part in re.split(r";|&|\s+and\s+", _clean(text), flags=re.I) if part.strip()]


def _person_name(raw):
    text = _clean(raw)
    text = re.sub(r"^(?:written\s+)?by\s*:?\s+", "", text, flags=re.I)
    return text.split(",")[0].strip()


def _author(soup, article, ld):
    raw_names = []
    if ld:
        raw_names.extend(_ld_names(ld.get("author")))
    if not raw_names:
        meta = soup.select_one('meta[name="author"]')
        if meta is not None and meta.get("content"):
            raw_names.append(meta["content"])
    if not raw_names:
        byline = article.select_one('[rel~=author], [itemprop=author], .byline')
        if byline is not None:
            raw_names.append(byline.get_text(" "))
    names = []
    for raw in raw_names:
        for part in _split_names(raw):
            name = _person_name(part)
            if name and name not in names:
                names.append(name)
    return " and ".join(names) or None


def _content(article):
    return article.select_one(".prose") or article


def _excluded(tag):
    if tag.name in EXCLUDED_TAGS:
        return True
    classes = " ".join(tag.get("class") or [])
    ident = tag.get("id") or ""
    return bool(EXCLUDED_CLASS_RE.search(classes)) or bool(EXCLUDED_CLASS_RE.search(ident))


def _chain(el, container):
    chain = [el]
    for parent in el.parents:
        if parent is container:
            break
        chain.append(parent)
    return chain


def _own_text(el):
    parts = []
    for s in el.find_all(string=True):
        if type(s) is not NavigableString:
            continue
        blocked = False
        for parent in s.parents:
            if parent is el:
                break
            if parent.name in BLOCK_TAGS or _excluded(parent):
                blocked = True
                break
        if not blocked:
            parts.append(str(s))
    return _clean("".join(parts))


def _body(container, title):
    for br in container.find_all("br"):
        br.replace_with(" ")
    paragraphs = []
    for el in container.find_all(BLOCK_TAGS):
        if any(_excluded(node) for node in _chain(el, container)):
            continue
        text = _own_text(el)
        if text and text != title:
            paragraphs.append(text)
    return "\n\n".join(paragraphs)


def _parse_release(fetch, url):
    soup = BeautifulSoup(fetch(url), "html.parser")
    ld = _news_json_ld(soup)
    article = soup.find("article") or soup.find("main") or soup
    title = _title(soup, article, ld)
    return {
        "url": url,
        "title": title,
        "date": _published_date(soup, ld),
        "author": _author(soup, article, ld),
        "body": _body(_content(article), title),
    }


def extract(fetch, listing_url):
    listing_url = urldefrag(listing_url)[0]
    release_urls = []
    seen_urls = set()
    seen_pages = set()
    page_url = listing_url
    while page_url and page_url not in seen_pages and len(seen_pages) < MAX_LISTING_PAGES:
        seen_pages.add(page_url)
        soup = BeautifulSoup(fetch(page_url), "html.parser")
        for url in _listing_links(soup, page_url, listing_url):
            if url not in seen_urls:
                seen_urls.add(url)
                release_urls.append(url)
        page_url = _next_page(soup, page_url)

    records = [_parse_release(fetch, url) for url in release_urls]
    records.sort(key=lambda record: record["date"] or "", reverse=True)
    return records
