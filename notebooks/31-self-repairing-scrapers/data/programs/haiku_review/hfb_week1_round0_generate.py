import json
import re
from datetime import datetime, timezone
from urllib.parse import parse_qsl, quote, urlencode, urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup
from bs4.element import Comment, Doctype, NavigableString, Tag
from dateutil import parser as date_parser


API_PAGE_SIZE = 100
MAX_PAGES = 200

API_CALL = re.compile(r"fetch\(\s*['\"`]([^'\"`]*/api/[^'\"`]*)['\"`]")
HEADINGS = ["h1", "h2", "h3", "h4", "h5", "h6"]
BLOCK_TAGS = HEADINGS + ["p", "li", "blockquote", "pre", "td", "th", "figcaption", "dt", "dd", "div"]
DROP_TAGS = ["script", "style", "noscript", "template", "nav", "aside", "header", "footer",
             "form", "button", "input", "select", "textarea", "iframe", "svg"]
BOILERPLATE_HOOKS = ("share", "related", "tags", "newsletter", "cookie", "consent", "contact",
                     "boilerplate", "about-us", "breadcrumb", "social", "byline", "meta")

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
NAME_SEPARATORS = re.compile(r"\s*[,|·•–—]\s*|\s+-\s+")


def extract(fetch, listing_url):
    article_urls = []
    seen = set()
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
            if url not in seen:
                seen.add(url)
                article_urls.append(url)
        page_url = _html_next(soup, page_url)

    # The listing is filled in by JavaScript from a JSON API; page through that API.
    api_url = _find_api_url(first_soup, listing_url)
    api_base = None
    if api_url:
        api_base = api_url.partition("?")[0].rstrip("/")
        for item in _walk_api(fetch, api_url):
            url = _item_url(item, listing_url)
            if url and url not in seen:
                seen.add(url)
                article_urls.append(url)

    records = []
    for url in article_urls:
        try:
            records.append(_parse_release(fetch, url, api_base))
        except FetchError as exc:
            # A withdrawn release is skipped; other HTTP errors are real failures.
            if getattr(exc, "status", None) in (404, 410):
                continue
            raise

    records.sort(key=lambda r: r["date"] or "", reverse=True)
    return records


def _parse_release(fetch, article_url, api_base):
    soup = BeautifulSoup(fetch(article_url), "html.parser")

    # The release page is a shell; its content comes from the JSON API using data-id.
    detail = {}
    holder = soup.find(attrs={"data-id": True})
    if holder is not None and api_base:
        rid = quote(str(holder["data-id"]), safe="")
        detail = _unwrap(_json_or_none(fetch(f"{api_base}/{rid}")))

    h1 = soup.find("h1")
    title = _clean_ws(detail.get("title") or (h1.get_text() if h1 else ""))

    # First publication date only; never "updated" or event dates.
    date = _iso_date(detail.get("published_at")) or _iso_date(
        _meta(soup, "article:published_time", "date")
    )

    names = _split_names(detail.get("author") or detail.get("authors"))
    if not detail and not names:
        names = _split_names(_meta(soup, "author"))
    author = " and ".join(dict.fromkeys(names)) or None

    body_html = detail.get("body_html") or detail.get("body")
    if not body_html and not detail:
        node = soup.select_one(".body")
        if node and _clean_ws(node.get_text()) not in ("", "Loading…", "Loading..."):
            body_html = str(node)
    body = _body_text(body_html, title)

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
    params["limit"] = str(API_PAGE_SIZE)
    seen = set()
    next_url = None
    for page in range(1, MAX_PAGES + 1):
        if next_url is None:
            if page > 1:
                params["page"] = str(page)
                params["offset"] = str(len(seen))
            url = f"{base}?{urlencode(params)}"
        else:
            url = next_url

        data = _json_or_none(fetch(url))
        items = data.get("items") if isinstance(data, dict) else data
        if not isinstance(items, list):
            return

        fresh = 0
        for item in items:
            if not isinstance(item, dict):
                continue
            key = item.get("slug") or item.get("id") or item.get("url")
            if key is None or key in seen:
                continue
            seen.add(key)
            fresh += 1
            yield item

        if not fresh or _no_more(data):
            return
        next_url = _api_next(data, url)


def _no_more(data):
    return isinstance(data, dict) and (data.get("has_more") is False or data.get("hasMore") is False)


def _api_next(data, url):
    if not isinstance(data, dict):
        return None
    links = data.get("links") if isinstance(data.get("links"), dict) else {}
    pagination = data.get("pagination") if isinstance(data.get("pagination"), dict) else {}
    for value in (data.get("next"), data.get("next_url"), links.get("next"), pagination.get("next")):
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


def _item_url(item, listing_url):
    if item.get("url"):
        return _clean_url(urljoin(listing_url, str(item["url"])))
    if item.get("slug"):
        return urljoin(_section_url(listing_url), "article/" + quote(str(item["slug"]), safe=""))
    return None


def _section_url(url):
    parts = urlsplit(url)
    path = parts.path if parts.path.endswith("/") else parts.path + "/"
    return urlunsplit((parts.scheme, parts.netloc, path, "", ""))


def _clean_url(url):
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def _unwrap(data):
    if not isinstance(data, dict):
        return {}
    for key in ("article", "item", "data", "news"):
        inner = data.get(key)
        if isinstance(inner, dict) and "title" in inner:
            return inner
    return data


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
    if value is None or value == "":
        return None
    try:
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, tz=timezone.utc).date().isoformat()
        text = str(value).strip()
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
    text = re.sub(r"^by\s+", "", _clean_ws(value), flags=re.I)
    names = []
    for part in NAME_SEPARATORS.split(text):
        part = part.strip(" ;:")
        # Drop job titles and organisational credits such as "Press Office".
        if not part or JOB_WORDS.search(part) or ORG_WORDS.search(part):
            continue
        names.append(part)
    return names


def _body_text(html, title):
    if not html:
        return ""

    if re.search(r"<[a-zA-Z]", html):
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
        if BOILERPLATE_TEXT.match(text):
            continue
        if index == last and FINAL_BOILERPLATE.match(text):
            continue
        if not paragraphs and _norm(text) == _norm(title):
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


def _clean_ws(value):
    if value is None:
        return ""
    return " ".join(str(value).split())


def _norm(value):
    return _clean_ws(value).lower()
