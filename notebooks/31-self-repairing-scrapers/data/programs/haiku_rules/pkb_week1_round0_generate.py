import re
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup
from dateutil import parser as date_parser

MAX_LISTING_PAGES = 200
TEXT_TAGS = ["h2", "h3", "h4", "h5", "h6", "p", "li", "blockquote"]
HEADING_TAGS = {"h2", "h3", "h4", "h5", "h6"}
PAGER_TOKENS = {"pagination", "pager", "paging", "paginator", "pages"}
BOILERPLATE_TAGS = {"nav", "aside", "footer", "form", "button", "script", "style",
                    "noscript", "iframe", "select", "textarea", "svg"}
BOILERPLATE_TOKENS = {
    "share", "sharing", "social", "related", "newsletter", "subscribe", "subscription",
    "cookie", "cookies", "consent", "tag", "tags", "contact", "about", "footer", "nav",
    "navigation", "breadcrumb", "breadcrumbs", "sidebar", "aside", "meta", "advert",
    "advertisement", "ad", "ads", "promo", "cta", "menu", "search", "byline",
    "disclaimer", "boilerplate", "teaser",
}
UPDATED_RE = re.compile(r"\b(last\s+)?(updat\w*|reviewed|modified|effective|closing|closes|until)\b", re.I)
ABOUT_RE = re.compile(r"^about\s+(us|the port|port of kestrel bay)\b", re.I)
JOB_WORDS = {
    "manager", "director", "officer", "head", "chief", "spokesperson", "spokesman",
    "spokeswoman", "editor", "coordinator", "analyst", "captain", "master", "engineer",
    "adviser", "advisor", "secretary", "communications", "relations", "executive",
    "president", "ceo", "cfo", "coo", "team", "department", "office", "harbour",
    "harbor", "port", "newsroom", "press", "media", "specialist", "assistant", "senior",
    "supervisor", "controller", "representative", "writer", "reporter", "correspondent",
    "consultant", "staff",
}


def _text(node):
    return re.sub(r"\s+", " ", node.get_text()).strip()


def _tokens(*values):
    found = set()
    for value in values:
        if not value:
            continue
        if isinstance(value, str):
            value = [value]
        for item in value:
            found.update(t for t in re.split(r"[^a-z0-9]+", item.lower()) if t)
    return found


def _is_boilerplate(el):
    for node in [el, *el.parents]:
        if node.name in BOILERPLATE_TAGS:
            return True
        if _tokens(node.get("class"), node.get("id")) & BOILERPLATE_TOKENS:
            return True
    return False


def _is_pagination(a):
    if "next" in (a.get("rel") or []):
        return True
    for node in [a, *a.parents]:
        if _tokens(node.get("class")) & PAGER_TOKENS:
            return True
    return False


def _parse_date(value):
    if not value or not re.search(r"\d{1,2}\D+\d{4}|\d{4}-\d{2}-\d{2}", value):
        return None
    try:
        return date_parser.parse(value, dayfirst=True, fuzzy=True).date().isoformat()
    except (ValueError, OverflowError):
        return None


def _is_first_published(node):
    context = " ".join(node.get("class") or []) + " " + _text(node)
    prev = node.previous_sibling
    if prev is not None:
        context += " " + (prev.get_text() if hasattr(prev, "get_text") else str(prev))
    return UPDATED_RE.search(context) is None


def _publish_date(soup, article):
    for selector in ('meta[itemprop="datePublished"]',
                     'meta[property="article:published_time"]',
                     'time[itemprop="datePublished"]'):
        node = soup.select_one(selector)
        if node is not None:
            value = node.get("content") or node.get("datetime") or _text(node)
            parsed = _parse_date(value)
            if parsed:
                return parsed
    for node in article.select("[class*=date]"):
        if _is_first_published(node):
            parsed = _parse_date(_text(node))
            if parsed:
                return parsed
    return None


def _has_job_word(name):
    return bool(set(re.findall(r"[a-z]+", name.lower())) & JOB_WORDS)


def _author(soup, article):
    node = None
    for selector in (".meta-author", "[rel~=author]", "[class*=author]"):
        node = article.select_one(selector)
        if node is None:
            node = soup.select_one(selector)
        if node is not None:
            break
    if node is not None:
        for junk in node.select("[class*=role], [class*=title], [class*=job], [class*=position]"):
            junk.decompose()
        raw = _text(node)
    else:
        meta = soup.find("meta", attrs={"name": "author"})
        raw = meta.get("content", "") if meta is not None else ""

    raw = re.sub(r"\([^)]*\)", " ", raw)
    raw = re.sub(r"^\s*(written\s+|posted\s+)?by\s+", "", raw.strip(), flags=re.I)

    names = []
    for part in re.split(r"\s*(?:,|;|&|/|\|)\s*|\s+and\s+", raw, flags=re.I):
        name = part.strip(" .-\u2013\u2014")
        if not name or _has_job_word(name):
            continue
        names.append(name)
    return " and ".join(names) if names else None


def _title(soup, article):
    h1 = article.find("h1")
    if h1 is None:
        h1 = soup.find("h1")
    if h1 is not None:
        return _text(h1)
    title_tag = soup.title
    title = title_tag.get_text() if title_tag is not None else ""
    return re.sub(r"\s+", " ", title).rsplit(" | ", 1)[0].strip()


def _blocks(container):
    out, skipping = [], False
    for el in container.find_all(TEXT_TAGS):
        if el.find_parent(["p", "li", "blockquote"]) is not None:
            continue
        if _is_boilerplate(el):
            continue
        text = _text(el)
        if not text:
            continue
        if el.name in HEADING_TAGS:
            skipping = ABOUT_RE.match(text) is not None
        elif ABOUT_RE.match(text):
            skipping = True
        if skipping:
            continue
        out.append(text)
    return out


def _body(fetch, article, page_url):
    containers = []
    lead = article.select_one(".body-lead")
    rest = article.select_one(".body-rest")
    if lead is not None:
        containers.append(lead)
    if rest is not None:
        src = rest.get("data-src")
        if src:
            containers.append(BeautifulSoup(fetch(urljoin(page_url, src)), "html.parser"))
        else:
            containers.append(rest)
    if not containers:
        containers.append(article)

    blocks, seen = [], set()
    for container in containers:
        for text in _blocks(container):
            if text not in seen:
                seen.add(text)
                blocks.append(text)
    return "\n\n".join(blocks)


def _listed_date(anchor):
    for box in anchor.parents:
        if box.name in ("div", "li", "article", "section"):
            tag = box.find(class_=re.compile(r"date"))
            if tag is not None:
                return _parse_date(_text(tag))
    return None


def _release_links(soup, listing_url):
    base = urlsplit(listing_url)
    prefix = base.path.rstrip("/") + "/"
    scope = soup.find("main")
    if scope is None:
        scope = soup

    found, seen = [], set()
    for a in scope.find_all("a", href=True):
        if _is_pagination(a):
            continue
        url = urljoin(listing_url, a["href"]).split("#")[0]
        parts = urlsplit(url)
        if parts.netloc != base.netloc or not parts.path.startswith(prefix):
            continue
        rest = parts.path[len(prefix):].strip("/")
        if not rest or rest.startswith("fragments/") or re.search(r"(^|/)page/?\d+$", rest):
            continue
        if url in seen:
            continue
        seen.add(url)
        found.append((url, _listed_date(a)))
    return found


def _next_page(soup, current):
    link = soup.find("link", rel=lambda r: bool(r) and "next" in r)
    if link is None:
        link = soup.find("a", rel=lambda r: bool(r) and "next" in r)
    if link is None:
        for a in soup.find_all("a", href=True):
            text = _text(a)
            if len(text) <= 20 and re.match(r"(next|older)\b|^[\u203a\u00bb>]$", text, re.I) and _is_pagination(a):
                link = a
                break
    if link is None or not link.get("href"):
        return None
    nxt = urljoin(current, link["href"]).split("#")[0]
    return None if nxt == current else nxt


def _release(fetch, url, listed_date):
    soup = BeautifulSoup(fetch(url), "html.parser")
    article = soup.find("article")
    if article is None:
        article = soup.find("main")
    if article is None:
        article = soup
    return {
        "url": url,
        "title": _title(soup, article),
        "date": _publish_date(soup, article) or listed_date,
        "author": _author(soup, article),
        "body": _body(fetch, article, url),
    }


def extract(fetch, listing_url):
    links = []
    page_url = listing_url
    visited = set()
    while page_url and page_url not in visited and len(visited) < MAX_LISTING_PAGES:
        visited.add(page_url)
        soup = BeautifulSoup(fetch(page_url), "html.parser")
        links.extend(_release_links(soup, listing_url))
        page_url = _next_page(soup, page_url)

    seen, records = set(), []
    for url, listed_date in links:
        if url in seen:
            continue
        seen.add(url)
        records.append(_release(fetch, url, listed_date))

    records.sort(key=lambda r: r["date"] or "", reverse=True)
    return records
