"""Collect the news releases of Corvel Packaging for the weekly monitoring job."""

import re
from urllib.parse import urldefrag, urljoin, urlparse

from bs4 import BeautifulSoup
from dateutil import parser as date_parser

_MONTH = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?"
_DATE_PATTERNS = [
    re.compile(rf"\b{_MONTH}\s+\d{{1,2}}(?:st|nd|rd|th)?,?\s+\d{{4}}\b", re.IGNORECASE),
    re.compile(rf"\b\d{{1,2}}(?:st|nd|rd|th)?\s+{_MONTH},?\s+\d{{4}}\b", re.IGNORECASE),
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
]
_UPDATED = re.compile(r"updated|reviewed|modified|revised", re.IGNORECASE)
_NEXT_LABELS = {"next", "next page", "older", "older posts", "older articles", "›", "»"}
_TITLE_WORDS = {
    "ceo", "cfo", "coo", "cto", "chief", "director", "manager", "head", "lead",
    "officer", "analyst", "editor", "specialist", "engineer", "president", "vice",
    "senior", "junior", "assistant", "executive", "sales", "marketing", "team",
    "department", "consultant", "writer", "coordinator", "representative",
    "spokesperson", "partner", "founder", "owner", "of", "at", "ops", "operations",
    "communications", "press", "account", "commercial", "product", "group", "office",
    "media",
}
_BLOCK_TAGS = ["p", "h2", "h3", "h4", "li", "blockquote"]
_JUNK = (".share-bar, .newsletter-box, .related-posts, .cvp-cookie, .post-meta, "
         "script, style, noscript, form")


def _clean(text):
    return re.sub(r"\s+", " ", text or "").strip()


def _date_from_text(text):
    for pattern in _DATE_PATTERNS:
        match = pattern.search(text or "")
        if match:
            try:
                return date_parser.parse(match.group(0), fuzzy=True).date().isoformat()
            except (ValueError, OverflowError):
                continue
    return None


def _segments(element):
    """Split the visible text of an element on bullets, bars and line breaks."""
    if element is None:
        return []
    parts = re.split(r"[·•|\n]", element.get_text("\n"))
    return [s for s in (_clean(p) for p in parts) if s]


def _meta_element(article):
    return article.select_one(".post-meta, .post-date, .date, [class*='meta']")


def _published_date(page, article):
    for time_tag in article.find_all("time"):
        label_parts = time_tag.get("class", []) + (
            time_tag.parent.get("class", []) if time_tag.parent else []
        )
        before = time_tag.previous_sibling
        before_text = _clean(before) if isinstance(before, str) else ""
        if _UPDATED.search(" ".join(label_parts) + " " + before_text):
            continue
        found = _date_from_text(time_tag.get("datetime") or time_tag.get_text())
        if found:
            return found

    meta = page.find("meta", attrs={"property": "article:published_time"})
    if meta and meta.get("content"):
        found = _date_from_text(meta["content"])
        if found:
            return found

    for segment in _segments(_meta_element(article)):
        if _UPDATED.search(segment):
            continue
        found = _date_from_text(segment)
        if found:
            return found
    return None


def _title(article, page):
    heading = article.find("h1") or page.find("h1")
    if heading:
        return _clean(heading.get_text())
    og = page.find("meta", attrs={"property": "og:title"})
    if og and og.get("content"):
        return _clean(og["content"])
    if page.title:
        return _clean(re.sub(r"\s*\|[^|]*$", "", page.title.get_text()))
    return None


def _split_names(text):
    text = re.sub(r"^\s*by\s+", "", text, flags=re.IGNORECASE)
    text = re.split(r"\s[-–—]\s", text)[0]
    names = []
    for part in re.split(r"\s*(?:,|;|&|\band\b)\s*", text, flags=re.IGNORECASE):
        part = _clean(part).strip(" .")
        words = part.split()
        if not words or len(words) > 4:
            continue
        if any(w.lower().strip(".,") in _TITLE_WORDS for w in words):
            continue
        names.append(part)
    return names


def _author(article, page):
    candidates = [_clean(el.get_text())
                  for el in article.select(".post-author, [rel~='author'], .byline")]
    for segment in _segments(_meta_element(article)):
        if re.match(r"by\s", segment, re.IGNORECASE):
            candidates.append(segment)
    if not candidates:
        meta = page.find("meta", attrs={"name": "author"})
        if meta and meta.get("content"):
            candidates.append(meta["content"])

    for candidate in candidates:
        for pattern in _DATE_PATTERNS:
            candidate = pattern.sub("", candidate)
        names = _split_names(candidate)
        if names:
            return " and ".join(names)
    return None


def _body(article):
    container = article.select_one(".post-content") or article
    for junk in container.select(_JUNK):
        junk.decompose()

    blocks = []
    for element in container.find_all(_BLOCK_TAGS):
        if element.find_parent(_BLOCK_TAGS) is not None:
            continue
        text = _clean(element.get_text())
        if text:
            blocks.append(text)
    return "\n\n".join(blocks)


def _listing_entries(soup, listing_url):
    listing = urlparse(listing_url)
    section = [s for s in listing.path.split("/") if s]
    scope = soup.find("main") or soup
    anchors = scope.select(".post-card a[href]") or scope.find_all("a", href=True)

    entries = []
    seen = set()
    for anchor in anchors:
        url, _ = urldefrag(urljoin(listing_url, anchor["href"]))
        parsed = urlparse(url)
        parts = [p for p in parsed.path.split("/") if p]
        # A release lives at <section>/<slug>/ and nothing deeper.
        if parsed.netloc != listing.netloc or parts[:-1] != section or len(parts) != len(section) + 1:
            continue
        if url in seen:
            continue
        seen.add(url)

        listed = None
        card = anchor.find_parent(class_="post-card")
        if card is not None:
            span = card.find("span")
            listed = _date_from_text(span.get_text()) if span else None
        entries.append((url, listed))
    return entries


def _next_page_url(soup, page_url):
    link = soup.select_one('link[rel~="next"], a[rel~="next"]')
    if link is None:
        for anchor in soup.find_all("a", href=True):
            classes = " ".join(anchor.get("class", [])).lower()
            if "disabled" in classes or anchor.get("aria-disabled") == "true":
                continue
            label = _clean(anchor.get_text()).lower()
            aria = anchor.get("aria-label", "").strip().lower()
            if label in _NEXT_LABELS or aria in _NEXT_LABELS or re.search(r"\bnext\b", classes):
                link = anchor
                break
    if link is None:
        return None
    return urljoin(page_url, link["href"])


def extract(fetch, listing_url):
    # Walk every listing page, keeping the first-seen order of release URLs.
    releases = {}
    visited_pages = set()
    page_url = listing_url
    while page_url and page_url not in visited_pages:
        visited_pages.add(page_url)
        soup = BeautifulSoup(fetch(page_url), "html.parser")
        for url, listed_date in _listing_entries(soup, listing_url):
            releases.setdefault(url, listed_date)
        page_url = _next_page_url(soup, page_url)

    records = []
    for url, listed_date in releases.items():
        page = BeautifulSoup(fetch(url), "html.parser")
        article = (page.select_one("article.post") or page.find("article")
                   or page.find("main") or page)

        title = _title(article, page)
        published = _published_date(page, article) or listed_date
        author = _author(article, page)
        body = _body(article)

        records.append({
            "url": url,
            "title": title,
            "date": published,
            "author": author,
            "body": body,
        })

    records.sort(key=lambda r: r["date"] or "", reverse=True)
    return records
