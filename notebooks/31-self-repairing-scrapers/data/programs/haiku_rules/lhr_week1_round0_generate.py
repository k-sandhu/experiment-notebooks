import re
from urllib.parse import urljoin, urlsplit, urlunsplit, parse_qs

from bs4 import BeautifulSoup
from dateutil import parser as dateparser

RELEASE_PATH = re.compile(r"^/press-room/\d{4}/[^/]+/?$")
PAGE_PATH = re.compile(r"/page/\d+/?$")
PAGE_KEYS = {"page", "p", "paged", "pg", "offset", "start"}
NEXT_TEXT = re.compile(r"^\s*(next|older|more|next page|>|›|»)\s*$", re.I)
TITLE_WORDS = re.compile(
    r"\b(head|director|manager|officer|editor|chief|spokes\w*|communications|press|analyst|partner|executive|lead|assistant)\b",
    re.I,
)
MAX_PAGES = 500


def _text(node):
    return " ".join(node.get_text(" ", strip=True).split()) if node else ""


def _strip_fragment(url):
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, parts.query, ""))


def _is_next(a):
    classes = [c.lower() for c in a.get("class", [])]
    if any("disabled" in c for c in classes) or a.get("aria-disabled") == "true":
        return False
    rels = [r.lower() for r in a.get("rel", [])]
    return "next" in rels or any("next" in c for c in classes) or bool(NEXT_TEXT.match(_text(a)))


def _to_date(value):
    value = (value or "").strip()
    if not value:
        return None
    try:
        return dateparser.isoparse(value).date().isoformat()
    except (ValueError, OverflowError):
        pass
    try:
        return dateparser.parse(value, dayfirst=True, fuzzy=True).date().isoformat()
    except (ValueError, OverflowError):
        return None


def _authors(soup, article):
    meta = soup.find("meta", attrs={"name": "author"})
    if meta and meta.get("content"):
        raw = meta["content"]
    else:
        node = article.select_one(".press-byline, .byline, [rel~=author], .author")
        raw = _text(node)

    raw = re.sub(r"\([^)]*\)", "", raw)
    raw = re.sub(r"^\s*by\s+", "", raw, flags=re.I)

    names = []
    for part in re.split(r",|&|\band\b", raw, flags=re.I):
        part = re.split(r"\s+[-–—|]\s+", part)[0].strip(" .;:")
        if not part or TITLE_WORDS.search(part):
            continue
        if part not in names:
            names.append(part)

    return " and ".join(names) if names else None


def _parse_release(html, url, listing_date):
    soup = BeautifulSoup(html, "html.parser")
    article = soup.select_one(".press-article") or soup.find("main") or soup

    h1 = article.find("h1", class_="press-title") or article.find("h1") or soup.find("h1")
    title = _text(h1)
    if not title:
        title = re.sub(r"\s*\|\s*[^|]*$", "", _text(soup.title)).strip()

    date = None
    meta_date = (
        soup.find("meta", attrs={"property": "article:published_time"})
        or soup.find("meta", attrs={"name": "article:published_time"})
    )
    if meta_date and meta_date.get("content"):
        date = _to_date(meta_date["content"])
    if not date:
        date = _to_date(_text(article.select_one(".press-date")))
    if not date:
        date = listing_date

    content = article.select_one(".press-content, [itemprop=articleBody]") or article
    paragraphs = []
    for el in content.find_all(["p", "h2", "h3", "h4", "li"]):
        if el.find_parent(["p", "li", "h2", "h3", "h4"]) is not None:
            continue
        text = _text(el)
        if text:
            paragraphs.append(text)

    return {
        "url": url,
        "title": title,
        "date": date,
        "author": _authors(soup, article),
        "body": "\n\n".join(paragraphs),
    }


def extract(fetch, listing_url):
    listing_parts = urlsplit(listing_url)
    host = listing_parts.netloc
    listing_path = listing_parts.path

    queue = [listing_url]
    visited_pages = set()
    release_urls = []
    card_dates = {}

    while queue:
        page_url = queue.pop(0)
        if page_url in visited_pages:
            continue
        if len(visited_pages) >= MAX_PAGES:
            break
        visited_pages.add(page_url)

        soup = BeautifulSoup(fetch(page_url), "html.parser")

        for a in soup.find_all("a", href=True):
            url = _strip_fragment(urljoin(page_url, a["href"].strip()))
            parts = urlsplit(url)
            if parts.netloc != host:
                continue

            if RELEASE_PATH.match(parts.path):
                if url not in card_dates:
                    release_urls.append(url)
                    card_date = a.select_one(".press-card__date")
                    card_dates[url] = _to_date(_text(card_date)) if card_date else None
                continue

            if url in visited_pages or not parts.path.startswith(listing_path):
                continue

            keys = {k.lower() for k in parse_qs(parts.query)}
            if (parts.path == listing_path and keys & PAGE_KEYS) or PAGE_PATH.search(parts.path) or _is_next(a):
                queue.append(url)

    records = []
    for url in release_urls:
        records.append(_parse_release(fetch(url), url, card_dates.get(url)))

    records.sort(key=lambda r: r["date"] or "", reverse=True)
    return records
