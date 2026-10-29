import re
from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup

BLOCK_TAGS = ["p", "h2", "h3", "h4", "h5", "h6", "li", "blockquote"]
DATE_RE = re.compile(r"(\d{1,2})\.(\d{1,2})\.(\d{4})")
ISSUE_RE = re.compile(r"Date of issue:?\s*(\d{1,2}\.\d{1,2}\.\d{4})", re.I)
NEXT_LABELS = {"next", "next page", ">", "\u203a", "\u00bb"}


def _clean(text):
    return " ".join((text or "").split())


def _parse_date(text):
    """Convert a dd.mm.yyyy string to YYYY-MM-DD, or None if no date is found."""
    m = DATE_RE.search(text or "")
    if not m:
        return None
    d, mo, y = m.groups()
    return datetime(int(y), int(mo), int(d)).strftime("%Y-%m-%d")


def _next_page(soup, current_url):
    """Find the URL of the next listing page, if the listing is paginated."""
    cand = soup.select_one('link[rel~="next"], a[rel~="next"]')
    if cand is None:
        for a in soup.find_all("a", href=True):
            label = _clean(a.get_text()).lower()
            aria = (a.get("aria-label") or "").lower()
            classes = " ".join(a.get("class", [])).lower()
            if (label in NEXT_LABELS
                    or re.search(r"\bnext\b", aria)
                    or re.search(r"\bnext\b", classes)):
                cand = a
                break
    if cand is None or not cand.get("href"):
        return None
    nxt = urljoin(current_url, cand["href"])
    return None if nxt == current_url else nxt


def _listing_items(fetch, listing_url):
    """Collect url, title and listing date from every page of the listing."""
    items = []
    visited = set()
    page_url = listing_url
    while page_url and page_url not in visited:
        visited.add(page_url)
        soup = BeautifulSoup(fetch(page_url), "html.parser")
        for row in soup.select(".notice-row"):
            link = row.select_one("a.notice-title") or row.find("a", href=True)
            if link is None or not link.get("href"):
                continue
            date_el = row.select_one(".notice-date")
            items.append({
                "url": urljoin(page_url, link["href"]),
                "title": _clean(link.get_text()),
                "date": _parse_date(date_el.get_text()) if date_el else None,
            })
        page_url = _next_page(soup, page_url)
    return items


def _author(soup, main):
    """Return the credited author name(s), or None when no person is credited."""
    candidates = [
        _clean(el.get_text())
        for el in main.select('[rel~="author"], .author-name, [itemprop="author"] [itemprop="name"]')
    ]
    if not candidates:
        block = main.select_one(".byline, .author, [itemprop='author']")
        if block is not None:
            candidates = [_clean(block.get_text())]
    if not candidates:
        meta = soup.find("meta", attrs={"name": "author"})
        if meta and meta.get("content"):
            candidates = [meta["content"]]

    names = []
    for candidate in candidates:
        candidate = re.sub(r"^by\s+", "", candidate, flags=re.I)
        for part in re.split(r";|&|\band\b", candidate):
            # Drop anything after a comma, which is usually a job title.
            name = part.split(",")[0].strip()
            if name and name not in names:
                names.append(name)
    return " and ".join(names) or None


def _body(main):
    """Return the main text of the release as paragraphs separated by blank lines."""
    box = main.select_one(".notice-text")
    fallback = box is None
    if fallback:
        box = main
    paragraphs = []
    for el in box.find_all(BLOCK_TAGS):
        if el.find_parent(BLOCK_TAGS) is not None:
            continue  # text is already covered by an enclosing block
        if fallback and (el.name == "h1" or set(el.get("class", [])) & {"ref", "date", "sig"}):
            continue
        text = _clean(el.get_text())
        if text:
            paragraphs.append(text)
    return "\n\n".join(paragraphs) or None


def _release(fetch, item):
    soup = BeautifulSoup(fetch(item["url"]), "html.parser")
    main = soup.find("main") or soup

    h1 = main.find("h1")
    title = _clean(h1.get_text()) if h1 else item["title"]

    # Use the "Date of issue" label only, never the "Effective" date.
    date = item["date"]
    meta = main.select_one("p.date")
    if meta is not None:
        m = ISSUE_RE.search(_clean(meta.get_text()))
        if m:
            date = _parse_date(m.group(1))

    return {
        "url": item["url"],
        "title": title,
        "date": date,
        "author": _author(soup, main),
        "body": _body(main),
    }


def extract(fetch, listing_url):
    items = _listing_items(fetch, listing_url)

    seen = set()
    records = []
    for item in items:
        if item["url"] in seen:
            continue
        seen.add(item["url"])
        records.append(_release(fetch, item))

    # Newest first; undated records go last.
    records.sort(key=lambda r: r["date"] or "", reverse=True)
    return records
