import re
from urllib.parse import urljoin, urlsplit, urlunsplit, parse_qs

from bs4 import BeautifulSoup, NavigableString, Tag
from dateutil import parser as dateparser

PAGE_PATH = re.compile(r"/page/\d+/?$")
PAGE_KEYS = {"page", "p", "paged", "pg", "offset", "start"}
NEXT_TEXT = re.compile(r"^\s*(next|older|more|next page|>|›|»)\s*$", re.I)
PAGER_CLASS = re.compile(r"pagination|pager", re.I)
CHROME_CLASS = re.compile(r"related|share|cookie|newsletter|lhr-nav|lhr-footer|lhr-header", re.I)
DATE_TEXT = re.compile(
    r"\d{4}-\d{2}-\d{2}"
    r"|\d{1,2}\s+[A-Za-z]{3,9}\.?\s+\d{4}"
    r"|[A-Za-z]{3,9}\.?\s+\d{1,2},?\s+\d{4}"
    r"|\d{1,2}/\d{1,2}/\d{4}"
)
UPDATED_SPLIT = re.compile(r"updated|reviewed|modified|revised", re.I)
BYLINE_PREFIX = re.compile(
    r"^\s*(?:(?:words|written|text|story|reported|reporting|photography)\s+)?by\b:?\s*"
    r"|^\s*words\s*:\s*",
    re.I,
)
TITLE_WORDS = re.compile(
    r"\b(head|director|manager|officer|editor|chief|spokes\w*|communications|press|analyst|partner|executive|lead|assistant)\b",
    re.I,
)
ORG_WORDS = re.compile(r"\b(office|team|department|lumen|retail|ltd|limited|plc|company)\b", re.I)
SKIP_HEADING = re.compile(
    r"^\s*(about (us|lumen home retail)|related\b|tags?\s*$|share\b|contact\b|(media|press) (contact|enquiries)\b)",
    re.I,
)
ABOUT_PARA = re.compile(r"^\s*about (us|lumen home retail)\b", re.I)
NOISE = ", ".join([
    "head", "script", "style", "noscript", "template", "form", "button", "input", "select",
    "iframe", "svg", "nav", "aside", "footer", "header",
    ".press-related", ".press-byline", ".press-date", ".press-title", ".press-about",
    ".press-share", ".press-tags", ".press-contact",
    "[class*=share-]", "[class*=cookie]", "[class*=newsletter]", "[class*=related]",
    "[class*=tags]", "[class*=contact]", "[class*=about-us]",
])
BLOCK_TAGS = {
    "address", "article", "aside", "blockquote", "dd", "div", "dl", "dt", "figcaption", "figure",
    "footer", "h1", "h2", "h3", "h4", "h5", "h6", "header", "hr", "li", "main", "ol", "p", "pre",
    "section", "table", "tbody", "td", "th", "thead", "tr", "ul",
}
HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
MAX_PAGES = 500


def _text(node, sep=""):
    return " ".join(node.get_text(sep).split()) if node is not None else ""


def _strip_fragment(url):
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, parts.query, ""))


def _absolute(page_url, href, host):
    url = _strip_fragment(urljoin(page_url, href.strip()))
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https") or parts.netloc.lower() != host:
        return None
    return url


def _is_next(a):
    classes = [c.lower() for c in a.get("class", [])]
    if any("disabled" in c for c in classes) or a.get("aria-disabled") == "true":
        return False
    rels = [r.lower() for r in a.get("rel", [])]
    return "next" in rels or any("next" in c for c in classes) or bool(NEXT_TEXT.match(_text(a)))


def _in_pager(a):
    for parent in a.parents:
        if not isinstance(parent, Tag):
            continue
        classes = " ".join(parent.get("class", []))
        label = parent.get("aria-label") or ""
        if PAGER_CLASS.search(classes) or PAGER_CLASS.search(label):
            return True
    return False


def _in_chrome(a):
    for parent in a.parents:
        if not isinstance(parent, Tag):
            continue
        if parent.name in {"nav", "header", "footer"}:
            return True
        if CHROME_CLASS.search(" ".join(parent.get("class", []))):
            return True
    return False


def _to_date(value):
    value = " ".join((value or "").split())
    if not value:
        return None
    try:
        return dateparser.isoparse(value).date().isoformat()
    except (ValueError, OverflowError):
        pass
    match = DATE_TEXT.search(value)
    if not match:
        return None
    try:
        return dateparser.parse(match.group(0), dayfirst=True).date().isoformat()
    except (ValueError, OverflowError):
        return None


def _card_date(a):
    node = a.select_one(".press-card__date") or a.find(class_=re.compile(r"date"))
    return _to_date(_text(node, " ")) if node is not None else None


def _published_date(soup, article):
    for attrs in (
        {"property": "article:published_time"},
        {"name": "article:published_time"},
        {"itemprop": "datePublished"},
    ):
        node = soup.find(attrs=attrs)
        if node is None:
            continue
        date = _to_date(node.get("content") or node.get("datetime") or _text(node, " "))
        if date:
            return date
    node = article.select_one(".press-date")
    if node is not None:
        return _to_date(UPDATED_SPLIT.split(_text(node, " "))[0])
    return None


def _title(soup, article):
    h1 = article.select_one("h1.press-title") or article.find("h1") or soup.find("h1")
    title = _text(h1)
    if not title:
        og = soup.find("meta", attrs={"property": "og:title"})
        title = " ".join(((og.get("content") if og is not None else "") or "").split())
    if not title and soup.title is not None:
        title = re.sub(r"\s*\|\s*[^|]*$", "", _text(soup.title)).strip()
    return title


def _authors(soup, article):
    node = article.select_one(".press-byline, .byline, [rel~=author], .author")
    raw = _text(node, " ")
    if not raw:
        meta = soup.find("meta", attrs={"name": "author"})
        raw = (meta.get("content") or "") if meta is not None else ""
    raw = re.sub(r"\([^)]*\)", " ", " ".join(raw.split()))
    raw = BYLINE_PREFIX.sub("", raw)

    names = []
    for part in re.split(r",|;|&|\band\b", raw, flags=re.I):
        part = re.split(r"\s+[-\u2013\u2014|]\s+", part)[0].strip(" .;:")
        part = BYLINE_PREFIX.sub("", part).strip(" .;:")
        if not re.search(r"[A-Za-z]", part):
            continue
        if TITLE_WORDS.search(part) or ORG_WORDS.search(part):
            continue
        if part not in names:
            names.append(part)

    return " and ".join(names) if names else None


def _blocks(node):
    blocks = []
    buf = []

    def flush(heading):
        text = " ".join("".join(buf).split())
        buf.clear()
        if text:
            blocks.append((heading, text))

    def walk(parent, heading):
        for child in parent.children:
            if isinstance(child, Tag):
                if child.name == "br":
                    buf.append(" ")
                elif child.name in BLOCK_TAGS:
                    flush(heading)
                    walk(child, child.name in HEADING_TAGS)
                    flush(child.name in HEADING_TAGS)
                else:
                    walk(child, heading)
            elif type(child) is NavigableString:
                buf.append(str(child))

    walk(node, False)
    flush(False)
    return blocks


def _parse_release(html, url, listing_date):
    soup = BeautifulSoup(html, "html.parser")
    article = soup.select_one(".press-article") or soup.find("main") or soup

    title = _title(soup, article)
    date = _published_date(soup, article) or listing_date
    author = _authors(soup, article)

    container = article.select_one(".press-content, [itemprop=articleBody]") or article
    for node in container.select(NOISE):
        node.decompose()
    for h1 in container.find_all("h1"):
        h1.decompose()

    paragraphs = []
    skipping = False
    for is_heading, text in _blocks(container):
        if is_heading:
            skipping = bool(SKIP_HEADING.match(text))
        if skipping or ABOUT_PARA.match(text):
            continue
        paragraphs.append(text)

    return {
        "url": url,
        "title": title,
        "date": date,
        "author": author,
        "body": "\n\n".join(paragraphs),
    }


def extract(fetch, listing_url):
    listing_url = _strip_fragment(listing_url)
    listing = urlsplit(listing_url)
    host = listing.netloc.lower()
    base = listing.path.rstrip("/")
    release_path = re.compile("^" + re.escape(base) + r"/\d{4}/[^/]+/?$")

    def under_listing(path):
        p = path.rstrip("/")
        return p == base or p.startswith(base + "/")

    queue = [listing_url]
    visited = set()
    releases = {}

    while queue:
        page_url = queue.pop(0)
        if page_url in visited:
            continue
        if len(visited) >= MAX_PAGES:
            break
        visited.add(page_url)

        try:
            html = fetch(page_url)
        except FetchError as err:
            if page_url != listing_url and err.status == 404:
                continue
            raise
        soup = BeautifulSoup(html, "html.parser")

        for link in soup.find_all("link", href=True):
            if "next" in {r.lower() for r in link.get("rel", [])}:
                url = _absolute(page_url, link["href"], host)
                if url and under_listing(urlsplit(url).path) and url not in visited and url not in queue:
                    queue.append(url)

        for a in soup.find_all("a", href=True):
            url = _absolute(page_url, a["href"], host)
            if url is None:
                continue
            parts = urlsplit(url)
            path = parts.path
            is_card = "press-card" in a.get("class", [])

            if is_card or release_path.match(path):
                if is_card or not _in_chrome(a) or _in_pager(a):
                    key = url.rstrip("/")
                    if key not in releases:
                        releases[key] = {"url": url, "card": None}
                    if releases[key]["card"] is None:
                        releases[key]["card"] = _card_date(a)
                continue

            if _in_chrome(a) and not _in_pager(a):
                continue
            if not under_listing(path) or url in visited or url in queue:
                continue

            keys = {k.lower() for k in parse_qs(parts.query)}
            paged = (
                (path.rstrip("/") == base and bool(keys & PAGE_KEYS))
                or PAGE_PATH.search(path)
                or _in_pager(a)
                or _is_next(a)
            )
            if paged:
                queue.append(url)

    records = []
    for info in releases.values():
        records.append(_parse_release(fetch(info["url"]), info["url"], info["card"]))

    records.sort(key=lambda r: r["date"] or "", reverse=True)
    return records
