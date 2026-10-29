import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from dateutil import parser as date_parser


MAX_PAGES = 100

_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}|\d{1,2}\s+[A-Za-z]+\s+\d{4}")
_NEXT_LABELS = {"next", "next page", "older", "older news", "next »", "»", "›", ">"}
_BLOCK_TAGS = ["p", "h2", "h3", "h4", "h5", "h6", "li"]
_SKIP_TAGS = {"nav", "aside", "form", "footer", "header", "script", "style", "noscript", "button"}
_SKIP_WORDS = (
    "share", "related", "tag", "newsletter", "contact", "about",
    "cookie", "social", "label", "published", "byline", "author",
)
_ABOUT_RE = re.compile(r"^about\s+(us|the\s+kestria|kestria)\b", re.I)
_TITLE_NOISE = "[class*=title], [class*=role], [class*=job]"


def _clean(node):
    for br in node.find_all("br"):
        br.replace_with(" ")
    return " ".join(node.get_text().split())


def _to_iso(text):
    match = _DATE_RE.search(text or "")
    if not match:
        return None
    try:
        return date_parser.parse(match.group(0), dayfirst=True).date().isoformat()
    except (ValueError, OverflowError):
        return None


def _listing_items(soup, page_url):
    for el in soup.select(".feed-item"):
        label = el.select_one(".label")
        kind = _clean(label).lower() if label else ""
        if kind:
            is_release = kind == "news release"
        else:
            is_release = "feed-item--release" in el.get("class", [])
        if not is_release:
            continue
        link = el.find("a", href=True)
        if link is None:
            continue
        date_el = el.select_one(".date")
        yield {
            "url": urljoin(page_url, link["href"]),
            "title": _clean(link),
            "listing_date": _to_iso(_clean(date_el)) if date_el else None,
        }


def _next_page(soup, page_url):
    link = soup.select_one("a[rel~=next]") or soup.select_one(".pagination .next a, li.next a, a.next")
    if link is None:
        for candidate in soup.find_all("a", href=True):
            if _clean(candidate).lower() in _NEXT_LABELS:
                link = candidate
                break
    return urljoin(page_url, link["href"]) if link is not None else None


def _title(soup, fallback):
    heading = soup.find("h1")
    text = _clean(heading) if heading else ""
    return text or fallback


def _published(soup):
    for el in soup.select(".published"):
        text = _clean(el)
        if re.search(r"updated|reviewed", text, re.I):
            continue
        date = _to_iso(text)
        if date:
            return date
    for node in soup.find_all(string=re.compile(r"^\s*published\b", re.I)):
        date = _to_iso(_clean(node.parent))
        if date:
            return date
    return None


def _authors(soup):
    names = []
    for el in soup.select(".byline, .author, .authors, [rel~=author]"):
        for noise in el.select(_TITLE_NOISE):
            noise.extract()
        text = re.sub(r"^by\s+", "", _clean(el), flags=re.I)
        for part in re.split(r";|\s+and\s+|\s*&\s*", text):
            name = part.split(",")[0].split("|")[0].strip(" -–—|:")
            if name and name not in names:
                names.append(name)
    return " and ".join(names) if names else None


def _skipped(node, container):
    current = node
    while current is not None and current is not container:
        if current.name in _SKIP_TAGS:
            return True
        classes = " ".join(current.get("class", [])).lower()
        if any(word in classes for word in _SKIP_WORDS):
            return True
        current = current.parent
    return False


def _body(soup):
    container = soup.select_one(".text") or soup.select_one("article") or soup.select_one("main")
    if container is None:
        return ""
    paragraphs = []
    for block in container.find_all(_BLOCK_TAGS):
        if block.find_parent(["li", "p"]) is not None:
            continue
        if _skipped(block, container):
            continue
        text = _clean(block)
        if not text or _ABOUT_RE.match(text):
            continue
        paragraphs.append(text)
    if not paragraphs:
        return _clean(container)
    return "\n\n".join(paragraphs)


def _release(fetch, item):
    soup = BeautifulSoup(fetch(item["url"]), "html.parser")
    author = _authors(soup)
    body = _body(soup)
    return {
        "url": item["url"],
        "title": _title(soup, item["title"]),
        "date": _published(soup) or item["listing_date"],
        "author": author,
        "body": body,
    }


def extract(fetch, listing_url):
    releases = []
    seen_urls = set()
    seen_pages = set()
    page_url = listing_url

    while page_url and page_url not in seen_pages and len(seen_pages) < MAX_PAGES:
        seen_pages.add(page_url)
        soup = BeautifulSoup(fetch(page_url), "html.parser")
        for item in _listing_items(soup, page_url):
            if item["url"] in seen_urls:
                continue
            seen_urls.add(item["url"])
            releases.append(_release(fetch, item))
        page_url = _next_page(soup, page_url)

    releases.sort(key=lambda r: r["date"] or "", reverse=True)
    return releases
