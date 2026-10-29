import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from dateutil import parser as date_parser


_SKIP_TAGS = {"nav", "header", "footer", "form", "aside", "script", "style", "button"}
_SKIP_CLASSES = {
    "about", "contact", "source", "byline", "author", "share", "social",
    "related", "newsletter", "tags", "cookie", "cookies",
}
_BYLINE_CLASSES = {"byline", "author"}
_BLOCK_TAGS = ["p", "li", "h2", "h3", "h4", "blockquote"]
_MONTH = r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?"
_DATELINE = re.compile(_MONTH + r"\s+\d{1,2},\s+\d{4}\s*/")
_BY_PREFIX = re.compile(r"^\s*by\b[\s:,-]*", re.IGNORECASE)
_NEXT_TEXT = re.compile(r"^\s*(next|older|more|next page|\u203a|\u00bb)\s*$", re.IGNORECASE)


def _clean(text):
    return re.sub(r"\s+", " ", text).strip()


def _text(tag):
    for br in tag.find_all("br"):
        br.replace_with(" ")
    return _clean(tag.get_text())


def _has_class(tag, names):
    return bool({c.lower() for c in (tag.get("class") or [])} & names)


def _in_skipped_block(el, container):
    node = el
    while node is not None and node is not container:
        if node.name in _SKIP_TAGS or _has_class(node, _SKIP_CLASSES):
            return True
        node = node.parent
    return False


def _is_boilerplate(block, text):
    if re.match(r"media contact", text, re.IGNORECASE) or re.match(r"SOURCE\b", text):
        return True
    lead = block.find(True)
    return (
        lead is not None
        and lead.name == "strong"
        and re.match(r"about\s", text, re.IGNORECASE) is not None
    )


def _title(soup):
    h1 = soup.select_one("main h1") or soup.find("h1")
    if h1:
        return _text(h1)
    if soup.title and soup.title.string:
        return _clean(soup.title.string.split(" | ")[0])
    return None


def _published_date(soup, container, url):
    meta = (
        soup.find("meta", attrs={"property": "article:published_time"})
        or soup.find("meta", attrs={"itemprop": "datePublished"})
        or soup.find("meta", attrs={"name": re.compile(r"^(pubdate|publish-?date|dc\.date\.issued)$", re.I)})
    )
    time_tag = soup.find("time", attrs={"itemprop": "datePublished"})

    raw_values = []
    if meta and meta.get("content"):
        raw_values.append(meta["content"])
    if time_tag:
        raw_values.append(time_tag.get("datetime") or time_tag.get_text())

    for raw in raw_values:
        try:
            return date_parser.parse(raw).date().isoformat()
        except (ValueError, OverflowError):
            pass

    # The dateline ("CITY, Region, Sept. 28, 2026 /Wire/ --") is the release's first-publication date.
    match = _DATELINE.search(container.get_text()[:600])
    if match:
        dateline = match.group(0).replace(".", "").rstrip(" /")
        return date_parser.parse(dateline).date().isoformat()

    raise ValueError(f"No publication date found on {url}")


def _authors(soup):
    byline = soup.find(
        lambda t: t.name in {"p", "div", "span", "address", "li", "cite", "small", "em", "section", "h4"}
        and _has_class(t, _BYLINE_CLASSES)
    )
    text = _text(byline) if byline else ""
    if not text:
        meta = soup.find("meta", attrs={"name": "author"})
        text = meta.get("content", "") if meta else ""
        # Organisation names in the author meta tag are not a person credit.
        if re.search(r"co-?operative|grain|newsroom|communications|office", text, re.IGNORECASE):
            text = ""

    text = _BY_PREFIX.sub("", _clean(text))
    names = []
    for part in re.split(r";|,?\s+and\s+|\s+&\s+", text):
        name = re.split(r",|\s[-\u2013|]\s", part)[0].strip()
        if name and name not in names:
            names.append(name)
    return " and ".join(names) if names else None


def _body(container):
    paragraphs = []
    for block in container.find_all(_BLOCK_TAGS):
        if block.find(_BLOCK_TAGS) or _in_skipped_block(block, container):
            continue
        text = _text(block)
        if not text or _is_boilerplate(block, text):
            continue
        paragraphs.append(text)
    return "\n\n".join(paragraphs)


def _next_page(soup, page_url):
    link = soup.find(["link", "a"], rel="next")
    if link is None:
        for a in soup.find_all("a", href=True):
            if _NEXT_TEXT.match(a.get_text()) or _has_class(a, {"next"}):
                link = a
                break
    return urljoin(page_url, link["href"]) if link and link.get("href") else None


def _parse_release(fetch, url):
    soup = BeautifulSoup(fetch(url), "html.parser")
    container = soup.select_one(".pr-text") or soup.select_one("main") or soup.body or soup
    return {
        "url": url,
        "title": _title(soup),
        "date": _published_date(soup, container, url),
        "author": _authors(soup),
        "body": _body(container),
    }


def extract(fetch, listing_url):
    records = []
    seen_urls = set()
    seen_pages = set()
    page_url = listing_url

    while page_url and page_url not in seen_pages:
        seen_pages.add(page_url)
        soup = BeautifulSoup(fetch(page_url), "html.parser")
        base = soup.find("base", href=True)
        base_url = urljoin(page_url, base["href"]) if base else page_url

        links = soup.select(".pr-list .pr a[href]") or soup.select(".pr a[href]")
        for link in links:
            url = urljoin(base_url, link["href"])
            if url not in seen_urls:
                seen_urls.add(url)
                records.append(_parse_release(fetch, url))

        page_url = _next_page(soup, base_url)

    records.sort(key=lambda record: record["date"], reverse=True)
    return records
