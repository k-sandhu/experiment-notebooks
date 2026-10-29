import json
import re
import unicodedata
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

MONTHS = {
    "janvier": 1, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
    "juillet": 7, "aout": 8, "septembre": 9, "octobre": 10, "novembre": 11,
    "decembre": 12,
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11,
    "december": 12,
}

NOISE_RE = re.compile(
    r"partage|share|social|related|connexe|similaire|tags?\b|etiquette|motcle|"
    r"newsletter|infolettre|abonn|contact|apropos|about|breadcrumb|fil-ariane|"
    r"cookie|consent|sidebar|menu|\bnav|comment|print|imprim|pagination|"
    r"auteur|author|byline|\bdate\b|meta",
    re.I,
)
STOP_HEADING_RE = re.compile(
    r"^\s*(à propos|a propos|about|renseignements|pour information|pour plus|"
    r"contact|personne-ressource|liens? connexes?|dans la même|articles? (similaires|connexes)|"
    r"mots-clés|étiquettes|tags)",
    re.I,
)


def _norm(s):
    s = (s or "").replace("\xa0", " ").replace("\u202f", " ")
    return re.sub(r"\s+", " ", s).strip()


def _text(el):
    """Text of an element keeping the page's own spacing (inline tags add nothing)."""
    for br in el.find_all("br"):
        br.replace_with(" ")
    return _norm(el.get_text())


def _ascii(s):
    return "".join(
        c for c in unicodedata.normalize("NFD", s.lower()) if not unicodedata.combining(c)
    )


def _parse_date(text):
    if not text:
        return None
    text = _norm(text)
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
    if m:
        return "%s-%s-%s" % m.groups()
    t = _ascii(text)
    m = re.search(r"(\d{1,2})\s*(?:er|e)?\s+([a-z]+)\.?,?\s+(\d{4})", t)
    if m and m.group(2) in MONTHS:
        return "%04d-%02d-%02d" % (int(m.group(3)), MONTHS[m.group(2)], int(m.group(1)))
    m = re.search(r"([a-z]+)\.?\s+(\d{1,2}),?\s+(\d{4})", t)
    if m and m.group(1) in MONTHS:
        return "%04d-%02d-%02d" % (int(m.group(3)), MONTHS[m.group(1)], int(m.group(2)))
    m = re.search(r"(\d{1,2})[/.](\d{1,2})[/.](\d{4})", t)
    if m:
        return "%04d-%02d-%02d" % (int(m.group(3)), int(m.group(2)), int(m.group(1)))
    return None


def _jsonld_items(soup):
    for sc in soup.find_all("script", type=re.compile("ld\\+json", re.I)):
        try:
            data = json.loads(sc.string or sc.get_text())
        except Exception:
            continue
        stack = [data]
        while stack:
            d = stack.pop()
            if isinstance(d, list):
                stack.extend(d)
            elif isinstance(d, dict):
                yield d
                if "@graph" in d:
                    stack.append(d["@graph"])


def _find_date(soup):
    for d in _jsonld_items(soup):
        v = d.get("datePublished")
        if isinstance(v, str) and _parse_date(v):
            return _parse_date(v)
    for prop in ("article:published_time", "og:published_time", "datePublished"):
        tag = soup.find("meta", attrs={"property": prop}) or soup.find(
            "meta", attrs={"name": prop}
        ) or soup.find("meta", attrs={"itemprop": prop})
        if tag and _parse_date(tag.get("content")):
            return _parse_date(tag.get("content"))
    tag = soup.find(attrs={"itemprop": "datePublished"})
    if tag:
        d = _parse_date(tag.get("content") or tag.get("datetime") or tag.get_text())
        if d:
            return d
    main = soup.find("main") or soup
    for el in main.find_all(["p", "div", "span", "time", "li"]):
        txt = _norm(el.get_text(" "))
        if len(txt) > 80:
            continue
        low = _ascii(txt)
        if re.search(r"publi[e]?\s*(le|:)|^publie|^date", low) and not re.search(
            r"mis a jour|modifie|revise|updated", low
        ):
            d = _parse_date(txt)
            if d:
                return d
    for el in main.find_all("time"):
        p = el.find_parent(["p", "div", "span"])
        ctx = _ascii(p.get_text(" ")) if p else ""
        if re.search(r"mis a jour|modifie|updated", ctx):
            continue
        d = _parse_date(el.get("datetime") or el.get_text())
        if d:
            return d
    return None


def _clean_names(raw):
    raw = _norm(raw)
    raw = re.sub(r"^(par|by|auteurs?|author|rédigé par|redige par)\s*:?\s+", "", raw, flags=re.I)
    parts = re.split(r"\s*(?:;|&|,|\bet\b|\band\b)\s*", raw)
    particles = {"de", "du", "des", "la", "le", "van", "von", "d'", "di", "da", "del"}
    names = []
    for p in parts:
        p = p.strip(" .")
        if not p:
            continue
        words = p.split()
        if all(w[0].isupper() or w.lower() in particles or w[0] in "'-" for w in words):
            names.append(p)
    return " and ".join(names) if names else None


def _find_author(soup):
    for d in _jsonld_items(soup):
        a = d.get("author")
        if a:
            items = a if isinstance(a, list) else [a]
            names = []
            for i in items:
                n = i.get("name") if isinstance(i, dict) else i
                if isinstance(n, str) and n.strip():
                    names.append(_norm(n))
            if names:
                return " and ".join(names)
    main = soup.find("main") or soup
    el = main.find(class_=re.compile(r"auteur|author|byline", re.I)) or main.find(
        attrs={"itemprop": "author"}
    ) or main.find(attrs={"rel": "author"})
    if el:
        names = [
            _norm(x.get_text())
            for x in el.find_all(attrs={"itemprop": "name"})
            if _norm(x.get_text())
        ]
        if names:
            return " and ".join(names)
        r = _clean_names(el.get_text(" "))
        if r:
            return r
    tag = soup.find("meta", attrs={"name": "author"})
    if tag and tag.get("content"):
        return _clean_names(tag["content"])
    for p in main.find_all("p"):
        t = _norm(p.get_text(" "))
        if len(t) < 80 and re.match(r"^(par|by)\s+\S", t, re.I):
            return _clean_names(t)
    return None


def _find_title(soup):
    main = soup.find("main") or soup
    h1 = main.find("h1") or soup.find("h1")
    if h1 and _text(h1):
        return _text(h1)
    tag = soup.find("meta", attrs={"property": "og:title"})
    if tag and tag.get("content"):
        return _norm(tag["content"])
    if soup.title:
        return _norm(soup.title.get_text()).split(" | ")[0]
    return ""


def _is_noise(el):
    cls = " ".join(el.get("class") or []) + " " + (el.get("id") or "")
    cls = _ascii(cls)
    return bool(cls.strip()) and bool(NOISE_RE.search(cls))


def _find_body(soup):
    main = soup.find("main") or soup
    container = None
    for sel in (
        ".contenu", ".content", ".entry-content", ".post-content", ".article-body",
        ".article-content", ".texte", "[itemprop=articleBody]", "article",
    ):
        c = main.select_one(sel)
        if c and c.find("p"):
            container = c
            break
    if container is None:
        container = main
    for t in container.find_all(["script", "style", "nav", "aside", "form", "noscript",
                                 "header", "footer", "button", "iframe"]):
        t.decompose()
    for t in list(container.find_all(True)):
        if getattr(t, "decomposed", False):
            continue
        if t is not container and _is_noise(t):
            # keep wrappers that are clearly content containers
            if re.search(r"contenu|content|texte|body", _ascii(" ".join(t.get("class") or []))):
                continue
            t.decompose()
    h1 = container.find("h1")
    if h1:
        h1.decompose()
    blocks = []
    for el in container.find_all(["p", "li", "h2", "h3", "h4", "h5", "blockquote"]):
        if el.name in ("p", "li", "blockquote") and el.find_parent(["li", "blockquote"]) not in (None, el):
            continue
        if el.name == "blockquote" and el.find("p"):
            continue
        if el.name == "li" and el.find("p"):
            continue
        txt = _text(el)
        if not txt:
            continue
        if el.name.startswith("h") and STOP_HEADING_RE.match(txt):
            break
        blocks.append(txt)
    return "\n\n".join(blocks)


def _same_listing_page(href, listing_url):
    a, b = urlparse(href), urlparse(listing_url)
    return a.netloc == b.netloc and a.path.rstrip("/").startswith(b.path.rstrip("/"))


def _release_links(soup, page_url, listing_url):
    main = soup.find("main") or soup
    links = []
    anchors = []
    for art in main.find_all("article"):
        a = art.find("a", href=True)
        if a:
            anchors.append(a)
    if not anchors:
        for h in main.find_all(["h2", "h3", "h4"]):
            a = h.find("a", href=True)
            if a:
                anchors.append(a)
    if not anchors:
        base = urlparse(listing_url).path.rstrip("/")
        for a in main.find_all("a", href=True):
            path = urlparse(urljoin(page_url, a["href"])).path.rstrip("/")
            if path != base and path.startswith(base + "/") and not re.search(
                r"/page/\d+$", path
            ):
                anchors.append(a)
    for a in anchors:
        href = a["href"].strip()
        if href.startswith(("#", "mailto:", "javascript:")):
            continue
        links.append((urljoin(page_url, href), a))
    return links


def _next_pages(soup, page_url, listing_url):
    out = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith(("#", "mailto:", "javascript:")):
            continue
        full = urljoin(page_url, href)
        rel = a.get("rel") or []
        txt = _ascii(_norm(a.get_text(" ")))
        is_next = "next" in rel or re.match(
            r"^(suivant|suivante|next|page suivante|plus de nouvelles|voir plus|charger plus|>|>>|›|»)", txt
        )
        is_page = re.search(r"[?&](page|p|pg|paged)=\d+", full) or re.search(
            r"/page/\d+/?$", urlparse(full).path
        )
        if (is_next or is_page) and _same_listing_page(full, listing_url):
            out.append(full)
    return out


def extract(fetch, listing_url):
    seen_pages = set()
    queue = [listing_url]
    entries = []
    seen_urls = set()
    while queue:
        page = queue.pop(0)
        key = page.split("#")[0]
        if key in seen_pages:
            continue
        seen_pages.add(key)
        if len(seen_pages) > 200:
            break
        try:
            html = fetch(page)
        except FetchError:
            if page == listing_url:
                raise
            continue
        soup = BeautifulSoup(html, "html.parser")
        for url, a in _release_links(soup, page, listing_url):
            url = url.split("#")[0]
            if url in seen_urls:
                continue
            seen_urls.add(url)
            art = a.find_parent("article")
            ldate = _parse_date(art.get_text(" ")) if art else None
            entries.append((url, ldate))
        for n in _next_pages(soup, page, listing_url):
            if n.split("#")[0] not in seen_pages:
                queue.append(n)

    records = []
    for url, ldate in entries:
        try:
            html = fetch(url)
        except FetchError:
            continue
        soup = BeautifulSoup(html, "html.parser")
        date = _find_date(soup) or ldate
        records.append(
            {
                "url": url,
                "title": _find_title(soup),
                "date": date,
                "author": _find_author(soup),
                "body": _find_body(soup),
            }
        )
    records.sort(key=lambda r: r["date"] or "", reverse=True)
    return records
