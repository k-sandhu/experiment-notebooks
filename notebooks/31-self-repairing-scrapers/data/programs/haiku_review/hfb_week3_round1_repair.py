import json
import re
from datetime import datetime, timezone
from html import escape
from urllib.parse import parse_qsl, quote, urlencode, urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup
from bs4.element import Comment, Doctype, NavigableString, Tag
from dateutil import parser as date_parser


API_PAGE_SIZE = 100
MAX_PAGES = 200

API_CALL = re.compile(r"fetch\(\s*['\"`]([^'\"`]*/api/[^'\"`]*)['\"`]")
# Epoch timestamps are long digit strings; short numbers are not treated as epochs.
EPOCH_TEXT = re.compile(r"-?\d{10,}(\.\d+)?")
HTML_TEXT = re.compile(r"<[a-zA-Z]")
HEADINGS = ["h1", "h2", "h3", "h4", "h5", "h6"]
BLOCK_TAGS = HEADINGS + ["p", "li", "blockquote", "pre", "td", "th", "figcaption", "dt", "dd", "div"]
DROP_TAGS = ["script", "style", "noscript", "template", "nav", "aside", "header", "footer",
             "form", "button", "input", "select", "textarea", "iframe", "svg"]
BOILERPLATE_HOOKS = ("share", "related", "tags", "newsletter", "cookie", "consent", "contact",
                     "boilerplate", "about-us", "breadcrumb", "social", "byline", "meta")

# Field names the API may use, most specific first. Updated and reviewed dates are never used.
TITLE_KEYS = ("headline", "title")
DATE_KEYS = ("firstPublishedAt", "first_published_at", "publishedAt", "published_at", "published")
AUTHOR_KEYS = ("byline", "author", "authors")
BODY_KEYS = ("body_html", "bodyHtml", "body", "content", "html")
ITEM_LIST_KEYS = ("data", "items", "results", "news")

# A heading that starts the standard boilerplate: everything from here on is dropped.
ABOUT_HEADING = re.compile(
    r"^(about\s+(us|harrow|the\s+(bank|group))\b.*|notes\s+to\s+editors?|"
    r"media\s+(contacts?|enquiries|inquiries)|press\s+(contacts?|enquiries|office)|"
    r"contact(\s+us)?|share(\s+this)?|related\b.*|tags?|further\s+information)$",
    re.I,
)
# Paragraphs that are boilerplate, contact boxes or related-link blocks.
BOILERPLATE_TEXT = re.compile(
    r"^(about\s+(us|harrow|the\s+(bank|group))\b|notes\s+to\s+editors?\b|"
    r"(media|press)\s+(contacts?|enquiries|inquiries|queries)\b|"
    r"for\s+(media|press)\s+(enquiries|inquiries|queries)\b|share\s+this\b|"
    r"related\s+(articles|news|links|content|releases)\b|tags?:|read\s+more\b|news\s+enquiries\b)",
    re.I,
)
# Standard "About" closing paragraph written without a heading, only when it is the last block.
FINAL_BOILERPLATE = re.compile(r"^harrow\s*(&|and)\s*finch\s+(bank|group)\s+(is|was)\s+(an?|the)\b", re.I)

JOB_WORDS = re.compile(
    r"\b(head|chief|director|manager|officer|economist|analyst|governor|president|ceo|cfo|coo|cto|"
    r"chair|senior|lead|partner|vice|secretary|editor|spokesperson|spokesman|spokeswoman|treasurer|"
    r"executive|adviser|advisor|specialist|counsel|representative|of|at|for)\b",
    re.I,
)
ORG_WORDS = re.compile(r"\b(team|office|newsroom|press|communications|media|staff|bank|department|desk)\b", re.I)
NAME_SEPARATORS = re.compile(r"\s*[,;|·•–—]\s*|\s+-\s+|\s+and\s+", re.I)


def extract(fetch, listing_url):
    # Article URL -> (API id, listing attributes) for every release found.
    candidates = {}
    first_soup = None
    page_url = listing_url
    visited = set()

    # Server-rendered article links and "next page" links, if any.
    while page_url and page_url not in visited and len(visited) < MAX_PAGES:
        visited.add(page_url)
        soup = BeautifulSoup(fetch(page_url), "html.parser")
        if first_soup is None:
            first_soup = soup
        for url in _html_article_urls(soup, listing_url, page_url):
            candidates.setdefault(url, (None, None))
        page_url = _html_next(soup, page_url)

    # The listing is filled in by JavaScript from a JSON API; page through all of it.
    api_url = _find_api_url(first_soup, listing_url)
    api_base = None
    if api_url:
        api_base = api_url.partition("?")[0].rstrip("/")
        for attrs in _walk_api(fetch, api_url):
            url = _item_url(attrs, listing_url)
            if url:
                candidates[url] = (attrs.get("id"), attrs)

    records = []
    for url, (known_id, listing) in candidates.items():
        try:
            records.append(_parse_release(fetch, url, api_base, known_id, listing or {}))
        except FetchError as exc:
            # A withdrawn release is skipped; other HTTP errors are real failures.
            if getattr(exc, "status", None) in (404, 410):
                continue
            raise

    # Newest first; releases without a date go last.
    records.sort(key=lambda r: (r["date"] is not None, r["date"] or ""), reverse=True)
    return records


def _parse_release(fetch, article_url, api_base, known_id, listing):
    soup = BeautifulSoup(fetch(article_url), "html.parser")

    # The release page is a shell; its content comes from the JSON API, keyed by data-item.
    holder = soup.find(attrs={"data-item": True}) or soup.find(attrs={"data-id": True})
    rid = (holder.get("data-item") or holder.get("data-id")) if holder is not None else None
    rid = rid or known_id
    detail = {}
    if rid and api_base:
        detail = _detail(_json_or_none(fetch(f"{api_base}/{quote(str(rid), safe='')}")))
    sources = [detail, listing]

    h1 = soup.find("h1")

    # The full headline from the release itself; the listing title may be shortened.
    title = _plain(_pick([detail], TITLE_KEYS))
    if not title and h1 is not None:
        title = _plain(h1.get_text())
    if not title:
        title = _plain(_pick([listing], TITLE_KEYS))

    # First publication date only; never "updated" or event dates.
    date = _first_date(sources, DATE_KEYS) or _iso_date(
        _meta(soup, "article:published_time", "date")
    )

    author = _author(sources, _meta(soup, "author"))

    body_html = _body_html(_pick([detail], BODY_KEYS))
    if not body_html:
        node = soup.select_one(".body")
        if node is not None and _clean_ws(node.get_text()) not in ("", "Loading…", "Loading..."):
            body_html = str(node)
    body = _body_text(body_html, title, author)

    return {
        "url": article_url,
        "title": title,
        "date": date,
        "author": author,
        "body": body,
    }


def _walk_api(fetch, api_url):
    base, _, query = api_url.partition("?")
    params = dict(parse_qsl(query))
    params["pageSize"] = str(API_PAGE_SIZE)
    seen = set()
    requested = set()
    next_url = None
    for page in range(1, MAX_PAGES + 1):
        if next_url is None:
            params["page"] = str(page)
            url = f"{base}?{urlencode(params)}"
        else:
            url = next_url
        # Never request the same address twice, so a looping "next" link cannot hang the walk.
        if url in requested:
            return
        requested.add(url)

        data = _json_or_none(fetch(url))
        items = _items_of(data)
        if items is None:
            return

        fresh = 0
        for item in items:
            if not isinstance(item, dict):
                continue
            attrs = _attributes(item)
            key = attrs.get("id") or attrs.get("slug") or attrs.get("url")
            if key is None or key in seen:
                continue
            seen.add(key)
            fresh += 1
            yield attrs

        # Stop when a page adds nothing new, so an API that ignores paging cannot loop.
        if not fresh or _no_more(data):
            return
        next_url = _api_next(data, url)


def _items_of(data):
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ITEM_LIST_KEYS:
            if isinstance(data.get(key), list):
                return data[key]
    return None


def _no_more(data):
    if not isinstance(data, dict):
        return False
    return any(data.get(key) is False for key in ("has_more", "hasMore", "has_next", "hasNext"))


def _api_next(data, url):
    if not isinstance(data, dict):
        return None
    links = data.get("links") if isinstance(data.get("links"), dict) else {}
    meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
    pagination = data.get("pagination") if isinstance(data.get("pagination"), dict) else {}
    candidates = (data.get("next"), data.get("next_url"), data.get("nextUrl"),
                  links.get("next"), meta.get("next"), pagination.get("next"))
    for value in candidates:
        if isinstance(value, dict):
            value = value.get("href")
        if isinstance(value, str) and value.strip().startswith(("/", "?", "http://", "https://")):
            return urljoin(url, value.strip())
    return None


def _find_api_url(soup, listing_url):
    for script in soup.find_all("script"):
        for match in API_CALL.finditer(script.get_text()):
            url = urljoin(listing_url, match.group(1))
            if "news" in urlsplit(url).path:
                return url
    return None


def _html_next(soup, page_url):
    tag = soup.find("link", rel=_is_next) or soup.find("a", rel=_is_next)
    if tag and tag.get("href"):
        return urljoin(page_url, tag["href"])
    return None


def _is_next(value):
    return bool(value) and "next" in value


def _html_article_urls(soup, listing_url, page_url):
    prefix = _section_url(listing_url) + "article/"
    for a in soup.find_all("a", href=True):
        url = _clean_url(urljoin(page_url, a["href"]))
        if url.startswith(prefix) and len(url) > len(prefix):
            yield url


def _item_url(attrs, listing_url):
    if attrs.get("slug"):
        return _clean_url(urljoin(_section_url(listing_url), "article/" + quote(str(attrs["slug"]), safe="")))
    if attrs.get("url"):
        return _clean_url(urljoin(listing_url, str(attrs["url"])))
    return None


def _attributes(item):
    # The API nests the fields under "attributes"; flatten them next to the id and type.
    merged = dict(item)
    nested = item.get("attributes")
    if isinstance(nested, dict):
        merged.update(nested)
    return merged


def _detail(data):
    if not isinstance(data, dict):
        return {}
    for key in ("data", "article", "item", "news"):
        inner = data.get(key)
        if isinstance(inner, dict):
            return _attributes(inner)
    return _attributes(data)


def _pick(sources, keys):
    for source in sources:
        for key in keys:
            value = source.get(key)
            if value:
                return value
    return None


def _first_date(sources, keys):
    for source in sources:
        for key in keys:
            date = _iso_date(source.get(key))
            if date:
                return date
    return None


def _author(sources, fallback):
    for source in sources:
        for key in AUTHOR_KEYS:
            names = _split_names(source.get(key))
            if names:
                return " and ".join(dict.fromkeys(names))
    names = _split_names(fallback)
    return " and ".join(dict.fromkeys(names)) or None


def _body_html(value):
    if isinstance(value, dict):
        value = value.get("html") or value.get("text") or value.get("value")
    if isinstance(value, list):
        parts = []
        for item in value:
            part = _body_html(item)
            if part:
                parts.append(part if HTML_TEXT.search(part) else f"<p>{escape(part)}</p>")
        return "".join(parts)
    return value if isinstance(value, str) else ""


def _plain(value):
    if not value:
        return ""
    text = str(value)
    if HTML_TEXT.search(text):
        text = BeautifulSoup(text, "html.parser").get_text(" ")
    return _clean_ws(text)


def _json_or_none(text):
    try:
        return json.loads(text)
    except (TypeError, ValueError):
        return None


def _meta(soup, *names):
    for name in names:
        tag = soup.find("meta", attrs={"property": name}) or soup.find("meta", attrs={"name": name})
        if tag and tag.get("content"):
            return _clean_ws(tag["content"])
    return None


def _iso_date(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        if isinstance(value, (int, float)) or (isinstance(value, str) and EPOCH_TEXT.fullmatch(value.strip())):
            number = float(value)
            # The API may send epoch milliseconds; a value this large cannot be seconds.
            if abs(number) > 1e11:
                number /= 1000
            # An epoch instant has no written calendar date, so take it in UTC.
            return datetime.fromtimestamp(number, tz=timezone.utc).date().isoformat()
        text = str(value).strip()
        if not text:
            return None
        try:
            parsed = date_parser.isoparse(text)
        except ValueError:
            parsed = date_parser.parse(text)
        # Keep the calendar date as the bank wrote it; do not convert time zones.
        return parsed.date().isoformat()
    except (ValueError, OverflowError, OSError):
        return None


def _split_names(value):
    if isinstance(value, dict):
        value = value.get("display_name") or value.get("name")
    if isinstance(value, list):
        names = []
        for item in value:
            names.extend(_split_names(item))
        return names
    if not isinstance(value, str):
        return []
    # Drop parenthesised job titles and a leading "By".
    text = re.sub(r"\([^)]*\)", " ", _clean_ws(value))
    text = re.sub(r"^by\s+", "", text, flags=re.I)
    names = []
    for part in NAME_SEPARATORS.split(text):
        part = part.strip(" ;:")
        # Organisational credits such as "Press Office" are not people.
        if ORG_WORDS.search(part):
            continue
        # Cut a job title that follows the name without a separator, e.g. "Jane Doe Head of Lending".
        job = JOB_WORDS.search(part)
        if job:
            part = part[:job.start()].strip(" -,")
        if part:
            names.append(part)
    return names


def _is_byline(text, author):
    # The credit line ("By Jane Doe, Head of Lending") is not body text.
    if not author or len(text) > 200 or not re.match(r"by\s", text, re.I):
        return False
    lowered = text.lower()
    return all(name.lower() in lowered for name in author.split(" and "))


def _body_text(html, title, author):
    if not html:
        return ""

    if HTML_TEXT.search(html):
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup.find_all(DROP_TAGS):
            tag.extract()
        for tag in soup.find_all(True):
            if _is_boilerplate(tag):
                tag.extract()
        for br in soup.find_all("br"):
            br.replace_with(" ")
        blocks = _collect(soup)
    else:
        blocks = [("p", _clean_ws(part)) for part in re.split(r"\n\s*\n", html)]
        blocks = [(name, text) for name, text in blocks if text]

    paragraphs = []
    last = len(blocks) - 1
    for index, (name, text) in enumerate(blocks):
        if name in HEADINGS and ABOUT_HEADING.match(text):
            break
        if not paragraphs and _norm(text) == _norm(title):
            continue
        if not paragraphs and _is_byline(text, author):
            continue
        if BOILERPLATE_TEXT.match(text):
            continue
        if index == last and FINAL_BOILERPLATE.match(text):
            continue
        paragraphs.append(text)
    return "\n\n".join(paragraphs)


def _is_boilerplate(tag):
    hooks = [c.lower() for c in (tag.get("class") or [])]
    if tag.get("id"):
        hooks.append(str(tag["id"]).lower())
    return any(hook in part for part in hooks for hook in BOILERPLATE_HOOKS)


def _collect(node):
    out, buf = [], []
    _walk(node, out, buf)
    _flush(out, buf, "text")
    return out


def _walk(node, out, buf):
    for child in node.children:
        if isinstance(child, (Comment, Doctype)):
            continue
        if isinstance(child, NavigableString):
            buf.append(str(child))
        elif isinstance(child, Tag):
            if child.find(BLOCK_TAGS):
                _flush(out, buf, "text")
                _walk(child, out, buf)
                _flush(out, buf, "text")
            elif child.name in BLOCK_TAGS:
                _flush(out, buf, "text")
                buf.append(child.get_text())
                _flush(out, buf, child.name)
            else:
                buf.append(child.get_text())


def _flush(out, buf, name):
    text = _clean_ws("".join(buf))
    del buf[:]
    if text:
        out.append((name, text))


def _section_url(url):
    parts = urlsplit(url)
    path = parts.path if parts.path.endswith("/") else parts.path + "/"
    return urlunsplit((parts.scheme, parts.netloc, path, "", ""))


def _clean_url(url):
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def _clean_ws(value):
    if value is None:
        return ""
    return " ".join(str(value).split())


def _norm(value):
    return _clean_ws(value).lower()
