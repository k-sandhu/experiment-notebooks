import datetime
import re
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

BLOCK_TAGS = ["p", "h2", "h3", "h4", "h5", "h6", "li", "blockquote", "pre", "figcaption", "dt", "dd"]
CHROME_TAGS = {"nav", "header", "footer", "aside"}
NON_BODY_CLASS = re.compile(
    r"about|share|newsletter|related|tag|contact|cookie|byline|pubdate|downloads", re.I
)
BODY_CLASS = re.compile(r"body", re.I)
UPDATED_CLASS = re.compile(r"updat|revis|review|modif", re.I)
UPDATED_TEXT = re.compile(r"\b(updated|revised|reviewed|modified)\b", re.I)
PUB_CLASS = re.compile(r"pub|first|issued|released", re.I)
DATE_CLASS = re.compile(r"date", re.I)
NOT_PUB_DATE_CLASS = re.compile(r"event|closing|effective|deadline|period|reference|next", re.I)
AUTHOR_CLASS = re.compile(r"author|byline", re.I)
ROLE_CLASS = re.compile(r"role|title|position|job", re.I)
AUTHOR_SPLIT = re.compile(r"\s*(?:,|;|\u00b7|\||&|\band\b)\s*", re.I)
ITEM_SELECTOR = "li.news-item, article.news-item, .card"
NEXT_LABELS = {"next", "next page", "older", "older releases", "\u203a", "\u00bb"}
MAX_LISTING_PAGES = 200
JOB_WORDS = {
    "head", "director", "chief", "statistician", "statisticians", "analyst", "analysts",
    "manager", "officer", "economist", "economists", "senior", "deputy", "lead", "team",
    "principal", "assistant", "unit", "division", "office", "of", "for", "the", "and",
    "editor", "spokesperson", "correspondent",
}
PARTICLES = {"de", "van", "von", "der", "da", "del", "la", "le"}
MONTH_NAMES = [
    "january", "february", "march", "april", "may", "june", "july", "august",
    "september", "october", "november", "december",
]
MONTHS = {name: i for i, name in enumerate(MONTH_NAMES, 1)}
MONTHS.update({name[:3]: i for i, name in enumerate(MONTH_NAMES, 1)})
MONTHS["sept"] = 9
DATE_PATTERNS = [
    (re.compile(r"(\d{4})-(\d{1,2})-(\d{1,2})"), "ymd"),
    (re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})"), "dmy"),
    (re.compile(r"(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]{3,})\.?,?\s+(\d{4})"), "dMy"),
    (re.compile(r"([A-Za-z]{3,})\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})"), "Mdy"),
]


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
    base_path = urlsplit(listing_url).path
    found = []
    visited = set()
    queue = [listing_url]
    while queue and len(visited) < MAX_LISTING_PAGES:
        page_url = queue.pop(0)
        if page_url in visited:
            continue
        visited.add(page_url)
        soup = BeautifulSoup(fetch(page_url), "html.parser")
        found.extend(_listing_items(soup, page_url))
        queue.extend(u for u in _page_links(soup, page_url, base_path) if u not in visited)
    return found


def _listing_items(soup, page_url):
    found = []
    for item in soup.select(ITEM_SELECTOR):
        link = (
            item.select_one("a.news-link[href]")
            or item.select_one("h1 a[href], h2 a[href], h3 a[href], h4 a[href]")
            or item.find("a", href=True)
        )
        if link is None:
            continue
        found.append((urljoin(page_url, link["href"]), _item_date(item)))
    return found


def _item_date(item):
    for t in item.find_all("time"):
        value = _parse_date(t.get("datetime")) or _parse_date(_text(t))
        if value:
            return value
    for el in item.find_all(class_=DATE_CLASS):
        value = _parse_date(_text(el))
        if value:
            return value
    return None


def _page_links(soup, current_url, base_path):
    links = []
    for tag in soup.select("link[rel~=next][href], a[rel~=next][href]"):
        links.append(urljoin(current_url, tag["href"]))
    for a in soup.find_all("a", href=True):
        url = urljoin(current_url, a["href"])
        label = _text(a).lower()
        aria = (a.get("aria-label") or "").strip().lower()
        if label in NEXT_LABELS or aria in NEXT_LABELS:
            links.append(url)
        target = urlsplit(url)
        if target.path == base_path and re.search(r"(?:^|&)page=\d+", target.query):
            links.append(url)
    return links


def _parse_release(html, url, listing_date):
    soup = BeautifulSoup(html, "html.parser")
    article = soup.find("article") or soup.find("main") or soup
    h1 = article.find("h1") or soup.find("h1")
    date = _release_date(article) or listing_date
    if date is None:
        raise ValueError("no publication date found for " + url)
    return {
        "url": url,
        "title": _title(soup, h1),
        "date": date,
        "author": _author(article),
        "body": _body(article),
    }


def _title(soup, h1):
    if h1 is not None and _text(h1):
        return _text(h1)
    title = soup.find("title")
    return _text(title).split(" | ")[0] if title is not None else ""


def _release_date(article):
    # Prefer the first-publication date; skip anything marked as updated/revised
    fallback = None
    for el in article.find_all(True):
        classes = _classes(el)
        if el.name != "time" and not DATE_CLASS.search(classes):
            continue
        chain = _chain(el, article)
        chain_classes = " ".join(_classes(node) for node in chain)
        if UPDATED_CLASS.search(chain_classes) or NOT_PUB_DATE_CLASS.search(chain_classes):
            continue
        text = _text(el)
        cut = UPDATED_TEXT.search(text)
        if cut:
            text = text[:cut.start()]
        value = _parse_date(el.get("datetime")) or _parse_date(text)
        if value is None:
            continue
        if PUB_CLASS.search(chain_classes):
            return value
        if fallback is None:
            fallback = value
    return fallback


def _author(article):
    names = []
    for el in article.find_all(class_=AUTHOR_CLASS):
        if ROLE_CLASS.search(_classes(el)):
            continue
        if any(AUTHOR_CLASS.search(_classes(anc)) for anc in el.parents):
            continue
        text = _text(el)
        text = re.sub(r"^(written\s+)?by\s*[:\-]?\s+", "", text, flags=re.I)
        for piece in AUTHOR_SPLIT.split(text):
            piece = piece.strip(" .")
            if _is_name(piece) and piece not in names:
                names.append(piece)
    return " and ".join(names) or None


def _is_name(text):
    words = text.split()
    if not 2 <= len(words) <= 5:
        return False
    for w in words:
        if w.lower() in JOB_WORDS:
            return False
        if not (w[0].isupper() or w.lower() in PARTICLES):
            return False
        if not w.replace("'", "").replace("-", "").replace(".", "").isalpha():
            return False
    return True


def _body(article):
    container = article.find(class_=BODY_CLASS)
    if container is None:
        container = article
    blocks = []
    for el in container.find_all(BLOCK_TAGS):
        chain = _chain(el, container)
        # Nested blocks (e.g. p inside li) are already included in their parent
        if any(anc.name in BLOCK_TAGS for anc in chain[1:]):
            continue
        if any(node.name in CHROME_TAGS or NON_BODY_CLASS.search(_classes(node)) for node in chain):
            continue
        text = " ".join(el.get_text().split())
        if text:
            blocks.append(text)
    return "\n\n".join(blocks)


def _chain(el, stop):
    # The element itself plus its ancestors up to, but not including, stop
    nodes = [el]
    for node in el.parents:
        if node is stop:
            break
        nodes.append(node)
    return nodes


def _parse_date(text):
    if not text:
        return None
    matches = []
    for pattern, order in DATE_PATTERNS:
        for m in pattern.finditer(text):
            matches.append((m.start(), order, m))
    matches.sort(key=lambda item: item[0])
    for _, order, m in matches:
        try:
            if order == "ymd":
                y, mo, d = int(m[1]), int(m[2]), int(m[3])
            elif order == "dmy":
                d, mo, y = int(m[1]), int(m[2]), int(m[3])
            elif order == "dMy":
                d, mo, y = int(m[1]), _month_number(m[2]), int(m[3])
            else:
                mo, d, y = _month_number(m[1]), int(m[2]), int(m[3])
            return datetime.date(y, mo, d).isoformat()
        except ValueError:
            continue
    return None


def _month_number(name):
    key = name.lower()
    if key in MONTHS:
        return MONTHS[key]
    raise ValueError(name)


def _classes(el):
    if not el.name:
        return ""
    return " ".join(el.get("class", []))


def _text(el):
    return " ".join(el.get_text().split()) if el is not None else ""
