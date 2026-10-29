import re
import xml.etree.ElementTree as ET
from datetime import date
from urllib.parse import parse_qs, urljoin, urlsplit

from bs4 import BeautifulSoup
from dateutil import parser as date_parser

RELEASE_PATH = re.compile(r"^/press/\d{4}/\d{2}/\d{2}/[^/]+/?$")
URL_DATE = re.compile(r"^/press/(\d{4})/(\d{2})/(\d{2})/")
PAGE_PATH = re.compile(r"/page/\d+/?$")
YEAR = re.compile(r"\b(?:19|20)\d{2}\b")
NOT_PUBLICATION_DATE = re.compile(
    r"updated|reviewed|revised|modified|effective|closing|closes|deadline|until|expires|event", re.I
)
ROLE_WORDS = re.compile(
    r"\b(director|analyst|head|senior|junior|associate|managing|chief|officer|partner|"
    r"manager|president|economist|lead|vice|principal|editor|chair)\b",
    re.I,
)
EXCLUDED_BLOCK = re.compile(r"share|newsletter|related|tags?|contact|cookie|disclaimer|social|advert|promo", re.I)
MAX_LISTING_PAGES = 200


def _clean(node):
    return " ".join(node.get_text(" ", strip=True).split())


def _absolute(base, href):
    parts = urlsplit(urljoin(base, href.strip()))
    return parts._replace(fragment="").geturl()


def _release_urls(soup, page_url, site):
    urls = []
    for a in soup.find_all("a", href=True):
        url = _absolute(page_url, a["href"])
        parts = urlsplit(url)
        if parts.netloc.lower() == site and RELEASE_PATH.match(parts.path):
            urls.append(parts._replace(query="").geturl())
    return urls


def _listing_pages(soup, page_url, listing_url):
    listing = urlsplit(listing_url)
    site = listing.netloc.lower()
    pages = []
    for a in soup.find_all("a", href=True):
        url = _absolute(page_url, a["href"])
        parts = urlsplit(url)
        if parts.netloc.lower() != site or not parts.path.startswith(listing.path):
            continue
        if RELEASE_PATH.match(parts.path):
            continue
        is_next = "next" in (a.get("rel") or [])
        if is_next or "page" in parse_qs(parts.query) or PAGE_PATH.search(parts.path):
            pages.append(url)
    return pages


def _feed_release_urls(soup, listing_url, fetch):
    # The listing itself is rendered by JavaScript, so the RSS feed advertised
    # in the page head is the reliable source of release links.
    link = soup.find("link", rel="alternate", type="application/rss+xml")
    if link is None or not link.get("href"):
        return []
    try:
        root = ET.fromstring(fetch(_absolute(listing_url, link["href"])).encode("utf-8"))
    except (FetchError, ET.ParseError):
        return []

    site = urlsplit(listing_url).netloc.lower()
    urls = []
    for node in root.iter():
        if node.tag.rsplit("}", 1)[-1] != "link":
            continue
        href = (node.get("href") or node.text or "").strip()
        if not href:
            continue
        parts = urlsplit(_absolute(listing_url, href))
        if parts.netloc.lower() == site and RELEASE_PATH.match(parts.path):
            urls.append(parts._replace(query="").geturl())
    return urls


def _parse_date(value):
    if not value or not YEAR.search(value):
        return None
    try:
        return date_parser.parse(value, fuzzy=True).date()
    except (ValueError, OverflowError):
        return None


def _publication_date(soup, url):
    candidates = []
    meta = soup.find("meta", attrs={"property": "article:published_time"})
    if meta is not None:
        candidates.append(meta.get("content"))
    time_tag = soup.find("time", attrs={"itemprop": "datePublished"})
    if time_tag is not None:
        candidates.append(time_tag.get("datetime") or _clean(time_tag))
    for span in soup.select(".pr-meta span"):
        label = _clean(span)
        if label and not NOT_PUBLICATION_DATE.search(label):
            candidates.append(label)
    for value in candidates:
        parsed = _parse_date(value)
        if parsed is not None:
            return parsed
    match = URL_DATE.match(urlsplit(url).path)
    return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))


def _authors(soup):
    raw = None
    tag = soup.select_one(".pr-meta .analyst")
    if tag is not None:
        raw = _clean(tag)
    if not raw:
        meta = soup.find("meta", attrs={"name": "author"})
        raw = meta.get("content") if meta is not None else None
    if not raw:
        return None
    raw = re.sub(r"^(?:written\s+by|by|authors?|analysts?)\b\s*:?\s*", "", raw.strip(), flags=re.I)
    names = []
    for piece in re.split(r"\s*(?:,|;|&|\band\b)\s*", raw, flags=re.I):
        piece = piece.strip()
        if piece and not ROLE_WORDS.search(piece) and piece not in names:
            names.append(piece)
    return " and ".join(names) or None


def _inside_excluded(el, container):
    for parent in el.parents:
        if parent is container:
            break
        if EXCLUDED_BLOCK.search(" ".join(parent.get("class") or [])):
            return True
    return False


def _body(container):
    paragraphs = []
    for el in container.find_all(["p", "h2", "h3", "h4"]):
        if _inside_excluded(el, container):
            continue
        text = _clean(el)
        if text:
            paragraphs.append(text)
    return "\n\n".join(paragraphs)


def _parse_release(html, url):
    soup = BeautifulSoup(html, "html.parser")
    article = soup.find("article") or soup.find("main") or soup
    heading = article.find("h1")
    if heading is None:
        heading = soup.find("h1")
    title = _clean(heading) if heading is not None else ""
    container = article.select_one(".pr-body") or article
    return {
        "url": url,
        "title": title,
        "date": _publication_date(soup, url).isoformat(),
        "author": _authors(soup),
        "body": _body(container),
    }


def extract(fetch, listing_url):
    site = urlsplit(listing_url).netloc.lower()
    queue = [listing_url]
    visited = set()
    release_urls = []
    first_soup = None

    while queue and len(visited) < MAX_LISTING_PAGES:
        page_url = queue.pop(0)
        if page_url in visited:
            continue
        visited.add(page_url)
        soup = BeautifulSoup(fetch(page_url), "html.parser")
        if first_soup is None:
            first_soup = soup
        release_urls.extend(_release_urls(soup, page_url, site))
        queue.extend(_listing_pages(soup, page_url, listing_url))

    release_urls.extend(_feed_release_urls(first_soup, listing_url, fetch))

    seen = set()
    records = []
    for url in release_urls:
        key = url.rstrip("/")
        if key in seen:
            continue
        seen.add(key)
        records.append(_parse_release(fetch(url), url))

    records.sort(key=lambda record: record["date"], reverse=True)
    return records
