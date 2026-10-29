import datetime
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

BLOCK_TAGS = ["p", "h2", "h3", "h4", "h5", "h6", "li", "blockquote", "pre"]
CHROME_TAGS = {"nav", "header", "footer", "aside"}
NON_BODY_CLASS = re.compile(
    r"about|share|newsletter|related|tag|contact|cookie|byline|pubdate|downloads", re.I
)
UPDATED_CLASS = re.compile(r"updat|revis|review|modif", re.I)
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
NEXT_LABELS = {"next", "next page", "older", "older releases", "\u203a", "\u00bb"}
JOB_WORDS = {
    "head", "director", "chief", "statistician", "statisticians", "analyst", "analysts",
    "manager", "officer", "economist", "economists", "senior", "deputy", "lead", "team",
    "principal", "assistant", "unit", "division", "office", "of", "for", "the", "and",
}
PARTICLES = {"de", "van", "von", "der", "da", "del", "la", "le"}


def extract(fetch, listing_url):
    items = _collect_listing(fetch, listing_url)
    records = []
    seen = set()
    for url, listing_date in items:
        if url in seen:
            continue
        seen.add(url)
        records.append(_parse_release(fetch(url), url, listing_date))
    # ISO dates sort correctly as strings; stable sort keeps listing order for ties
    records.sort(key=lambda r: r["date"], reverse=True)
    return records


def _collect_listing(fetch, listing_url):
    found = []
    visited = set()
    page_url = listing_url
    while page_url and page_url not in visited:
        visited.add(page_url)
        soup = BeautifulSoup(fetch(page_url), "html.parser")
        for item in soup.select("li.news-item"):
            link = item.select_one("a.news-link[href]") or item.find("a", href=True)
            if link is None:
                continue
            time_el = item.find("time")
            listing_date = _iso_date(time_el.get("datetime") if time_el else None)
            found.append((urljoin(page_url, link["href"]), listing_date))
        page_url = _next_page(soup, page_url)
    return found


def _next_page(soup, current_url):
    for tag in soup.select("link[rel~=next][href], a[rel~=next][href]"):
        return urljoin(current_url, tag["href"])
    for a in soup.find_all("a", href=True):
        label = _text(a).lower()
        aria = (a.get("aria-label") or "").strip().lower()
        if label in NEXT_LABELS or aria in NEXT_LABELS:
            return urljoin(current_url, a["href"])
    return None


def _parse_release(html, url, listing_date):
    soup = BeautifulSoup(html, "html.parser")
    article = soup.find("article", class_="release") or soup.find("main") or soup
    h1 = article.find("h1") or soup.find("h1")
    date = _release_date(article) or listing_date
    if date is None:
        raise ValueError("no publication date found for " + url)
    return {
        "url": url,
        "title": _text(h1),
        "date": date,
        "author": _author(article.find(class_="byline")),
        "body": _body(article),
    }


def _release_date(article):
    # Prefer the first-publication time; skip any time marked as updated/reviewed
    chosen = None
    for t in article.find_all("time", attrs={"datetime": True}):
        context = " ".join(_classes(node) for node in [t, *t.parents])
        if UPDATED_CLASS.search(context):
            continue
        if "pubdate" in t.get("class", []):
            return _iso_date(t["datetime"])
        if chosen is None:
            chosen = t
    return _iso_date(chosen["datetime"]) if chosen is not None else None


def _author(tag):
    if tag is None:
        return None
    text = _text(tag)
    text = re.sub(r"^\s*(by|written by)\s+", "", text, flags=re.I)
    names = []
    for segment in text.split(","):
        pieces = [p.strip() for p in re.split(r"\s+and\s+|\s*&\s*", segment) if p.strip()]
        if not pieces:
            continue
        if all(_is_name(p) for p in pieces):
            names.extend(pieces)
        else:
            # Remaining segments are job titles or organisation names
            break
    return " and ".join(names) or None


def _is_name(text):
    words = text.split()
    if not 2 <= len(words) <= 4:
        return False
    for w in words:
        if w.lower() in JOB_WORDS:
            return False
        if not (w[0].isupper() or w.lower() in PARTICLES):
            return False
    return True


def _body(article):
    container = article.find(class_="release-body") or article
    blocks = []
    for el in container.find_all(BLOCK_TAGS):
        # Nested blocks (e.g. p inside li) are already included in their parent
        if any(anc.name in BLOCK_TAGS for anc in el.parents):
            continue
        if _in_chrome(el, container):
            continue
        text = " ".join(el.get_text().split())
        if text:
            blocks.append(text)
    return "\n\n".join(blocks)


def _in_chrome(el, stop):
    for node in el.parents:
        if node is stop:
            break
        if node.name in CHROME_TAGS or NON_BODY_CLASS.search(_classes(node)):
            return True
    return NON_BODY_CLASS.search(_classes(el)) is not None


def _classes(el):
    if not el.name:
        return ""
    return " ".join(el.get("class", []))


def _iso_date(value):
    if not value:
        return None
    m = DATE_RE.search(value)
    if not m:
        return None
    try:
        return datetime.date.fromisoformat(m.group(0)).isoformat()
    except ValueError:
        return None


def _text(el):
    return " ".join(el.get_text(" ").split()) if el is not None else ""
