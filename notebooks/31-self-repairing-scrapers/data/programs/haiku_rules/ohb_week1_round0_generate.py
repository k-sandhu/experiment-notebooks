import re
from urllib.parse import urldefrag, urljoin, urlparse

from bs4 import BeautifulSoup, Comment
from dateutil import parser as date_parser


_MAX_PAGES = 100
_DATE_RE = re.compile(
    r"\b(?:\d{4}-\d{2}-\d{2}"
    r"|\d{1,2}\s+[A-Za-z]{3,9}\.?,?\s+\d{4}"
    r"|[A-Za-z]{3,9}\.?\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})\b"
)
_CONTAINER_TAGS = ("tr", "li", "article", "td", "div", "p")
_BLOCK_TAGS = (
    "p", "div", "li", "tr", "table", "ul", "ol", "blockquote",
    "h1", "h2", "h3", "h4", "h5", "h6",
)
_NOISE_ATTR = re.compile(
    r"\b(cookies?|share|sharing|social|newsletter|subscribe|related|tags?|breadcrumbs?"
    r"|footer|nav|navigation|contact-?box|about-?us)\b",
    re.I,
)
_PAGE_WORDS = {"next", "next page", "older", "older posts", "more"}
_TITLE_WORDS = {
    "manager", "director", "head", "chief", "officer", "editor", "spokesperson",
    "spokesman", "spokeswoman", "president", "ceo", "cfo", "coo", "cto", "executive",
    "secretary", "chair", "chairman", "partner", "lead", "vice", "senior", "general",
    "commercial", "managing", "operations", "finance", "financial", "sales",
    "marketing", "communications", "production", "technical", "of", "the", "for", "and",
}
_META_LINE = re.compile(
    r"^(first\s+published|published|posted|last\s+updated|updated|reviewed|posted\s+by|written\s+by)\s*:",
    re.I,
)
_BOILERPLATE_LINE = re.compile(
    r"^([«‹]?\s*back to\b|share (this|on|buttons?)\b|tags?\s*:|follow us\b|subscribe\b"
    r"|sign up\b|cookies?\b|related (news|links|articles|stories)\b|©|copyright\b"
    r"|all rights reserved|about (us|oakhill bakeries group|the group)\b"
    r"|notes? to (the )?(editors?|media)\b|(media|press|investor) (contacts?|enquiries|inquiries)\b"
    r"|contact:)",
    re.I,
)


def _clean(text):
    return re.sub(r"\s+", " ", text or "").strip()


def _parse_date(text):
    match = _DATE_RE.search(text or "")
    if not match:
        return None
    try:
        return date_parser.parse(match.group(0), fuzzy=True).date().isoformat()
    except (ValueError, OverflowError):
        return None


def _get(fetch, url):
    """Fetch a page; return None when the page is gone, re-raise other errors."""
    try:
        return fetch(url)
    except FetchError as error:
        if getattr(error, "status", None) in (404, 410):
            return None
        raise


def _block_of(element):
    for parent in element.parents:
        if parent.name in _CONTAINER_TAGS:
            return parent
    return element.parent


def _is_page_link(link, text):
    rel = link.get("rel") or []
    if isinstance(rel, str):
        rel = [rel]
    if "next" in (value.lower() for value in rel):
        return True
    label = _clean(text).lower()
    if label.isdigit() or label in {"›", "»", ">", ">>"}:
        return True
    return re.sub(r"[^a-z ]", "", label).strip() in _PAGE_WORDS


def _scan_listing(soup, page_url, host):
    """Return (dated release links, pagination links) found on one listing page."""
    releases, pages = [], []
    for link in soup.find_all("a", href=True):
        text = _clean(link.get_text(" "))
        if not text:
            continue
        url = urldefrag(urljoin(page_url, link["href"]))[0]
        if urlparse(url).netloc != host or url == page_url:
            continue
        block = _block_of(link)
        block_text = _clean(block.get_text(" ")) if block is not None else ""
        listing_date = _parse_date(block_text.replace(text, " ", 1))
        if listing_date:
            releases.append((url, listing_date))
        elif _is_page_link(link, text):
            pages.append(url)
    return releases, pages


def _find_heading(soup):
    for selector in ("h1", 'font[size="4"]', "h2"):
        for element in soup.select(selector):
            if _clean(element.get_text(" ")):
                return element
    return None


def _is_title(token):
    return token.lower().strip(".,") in _TITLE_WORDS


def _name_from_part(part):
    tokens = part.split()
    if not any(_is_title(token) for token in tokens):
        return part or None
    runs, run = [], []
    for token in tokens:
        if _is_title(token):
            if run:
                runs.append(run)
                run = []
        else:
            run.append(token)
    if run:
        runs.append(run)
    runs = [candidate for candidate in runs if len(candidate) >= 2]
    return " ".join(max(runs, key=len)) if runs else None


def _clean_author(raw):
    raw = re.sub(r"^by\s+", "", _clean(raw), flags=re.I)
    names = []
    for part in re.split(r"\s*(?:,|;|&|\band\b)\s*", raw, flags=re.I):
        name = _name_from_part(part.strip())
        if name and name not in names:
            names.append(name)
    return " and ".join(names) or None


def _parse_release(html, url, listing_date):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "iframe", "form"]):
        tag.extract()

    heading = _find_heading(soup)
    if heading is not None:
        title = _clean(heading.get_text(" "))
        main = heading.find_parent("td") or heading.parent
        heading.extract()
    else:
        page_title = soup.title.get_text() if soup.title else ""
        title = _clean(page_title.split(" - ", 1)[-1])
        main = soup.body or soup

    for link in main.find_all("a", href=True):
        label = _clean(link.get_text(" ")).lstrip("«‹<» ").lower()
        if label.startswith("back to"):
            parent = link.find_parent("p")
            link.extract()
            if parent is not None and not _clean(parent.get_text(" ")):
                parent.extract()

    for element in main.find_all(True):
        attrs = " ".join(element.get("class") or []) + " " + (element.get("id") or "")
        if _NOISE_ATTR.search(attrs):
            element.extract()

    for string in list(main.find_all(string=True)):
        if isinstance(string, Comment):
            continue
        string.replace_with(re.sub(r"\s+", " ", str(string)))
    for br in main.find_all("br"):
        br.replace_with("\n")
    for block in main.find_all(_BLOCK_TAGS):
        block.insert_before("\n")
        block.insert_after("\n")

    lines = [_clean(line) for line in main.get_text().split("\n")]

    release_date = None
    author = None
    for line in lines:
        if release_date is None:
            match = re.match(
                r"^(?:first\s+published|published|posted)\s*(?:on)?\s*:?\s*(.*)$", line, re.I
            )
            if match:
                release_date = _parse_date(match.group(1))
        if author is None:
            match = re.match(r"^(?:posted|written|authored)\s+by\s*:?\s*(.+)$", line, re.I)
            if match is None:
                match = re.match(r"^(?:author|by)\s*:\s*(.+)$", line, re.I)
            if match:
                author = _clean_author(match.group(1))
    release_date = release_date or listing_date

    paragraphs, current = [], []
    for line in lines:
        if not line or _META_LINE.match(line) or _BOILERPLATE_LINE.match(line):
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        current.append(line)
    if current:
        paragraphs.append(" ".join(current))

    return {
        "url": url,
        "title": title,
        "date": release_date,
        "author": author,
        "body": "\n\n".join(paragraphs),
    }


def extract(fetch, listing_url):
    listing_url = urldefrag(listing_url)[0]
    host = urlparse(listing_url).netloc

    queue = [listing_url]
    visited = set()
    found = {}
    while queue and len(visited) < _MAX_PAGES:
        page_url = queue.pop(0)
        if page_url in visited:
            continue
        visited.add(page_url)
        html = fetch(page_url) if page_url == listing_url else _get(fetch, page_url)
        if html is None:
            continue
        releases, pages = _scan_listing(BeautifulSoup(html, "html.parser"), page_url, host)
        for url, listing_date in releases:
            found.setdefault(url, listing_date)
        queue.extend(page for page in pages if page not in visited)

    records = []
    for url, listing_date in found.items():
        html = _get(fetch, url)
        if html is None:
            continue
        records.append(_parse_release(html, url, listing_date))

    records.sort(key=lambda record: record["date"] or "", reverse=True)
    return records
