import re
import unicodedata
from datetime import date
from urllib.parse import urljoin, urldefrag

from bs4 import BeautifulSoup

MONTHS = {
    "janvier": 1, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
    "juillet": 7, "aout": 8, "septembre": 9, "octobre": 10, "novembre": 11,
    "decembre": 12,
}

DATE_RE = re.compile(r"(\d{1,2})(?:er)?\s+([a-z]+)\s+(\d{4})")
SPLIT_AUTHORS_RE = re.compile(r"\s*(?:,|;|\s[-–—|/&]\s|\s+et\s+|\s+and\s+)\s*", re.I)
PREFIX_RE = re.compile(r"^(par|by)\s+", re.I)
TITLE_WORD_RE = re.compile(
    r"(directeur|directrice|conseill|responsable|charg|gestionnaire|agent|analyste"
    r"|coordonn|president|adjoint|technicien|redact|porte-parole|specialiste|chef"
    r"|editeur|editrice)"
)
BOILERPLATE_CLASSES = {"auteur", "date", "partage", "share", "tags", "related", "contact"}
BOILERPLATE_TAGS = {"nav", "header", "footer", "form", "aside"}
MAX_PAGES = 200


def _clean(text):
    return " ".join(text.split())


def _fold(text):
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii").lower()


def _parse_date(text):
    for match in DATE_RE.finditer(_fold(text or "")):
        month = MONTHS.get(match.group(2))
        if not month:
            continue
        try:
            return date(int(match.group(3)), month, int(match.group(1))).isoformat()
        except ValueError:
            continue
    return None


def _in_boilerplate(tag):
    for node in [tag] + list(tag.parents):
        if node.name in BOILERPLATE_TAGS:
            return True
        classes = node.get("class") or []
        if any(c in BOILERPLATE_CLASSES for c in classes):
            return True
    return False


def _listing_items(soup, base):
    items = []
    for article in soup.select("article.nouvelle"):
        link = article.find("a", href=True)
        if link is None:
            continue
        date_el = article.find(class_="date")
        items.append((
            urldefrag(urljoin(base, link["href"]))[0],
            _clean(link.get_text(" ")),
            _parse_date(date_el.get_text(" ") if date_el else ""),
        ))
    if not items:
        main = soup.find("main") or soup
        for h2 in main.find_all("h2"):
            link = h2.find("a", href=True)
            if link is not None:
                items.append((
                    urldefrag(urljoin(base, link["href"]))[0],
                    _clean(link.get_text(" ")),
                    None,
                ))
    return items


def _next_page(soup, current):
    for link in soup.find_all(["link", "a"], href=True):
        rel = link.get("rel") or []
        if isinstance(rel, str):
            rel = rel.split()
        classes = " ".join(link.get("class") or []).lower()
        text = _fold(_clean(link.get_text(" ")))
        if ("next" in rel or "next" in classes or "suivant" in classes
                or text in {"suivant", "suivante", "page suivante", "next", "»", ">"}):
            return urljoin(current, link["href"])
    return None


def _title(soup, fallback):
    main = soup.find("main") or soup
    h1 = main.find("h1") or soup.find("h1")
    text = _clean(h1.get_text(" ")) if h1 else ""
    return text or fallback


def _first_published_date(soup):
    for el in soup.find_all(class_="date"):
        text = _fold(_clean(el.get_text(" ")))
        if "publi" in text and "mis a jour" not in text and "modifi" not in text:
            parsed = _parse_date(text)
            if parsed:
                return parsed
    return None


def _authors(soup):
    el = soup.find(class_="auteur")
    if el is None:
        return None
    text = PREFIX_RE.sub("", _clean(el.get_text(" ")))
    names = []
    for part in SPLIT_AUTHORS_RE.split(text):
        part = part.strip(" .;:")
        if not part or not part[0].isupper():
            continue
        if TITLE_WORD_RE.search(_fold(part)):
            continue
        names.append(part)
    return " and ".join(names) or None


def _body(soup):
    container = soup.find(class_="contenu") or soup.find("main") or soup
    paragraphs = []
    for block in container.find_all(["p", "h2", "h3", "h4", "li"]):
        if _in_boilerplate(block):
            continue
        text = _clean(block.get_text(" "))
        if text:
            paragraphs.append(text)
    return "\n\n".join(paragraphs)


def extract(fetch, listing_url):
    found = {}
    visited = set()
    page_url = listing_url

    while page_url and page_url not in visited and len(visited) < MAX_PAGES:
        visited.add(page_url)
        soup = BeautifulSoup(fetch(page_url), "html.parser")
        for url, title, published in _listing_items(soup, page_url):
            if url not in found:
                found[url] = (title, published)
        page_url = _next_page(soup, page_url)

    records = []
    for url, (listing_title, listing_date) in found.items():
        soup = BeautifulSoup(fetch(url), "html.parser")
        records.append({
            "url": url,
            "title": _title(soup, listing_title),
            "date": _first_published_date(soup) or listing_date,
            "author": _authors(soup),
            "body": _body(soup),
        })

    records.sort(key=lambda r: r["date"] or "", reverse=True)
    return records
