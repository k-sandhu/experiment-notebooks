"""Collect the news releases on the Food Manufacturers Federation of Kestria media centre."""

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from dateutil import parser as date_parser

ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
YEAR = re.compile(r"\b\d{4}\b")
MAX_LISTING_PAGES = 500

# Page furniture that must never end up in a release body.
NOISE_SELECTOR = (
    "script, style, noscript, nav, aside, form, button, iframe, "
    "[class~=share], [class*=newsletter], [class*=related], [class~=tags], "
    "[class*=cookie], [class*=member-cta], [class*=contact-box]"
)
# Body blocks. Nested blocks are taken through their outermost block ancestor.
BLOCK_TAGS = ["p", "h2", "h3", "h4", "h5", "h6", "li", "blockquote", "pre"]
HEADING_TAGS = {"h2", "h3", "h4", "h5", "h6"}
# Standard boilerplate about the federation, which is dropped from the body.
ABOUT_PATTERN = re.compile(
    r"^(about (us|fmf|the (food manufacturers )?federation( of kestria)?)\b"
    r"|the food manufacturers federation of kestria( \(fmf\))? (is|represents)\b)",
    re.IGNORECASE,
)
NEXT_LABELS = {"next", "next page", "older", "older posts", ">", "›", "»", "next »", "next ›"}


def extract(fetch, listing_url):
    # Walk every listing page, collecting each NewsArticle link once.
    items = []
    seen_pages = set()
    seen_urls = set()
    page_url = listing_url
    while page_url and page_url not in seen_pages and len(seen_pages) < MAX_LISTING_PAGES:
        seen_pages.add(page_url)
        soup = BeautifulSoup(fetch(page_url), "html.parser")
        for url, listing_date in _listing_items(soup, page_url):
            if url not in seen_urls:
                seen_urls.add(url)
                items.append((url, listing_date))
        page_url = _next_page(soup, page_url)

    # A failed release page raises rather than being skipped, so the weekly run
    # never silently drops a release.
    records = [_release_record(fetch, url, listing_date) for url, listing_date in items]
    records.sort(key=lambda record: record["date"] or "", reverse=True)
    return records


def _listing_items(soup, page_url):
    items = []
    for node in soup.find_all(attrs={"itemtype": re.compile(r"NewsArticle")}):
        link = node.select_one('a[itemprop="url"]') or node.find("a", href=True)
        if link is None or not link.get("href"):
            continue
        date_node = node.select_one('meta[itemprop="datePublished"]')
        listing_date = _iso_date(date_node.get("content")) if date_node else None
        items.append((urljoin(page_url, link["href"].strip()), listing_date))
    return items


def _next_page(soup, page_url):
    link = soup.select_one('link[rel~="next"], a[rel~="next"]')
    if link is None:
        for candidate in soup.find_all("a", href=True):
            label = " ".join(candidate.get_text().split()).lower()
            aria = (candidate.get("aria-label") or "").strip().lower()
            if label in NEXT_LABELS or aria in NEXT_LABELS:
                link = candidate
                break
    if link is None or not link.get("href"):
        return None
    return urljoin(page_url, link["href"].strip())


def _release_record(fetch, url, listing_date):
    soup = BeautifulSoup(fetch(url), "html.parser")
    scope = soup.find("article") or soup
    return {
        "url": url,
        "title": _title(soup),
        "date": _published(soup, scope, listing_date),
        "author": _author(scope),
        "body": _body(soup),
    }


def _title(soup):
    heading = soup.select_one('h1[itemprop="headline"]') or soup.find("h1")
    return " ".join(heading.get_text().split()) if heading else ""


def _published(soup, scope, listing_date):
    # Use the first-publication timestamp only, never a modified or reviewed date.
    candidates = scope.select('[itemprop="datePublished"]')
    candidates += soup.select('meta[property="article:published_time"]')
    for node in candidates:
        iso = _iso_date(node.get("content") or node.get("datetime"))
        if iso:
            return iso
    return listing_date


def _iso_date(value):
    value = (value or "").strip()
    if not value:
        return None
    match = ISO_DATE.search(value)
    if match:
        return match.group(0)
    # Only parse strings that carry a year, so a missing year is never guessed.
    if not YEAR.search(value):
        return None
    try:
        return date_parser.parse(value).date().isoformat()
    except (ValueError, OverflowError):
        return None


def _author(scope):
    names = []
    # Credited people only: organisations are skipped, and job titles are excluded
    # because only the name node is read.
    for node in scope.select('[itemprop="author"]'):
        if "Organization" in str(node.get("itemtype") or ""):
            continue
        name_node = node.select_one('[itemprop="name"]')
        if name_node is None and node.select_one('[itemprop="jobTitle"]') is None:
            name_node = node
        if name_node is not None:
            names.append(name_node.get_text(" "))

    # Fall back to a visible "By ..." byline when no schema author is present.
    if not names:
        byline = scope.select_one(".byline")
        if byline is not None:
            for part in re.split(r"[·|]", byline.get_text()):
                if re.match(r"^\s*by\s+", part, re.IGNORECASE):
                    names.append(part)

    unique = []
    for name in names:
        name = _clean_name(name)
        if name and name not in unique:
            unique.append(name)
    return " and ".join(unique) if unique else None


def _clean_name(text):
    text = " ".join(text.split())
    text = re.sub(r"^by\s+", "", text, flags=re.IGNORECASE)
    return text.strip(" ,;")


def _body(soup):
    container = (
        soup.select_one('[itemprop="articleBody"]')
        or soup.find("article")
        or soup.find("main")
    )
    if container is None:
        return ""

    for node in container.select(NOISE_SELECTOR):
        node.decompose()
    for br in container.find_all("br"):
        br.replace_with(" ")

    paragraphs = []
    skipping = False  # True while inside an "About us" section.
    for el in container.find_all(BLOCK_TAGS):
        parent = el.find_parent(BLOCK_TAGS)
        if parent is not None and _inside(parent, container):
            continue  # Text is already included through its outer block.
        text = " ".join(el.get_text().split())
        if not text:
            continue
        if el.name in HEADING_TAGS:
            skipping = bool(ABOUT_PATTERN.match(text))
            if not skipping:
                paragraphs.append(text)
            continue
        if skipping or ABOUT_PATTERN.match(text):
            continue
        paragraphs.append(text)
    return "\n\n".join(paragraphs)


def _inside(node, container):
    return any(ancestor is container for ancestor in node.parents)
