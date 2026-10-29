import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from dateutil import parser as date_parser

MAX_LISTING_PAGES = 200

MONTH_HEADING = re.compile(r"^[A-Za-z]+\s+\d{4}$")
DAY_NUMBER = re.compile(r"\d{1,2}")
RELEASE_PATH = re.compile(r"/news/[^/]+/?$")
AUTHOR_PREFIX = re.compile(r"^\s*(?:authors?\s*:\s*|written\s+by\s+|by\s+)", re.I)
NAME_SPLIT = re.compile(r"\s*;\s*|\s+and\s+|\s*&\s*", re.I)
JOB_WORDS = re.compile(
    r"\b(head|director|chief|manager|officer|analyst|lead|senior|commissioner|chair|"
    r"executive|editor|advis[eo]r|specialist|team|assistant|secretary|president|partner|"
    r"economist|spokesperson|communications|press|deputy|principal)\b",
    re.I,
)
NEXT_LABELS = {"next", "next page", "older", "older posts", "older news"}
BLOCK_TAGS = ("p", "li", "blockquote", "h2", "h3", "h4", "h5", "h6")
SKIP_TAGS = ("nav", "header", "footer", "form", "aside", "script", "style")
SKIP_CLASSES = {
    "share", "sharing", "social", "related", "tags", "tag-list", "contact",
    "newsletter", "cookie-notice", "lede-author", "byline", "meta",
}


def _clean(node):
    """Return the node's text with whitespace collapsed; empty string for None."""
    if node is None:
        return ""
    return " ".join(node.get_text().split())


def _iso(raw):
    try:
        return date_parser.parse(raw).date().isoformat()
    except (ValueError, OverflowError, TypeError):
        return None


def _next_page_url(soup, page_url):
    link = soup.find("link", rel="next") or soup.find("a", rel="next")
    if link is None:
        for candidate in soup.find_all("a", href=True):
            label = _clean(candidate).lower().strip(" ›»>")
            if label in NEXT_LABELS or "next" in (candidate.get("class") or []):
                link = candidate
                break
    if link is None or not link.get("href"):
        return None
    return urljoin(page_url, link["href"])


def _listing_entries(soup, listing_url):
    """Return (url, listing_date) pairs for release links on one listing page."""
    root = soup.find(class_="archive") or soup.find("main") or soup
    entries = []
    month = None
    for el in root.find_all(["h2", "h3", "h4", "li"]):
        if el.name != "li":
            label = _clean(el)
            if MONTH_HEADING.match(label):
                month = label
            continue
        link = el.find("a", href=True)
        if link is None:
            continue
        url = urljoin(listing_url, link["href"])
        if not RELEASE_PATH.search(urlparse(url).path):
            continue
        listing_date = None
        day = el.find(class_="day")
        if day is not None and month and DAY_NUMBER.fullmatch(_clean(day)):
            listing_date = _iso(f"{_clean(day)} {month}")
        entries.append((url, listing_date))
    return entries


def _all_listing_entries(fetch, listing_url):
    entries = []
    seen_pages = set()
    url = listing_url
    while url and url not in seen_pages and len(seen_pages) < MAX_LISTING_PAGES:
        seen_pages.add(url)
        soup = BeautifulSoup(fetch(url), "html.parser")
        entries.extend(_listing_entries(soup, url))
        url = _next_page_url(soup, url)
    return entries


def _author_names(raw):
    raw = AUTHOR_PREFIX.sub("", raw.strip(), count=1)
    names = []
    for part in NAME_SPLIT.split(raw):
        for piece in part.split(","):
            piece = piece.strip(" .")
            # Drop job titles and anything carrying digits (e.g. a "Published" date).
            if not piece or JOB_WORDS.search(piece) or re.search(r"\d", piece):
                continue
            if piece not in names:
                names.append(piece)
    return " and ".join(names) or None


def _page_date(soup):
    meta = soup.find("meta", attrs={"property": "article:published_time"})
    if meta and meta.get("content"):
        return _iso(meta["content"])
    time_tag = (soup.find("time", attrs={"itemprop": "datePublished"})
                or soup.find("time", class_=re.compile("publish")))
    if time_tag and time_tag.get("datetime"):
        return _iso(time_tag["datetime"])
    return None


def _skipped(el, container):
    """True if the element sits inside navigation, share, related or similar furniture."""
    for node in [el, *el.parents]:
        if node is container:
            break
        if node.name in SKIP_TAGS:
            return True
        if SKIP_CLASSES & set(node.get("class") or []):
            return True
    return False


def _inside_block(el, container):
    """True if a block-level ancestor (below the container) already yields this text."""
    for node in el.parents:
        if node is container:
            return False
        if node.name in BLOCK_TAGS:
            return True
    return False


def _body(soup, main):
    container = soup.find(class_="article-text") or soup.find("article") or main
    paragraphs = []
    for el in container.find_all(BLOCK_TAGS):
        if _skipped(el, container) or _inside_block(el, container):
            continue
        text = _clean(el)
        if text:
            paragraphs.append(text)
    return "\n\n".join(paragraphs)


def _parse_release(html, url, listing_date):
    soup = BeautifulSoup(html, "html.parser")
    main = soup.find("main") or soup

    heading = main.find("h1") or soup.find("h1")
    if heading is not None:
        title = _clean(heading)
    else:
        title = _clean(soup.title).rsplit(" | ", 1)[0]

    byline = main.find(class_=re.compile(r"lede-author|byline|author"))
    if byline is not None:
        raw_author = _clean(byline)
    else:
        meta = soup.find("meta", attrs={"name": "author"})
        raw_author = (meta.get("content") or "") if meta else ""

    return {
        "url": url,
        "title": title,
        "date": listing_date or _page_date(soup),
        "author": _author_names(raw_author),
        "body": _body(soup, main),
    }


def extract(fetch, listing_url):
    # Collect unique release URLs across every listing page, keeping listing order.
    entries = {}
    for url, listing_date in _all_listing_entries(fetch, listing_url):
        entries.setdefault(url, listing_date)

    records = []
    for url, listing_date in entries.items():
        try:
            html = fetch(url)
        except FetchError as exc:
            # A release that has been withdrawn is skipped; other failures are real errors.
            if exc.status in (404, 410):
                continue
            raise
        records.append(_parse_release(html, url, listing_date))

    # Newest first; releases with no determinable date fall to the end.
    records.sort(key=lambda r: r["date"] or "", reverse=True)
    return records
