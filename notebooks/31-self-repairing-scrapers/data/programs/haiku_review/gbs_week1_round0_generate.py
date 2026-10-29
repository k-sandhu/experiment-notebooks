import json
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from dateutil import parser as dateparser
from dateutil.parser import isoparse

# Block-level elements that make up a release body, in document order.
BLOCK_TAGS = ["h2", "h3", "h4", "p", "li", "blockquote"]
HEADING_TAGS = ("h2", "h3", "h4")

# Heading that opens the standard boilerplate ("About us") at the end of a release.
ABOUT_RE = re.compile(r"^(about (us|greenbasket)|notes to editors?)\b", re.IGNORECASE)
VISIBLE_DATE_RE = re.compile(r"\d{1,2}\s+[A-Za-z]+\s+\d{4}")
ISO_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


def _clean(text):
    return " ".join((text or "").split())


def _strip_by(text):
    return re.sub(r"^\s*by\s+", "", text, flags=re.IGNORECASE)


def _next_data(soup):
    # Embedded Next.js data; used as a fallback and for structured fields
    tag = soup.find("script", id="__NEXT_DATA__")
    if tag is None:
        return {}
    try:
        data = json.loads(tag.get_text())
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def _page_props(data):
    return (data.get("props") or {}).get("pageProps") or {}


def _next_page(soup, page_url):
    # Follow rel="next" or a "Next" link when the listing is paginated
    link = soup.select_one('a[rel~="next"][href], link[rel~="next"][href]')
    if link is None:
        for candidate in soup.select("a[href]"):
            label = _clean(candidate.get_text()).lower()
            aria = (candidate.get("aria-label") or "").lower()
            if label in ("next", "next page", "›", "»") or "next page" in aria:
                link = candidate
                break
    return urljoin(page_url, link["href"]) if link is not None else None


def _listing_urls(soup, page_url, listing_url):
    urls = []
    for news_list in soup.select('[class*="NewsList_list"]'):
        for item in news_list.find_all("li"):
            link = item.find("a", href=True)
            if link is not None:
                urls.append(urljoin(page_url, link["href"]))
    if not urls:
        # Fall back to the embedded data, which lists the same releases
        for article in _page_props(_next_data(soup)).get("articles") or []:
            slug = article.get("slug")
            if slug:
                urls.append(listing_url.rstrip("/") + "/" + slug)
    return urls


def _collect_release_urls(fetch, listing_url):
    urls = []
    visited = set()
    page_url = listing_url
    while page_url and page_url not in visited:
        visited.add(page_url)
        soup = BeautifulSoup(fetch(page_url), "html.parser")
        urls.extend(_listing_urls(soup, page_url, listing_url))
        page_url = _next_page(soup, page_url)
    return list(dict.fromkeys(urls))  # de-duplicate, keep listing order


def _to_iso_date(value):
    if not value or not isinstance(value, str):
        return None
    try:
        if ISO_DATE_RE.match(value):
            parsed = isoparse(value)
        else:
            parsed = dateparser.parse(value, dayfirst=True)
    except (ValueError, OverflowError):
        return None
    return parsed.date().isoformat()


def _release_date(soup, article, article_json):
    # First-publication date only; never "updated", "reviewed" or event dates
    candidates = [article_json.get("publishedAt")]
    meta = soup.find("meta", attrs={"property": "article:published_time"})
    if meta is not None:
        candidates.append(meta.get("content"))
    for span in article.select('[class*="ArticleMeta_meta"] span'):
        text = _clean(span.get_text())
        if VISIBLE_DATE_RE.search(text) and not re.search(r"updat|review", text, re.IGNORECASE):
            candidates.append(text)
    for value in candidates:
        iso = _to_iso_date(value)
        if iso:
            return iso
    return None


def _release_title(soup, article, article_json):
    h1 = article.find("h1")
    if h1 is not None and _clean(h1.get_text()):
        return _clean(h1.get_text())
    if article_json.get("title"):
        return _clean(article_json["title"])
    if soup.title is not None:
        return _clean(soup.title.get_text().split(" | ")[0])
    return None


def _release_author(article, article_json):
    author = article_json.get("author")
    if isinstance(author, dict):
        raw = [author.get("name")]
    elif isinstance(author, list):
        raw = [a.get("name") if isinstance(a, dict) else a for a in author]
    elif isinstance(author, str):
        raw = [author]
    else:
        raw = []
    names = [_clean(_strip_by(n)) for n in raw if isinstance(n, str)]
    names = [n for n in names if n]

    if not names:
        # Visible byline: "Name, Job title" -> keep the name part only
        el = article.select_one('[class*="ArticleMeta_author"]')
        if el is not None:
            text = _clean(_strip_by(_clean(el.get_text())))
            name = _clean(text.split(",")[0])
            if name:
                names = [name]

    return " and ".join(names) if names else None


def _release_body(article, article_json):
    container = article.select_one('[class*="RichText_root"]')
    if container is not None:
        paragraphs = []
        for el in container.find_all(BLOCK_TAGS):
            if el.find_parent(BLOCK_TAGS) is not None:
                continue  # text already included via its block ancestor
            text = _clean(el.get_text())
            if not text:
                continue
            if el.name in HEADING_TAGS and ABOUT_RE.match(text):
                break  # standard boilerplate starts here
            paragraphs.append(text)
        if paragraphs:
            return "\n\n".join(paragraphs)

    # Fallback: structured body blocks in the embedded data
    paragraphs = []
    for block in article_json.get("body") or []:
        if not isinstance(block, dict) or block.get("_type") != "block":
            continue
        text = _clean("".join(
            c.get("text", "") for c in block.get("children") or [] if isinstance(c, dict)
        ))
        if not text:
            continue
        if block.get("style") in HEADING_TAGS and ABOUT_RE.match(text):
            break
        paragraphs.append(text)
    return "\n\n".join(paragraphs)


def _parse_release(html, url):
    soup = BeautifulSoup(html, "html.parser")
    article_json = _page_props(_next_data(soup)).get("article") or {}
    article = soup.select_one('[class*="Article_root"]') or soup
    return {
        "url": url,
        "title": _release_title(soup, article, article_json),
        "date": _release_date(soup, article, article_json),
        "author": _release_author(article, article_json),
        "body": _release_body(article, article_json),
    }


def extract(fetch, listing_url):
    records = []
    for url in _collect_release_urls(fetch, listing_url):
        records.append(_parse_release(fetch(url), url))
    # Newest first; ties keep listing order because the sort is stable
    records.sort(key=lambda r: r["date"] or "", reverse=True)
    return records
