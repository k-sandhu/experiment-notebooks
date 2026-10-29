import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from dateutil import parser as date_parser


def _soup(html):
    return BeautifulSoup(html, "html.parser")


def _clean(text):
    return " ".join(text.split())


def _listing_urls(soup, base_url):
    urls = []
    for row in soup.select("ul.news-rows li.news-row"):
        link = row.find("a", href=True)
        if link:
            urls.append(urljoin(base_url, link["href"]))
    return urls


def _next_page(soup, base_url):
    link = soup.find("a", rel=lambda r: r and "next" in r, href=True)
    if link is None:
        link = soup.find("a", string=re.compile(r"^\s*(next|older)\b", re.I), href=True)
    if link is None:
        link = soup.find("a", attrs={"aria-label": re.compile(r"^next", re.I)}, href=True)
    return urljoin(base_url, link["href"]) if link else None


def _publish_date(header, soup):
    time_tag = header.find("time", attrs={"datetime": True}) or soup.find(
        "time", attrs={"datetime": True}
    )
    if time_tag is None:
        return None
    raw = time_tag["datetime"].strip()
    match = re.match(r"(\d{4}-\d{2}-\d{2})", raw)
    if match:
        return match.group(1)
    try:
        return date_parser.parse(raw).strftime("%Y-%m-%d")
    except (ValueError, OverflowError):
        return None


def _authors(text):
    text = re.sub(r"^\s*by\s+", "", text, flags=re.I)
    names = []
    for part in re.split(r"\s+and\s+|\s*&\s*|\s*;\s*", text):
        name = part.split(",")[0].strip()
        if name:
            names.append(name)
    return " and ".join(names) or None


def _parse_release(html, url):
    soup = _soup(html)
    header = soup.select_one(".news-header") or soup.find("main") or soup

    h1 = header.find("h1") or soup.find("h1")
    if h1 is not None:
        title = _clean(h1.get_text())
    else:
        title = _clean(soup.title.get_text().split("|")[0]) if soup.title else ""

    byline = header.select_one(".news-byline")
    author = _authors(_clean(byline.get_text())) if byline is not None else None

    body_el = soup.select_one(".news-body")
    paragraphs = []
    if body_el is not None:
        paragraphs = [_clean(p.get_text()) for p in body_el.find_all("p")]
        if not any(paragraphs):
            paragraphs = [_clean(line) for line in body_el.get_text("\n").split("\n")]
    body = "\n\n".join(p for p in paragraphs if p)

    return {
        "url": url,
        "title": title,
        "date": _publish_date(header, soup),
        "author": author,
        "body": body,
    }


def extract(fetch, listing_url):
    release_urls = []
    seen_urls = set()
    visited_pages = set()
    page_url = listing_url

    while page_url and page_url not in visited_pages:
        visited_pages.add(page_url)
        soup = _soup(fetch(page_url))
        for url in _listing_urls(soup, page_url):
            if url not in seen_urls:
                seen_urls.add(url)
                release_urls.append(url)
        page_url = _next_page(soup, page_url)

    records = [_parse_release(fetch(url), url) for url in release_urls]
    records.sort(key=lambda r: r["date"] or "", reverse=True)
    return records
