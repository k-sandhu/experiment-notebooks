import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from dateutil import parser as date_parser


DATE_RE = re.compile(r"\b\d{1,2}\s+[A-Za-z]+\s+\d{4}\b|\b\d{4}-\d{2}-\d{2}\b")
RELEASE_PATH_RE = re.compile(r"/press-releases/\d{4}/\d{2}/")
NEXT_LABELS = {"next", "next page", "\u203a", "\u00bb", ">"}
TITLE_WORDS = {
    "governor", "deputy", "director", "head", "chief", "officer", "economist",
    "analyst", "manager", "adviser", "advisor", "secretary", "spokesperson",
    "executive", "president", "chair", "member", "senior", "principal",
}
BODY_SKIP_ANCESTORS = ["aside", "nav", "footer", "header", "form", "figure"]


def _clean(text):
    return " ".join((text or "").split())


def _to_iso(text):
    match = DATE_RE.search(text or "")
    if not match:
        return None
    try:
        return date_parser.parse(match.group(0)).date().isoformat()
    except (ValueError, OverflowError):
        return None


def _listing_entries(soup, base):
    entries = []
    for row in soup.select("table.bok-table tbody tr"):
        link = row.find("a", href=True)
        if link is None:
            continue
        url = urljoin(base, link["href"])
        date_cell = row.find("td", class_="date") or row.find("td")
        listing_date = _to_iso(date_cell.get_text(" ")) if date_cell else None
        entries.append((url, listing_date))

    if not entries:
        # Fallback for listings that are not in the expected table layout.
        for link in soup.select("main a[href]"):
            if RELEASE_PATH_RE.search(link["href"]):
                entries.append((urljoin(base, link["href"]), None))
    return entries


def _next_page(soup, base):
    link = soup.select_one('a[rel~="next"]')
    if link is None:
        for candidate in soup.find_all("a", href=True):
            label = _clean(candidate.get_text()).lower()
            aria = (candidate.get("aria-label") or "").lower()
            if label in NEXT_LABELS or aria == "next page":
                link = candidate
                break
    if link is None or not link.get("href"):
        return None
    return urljoin(base, link["href"])


def _collect_listing(fetch, listing_url):
    entries = []
    seen_urls = set()
    seen_pages = set()
    page = listing_url

    while page and page not in seen_pages:
        seen_pages.add(page)
        soup = BeautifulSoup(fetch(page), "html.parser")
        for url, listing_date in _listing_entries(soup, page):
            if url not in seen_urls:
                seen_urls.add(url)
                entries.append((url, listing_date))
        page = _next_page(soup, page)

    return entries


def _author(soup):
    text = None
    meta = soup.find("meta", attrs={"name": "author"})
    if meta and meta.get("content"):
        text = meta["content"]
    else:
        byline = soup.select_one(".byline, .author, [class*=byline]")
        if byline:
            text = byline.get_text(" ")
    if not text:
        return None

    text = re.sub(r"^\s*by\s+", "", _clean(text), flags=re.I)
    names = []
    for chunk in re.split(r"\s*(?:,|;|\band\b)\s*", text, flags=re.I):
        tokens = [
            token for token in chunk.split()
            if token.lower().strip(".()") not in TITLE_WORDS
        ]
        name = " ".join(tokens).strip(" ()")
        if name:
            names.append(name)
    return " and ".join(names) if names else None


def _body(soup):
    container = soup.select_one(".rte") or soup.select_one("article") or soup.find("main")
    if container is None:
        return ""

    paragraphs = []
    for element in container.find_all(["p", "h2", "h3", "h4", "li"]):
        if element.name == "li" and element.find("p"):
            continue
        if element.find_parent(BODY_SKIP_ANCESTORS) is not None:
            continue
        text = _clean(element.get_text())
        if text:
            paragraphs.append(text)
    return "\n\n".join(paragraphs)


def _release(fetch, url, listing_date):
    soup = BeautifulSoup(fetch(url), "html.parser")

    title_el = soup.select_one(".page-head h1") or soup.find("h1")
    title = _clean(title_el.get_text()) if title_el else ""

    date = None
    published = soup.find(string=re.compile(r"Published\s+on", re.I))
    if published:
        text = str(published)
        start = re.search(r"Published\s+on", text, re.I).start()
        date = _to_iso(text[start:])
    if date is None:
        date = listing_date

    return {
        "url": url,
        "title": title,
        "date": date,
        "author": _author(soup),
        "body": _body(soup),
    }


def extract(fetch, listing_url):
    entries = _collect_listing(fetch, listing_url)
    records = [_release(fetch, url, listing_date) for url, listing_date in entries]
    records.sort(key=lambda record: record["date"] or "", reverse=True)
    return records
