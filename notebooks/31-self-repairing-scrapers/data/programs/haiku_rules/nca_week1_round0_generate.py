import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from dateutil import parser as date_parser


BLOCK_TAGS = ("p", "h2", "h3", "h4", "li", "blockquote")
NOISE_CLASS = re.compile(
    r"share|social|related|tag|newsletter|cookie|contact|analyst|about|promo|advert|aside|sidebar",
    re.I,
)
NEXT_LABELS = {"next", "next page", "older", "\u203a", "\u00bb"}
NOT_PUBLISHED = re.compile(r"updated|reviewed|modified|effective|closing", re.I)


def _soup(html):
    return BeautifulSoup(html, "html.parser")


def _text(node):
    return " ".join(node.get_text().split()) if node is not None else ""


def _parse_date(value):
    if not value:
        return None
    try:
        return date_parser.parse(value, fuzzy=True).date().isoformat()
    except (ValueError, OverflowError):
        return None


def _next_page(soup, current):
    link = soup.select_one('link[rel~="next"], a[rel~="next"]')
    if link is None:
        for a in soup.find_all("a", href=True):
            label = _text(a).lower()
            aria = (a.get("aria-label") or "").lower()
            if label in NEXT_LABELS or "next" in aria:
                link = a
                break
    if link is None or not link.get("href"):
        return None
    return urljoin(current, link["href"])


def _iter_listing_pages(fetch, listing_url):
    seen = set()
    url = listing_url
    while url and url not in seen:
        seen.add(url)
        soup = _soup(fetch(url))
        yield url, soup
        url = _next_page(soup, url)


def _listing_items(soup, page_url):
    items = []
    for link in soup.select("a.card-link[href]"):
        card = link.find_parent(class_="card") or link.parent
        items.append({
            "url": urljoin(page_url, link["href"]),
            "listing_date": _parse_date(_text(card.select_one(".card-date"))),
        })
    return items


def _published_date(soup, fallback):
    for node in soup.select(
        'meta[property="article:published_time"], meta[itemprop="datePublished"], '
        'meta[name="date"], meta[name="pubdate"], time[itemprop="datePublished"]'
    ):
        value = node.get("content") or node.get("datetime") or _text(node)
        date = _parse_date(value)
        if date:
            return date

    for script in soup.find_all("script", type="application/ld+json"):
        match = re.search(r'"datePublished"\s*:\s*"([^"]+)"', script.get_text())
        if match:
            date = _parse_date(match.group(1))
            if date:
                return date

    for node in soup.select(".dateline, .published, .date"):
        label = _text(node)
        if NOT_PUBLISHED.search(label):
            continue
        date = _parse_date(label)
        if date:
            return date

    return fallback


def _authors(soup):
    container = soup.select_one(".authors, .byline")
    if container is None:
        return None
    names = [_text(a) for a in container.select('a[rel~="author"]')]
    if not names:
        text = _text(container)
        text = re.sub(r"^(by|written by)\s+", "", text, flags=re.I)
        names = [n.strip() for n in re.split(r",|\band\b|&", text) if n.strip()]
    names = [n for n in names if n]
    return " and ".join(names) if names else None


def _title(soup):
    node = (
        soup.select_one("main h1.headline")
        or soup.select_one("main h1")
        or soup.select_one("h1")
    )
    return _text(node)


def _is_noise(el, container):
    for node in [el, *el.parents]:
        if node is container:
            break
        classes = " ".join(node.get("class") or []) + " " + (node.get("id") or "")
        if NOISE_CLASS.search(classes):
            return True
    return False


def _nested_in_block(el, container):
    for anc in el.parents:
        if anc is container:
            return False
        if anc.name in BLOCK_TAGS:
            return True
    return False


def _body(soup):
    container = soup.select_one(".article-body")
    if container is None:
        return ""
    paragraphs = []
    for el in container.find_all(BLOCK_TAGS):
        if _is_noise(el, container) or _nested_in_block(el, container):
            continue
        text = _text(el)
        if not text or text.lower().startswith("about northstar"):
            continue
        paragraphs.append(text)
    return "\n\n".join(paragraphs)


def extract(fetch, listing_url):
    cards = {}
    for page_url, soup in _iter_listing_pages(fetch, listing_url):
        for item in _listing_items(soup, page_url):
            cards.setdefault(item["url"], item)

    records = []
    for url, item in cards.items():
        soup = _soup(fetch(url))
        records.append({
            "url": url,
            "title": _title(soup),
            "date": _published_date(soup, item["listing_date"]),
            "author": _authors(soup),
            "body": _body(soup),
        })

    records.sort(key=lambda r: r["date"] or "", reverse=True)
    return records
