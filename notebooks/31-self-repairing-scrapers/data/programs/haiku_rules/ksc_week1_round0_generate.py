import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from dateutil import parser as dateparser

_MAX_LISTING_PAGES = 500


def _text(node):
    if node is None:
        return ""
    return " ".join(node.get_text(" ", strip=True).split())


def _soup(html):
    return BeautifulSoup(html, "html.parser")


def _iso_date(text):
    if not text:
        return None
    try:
        return dateparser.parse(text, dayfirst=True).date().isoformat()
    except (ValueError, OverflowError, TypeError):
        return None


def _authors(text):
    if not text:
        return None
    # Drop parenthesised job titles/affiliations and a leading "By"
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"^\s*by\s+", "", text, flags=re.IGNORECASE)
    parts = re.split(r"\s*(?:,|;|&|\band\b)\s*", text)
    names = [" ".join(p.split()) for p in parts if p and p.strip()]
    return " and ".join(names) if names else None


def _is_release(url, listing_url):
    lp = urlparse(listing_url)
    p = urlparse(url)
    if p.netloc != lp.netloc:
        return False
    base = lp.path.rstrip("/")
    path = p.path.rstrip("/")
    if not path.startswith(base + "/"):
        return False
    rest = path[len(base) + 1:]
    return bool(rest) and "/" not in rest


def _next_page(soup, current_url):
    link = soup.select_one("a[rel~='next'][href]")
    if link is None:
        for a in soup.find_all("a", href=True):
            label = _text(a).lower()
            aria = (a.get("aria-label") or "").lower()
            if label in ("next", "next page", "›", "»") or "next" in aria:
                link = a
                break
    if link is None:
        return None
    return urljoin(current_url, link["href"])


def _listing_pages(fetch, listing_url):
    url = listing_url
    seen = set()
    while url and url not in seen and len(seen) < _MAX_LISTING_PAGES:
        seen.add(url)
        soup = _soup(fetch(url))
        yield soup
        url = _next_page(soup, url)


def _release(fetch, url, teaser_date):
    soup = _soup(fetch(url))
    main = soup.find("main") or soup

    h1 = main.find("h1")
    title = _text(h1)
    if not title and soup.title and soup.title.string:
        title = soup.title.string.split(" | ")[0].strip()

    meta = {}
    dl = main.find("dl", class_="meta") or main.find("dl")
    if dl is not None:
        for dt in dl.find_all("dt"):
            dd = dt.find_next_sibling("dd")
            if dd is not None:
                meta[_text(dt).lower()] = dd

    date = _iso_date(_text(meta.get("published")))
    if date is None:
        time_tag = main.find("time")
        if time_tag is not None:
            date = _iso_date(time_tag.get("datetime") or _text(time_tag))
    if date is None:
        date = teaser_date

    author_node = meta.get("author") or meta.get("authors") or meta.get("written by")
    author = _authors(_text(author_node)) if author_node is not None else None

    body_root = main.select_one(".body") or main
    blocks = []
    for el in body_root.find_all(["p", "h2", "h3", "h4", "li", "blockquote"]):
        if el.find_parent(["p", "li", "blockquote"]) is not None and el.name == "p":
            continue
        if "contact" in (el.get("class") or []):
            continue
        t = _text(el)
        if t:
            blocks.append(t)
    body = "\n\n".join(blocks)

    return {
        "url": url,
        "title": title,
        "date": date,
        "author": author,
        "body": body,
    }


def extract(fetch, listing_url):
    links = []
    seen = set()
    teaser_dates = {}

    for soup in _listing_pages(fetch, listing_url):
        for a in soup.select("article h2 a[href]"):
            url = urljoin(listing_url, a["href"]).split("#")[0]
            if url in seen or not _is_release(url, listing_url):
                continue
            seen.add(url)
            links.append(url)
            article = a.find_parent("article")
            meta = article.find(class_="teaser__meta") if article else None
            meta_text = _text(meta)
            if "·" in meta_text:
                meta_text = meta_text.split("·")[-1]
            teaser_dates[url] = _iso_date(meta_text.strip())

    records = [_release(fetch, url, teaser_dates.get(url)) for url in links]
    records.sort(key=lambda r: r["date"] or "", reverse=True)
    return records
