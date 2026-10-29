import re
from urllib.parse import urljoin
from datetime import datetime
from dateutil import parser as date_parser
from bs4 import BeautifulSoup

# FetchError is assumed to be defined elsewhere

def extract(fetch, listing_url):
    """
    Extract all news releases from the listing page.

    Parameters
    ----------
    fetch : callable
        fetch(url) -> str (HTML). Raises FetchError on HTTP errors.
    listing_url : str
        Absolute URL of the listing page (e.g., "https://www.devvalbrume.example/nouvelles/").

    Returns
    -------
    list[dict]
        Each dict has keys: url, title, date, author, body.
        Newest first.
    """
    listing_html = fetch(listing_url)
    soup_listing = BeautifulSoup(listing_html, "html.parser")

    article_items = soup_listing.find_all("article", class_="nouvelle")
    records = []

    for item in article_items:
        h2 = item.find("h2")
        if not h2:
            continue
        link_tag = h2.find("a", href=True)
        if not link_tag:
            continue
        rel_url = link_tag["href"]
        abs_url = urljoin(listing_url, rel_url)

        try:
            release_html = fetch(abs_url)
        except Exception:
            # Skip if fetch fails
            continue
        soup_release = BeautifulSoup(release_html, "html.parser")

        h1 = soup_release.find("h1")
        if h1:
            title = h1.get_text(strip=True)
        else:
            title = ""

        date_tag = soup_release.find("p", class_="date")
        if not date_tag:
            continue
        date_text = date_tag.get_text(strip=True)
        match = re.search(r"Publié\s+le\s+(\d+(?:er)?)\s+(\w+)\s+(\d{4})", date_text, flags=re.IGNORECASE)
        if not match:
            continue
        day_str = match.group(1)
        month_str = match.group(2).lower()
        year_str = match.group(3)
        day_num = int(re.sub(r"e?r$", "", day_str))
        month_map = {
            "janvier": 1, "février": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
            "juillet": 7, "août": 8, "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12
        }
        month_num = month_map.get(month_str)
        if month_num is None:
            continue
        try:
            day_clean = str(day_num)
            date_str = f"{day_clean} {month_str} {year_str}"
            dt = date_parser.parse(date_str, fuzzy=True)
            date_iso = dt.date().isoformat()
        except Exception:
            continue

        author_tag = soup_release.find("p", class_="auteur")
        if author_tag:
            author_text = author_tag.get_text(strip=True)
            if author_text.lower().startswith("par "):
                author_text = author_text[4:].strip()
            author_text = author_text.rstrip(".")
            author_text = " ".join(author_text.split())
            author = author_text if author_text else None
        else:
            author = None

        contenu_div = soup_release.find("div", class_="contenu")
        if contenu_div:
            paras = []
            for p in contenu_div.find_all("p"):
                paras.append(p.get_text(strip=False).replace("\n", " ").strip())
            body = "\n\n".join(paras)
        else:
            body = ""

        record = {
            "url": abs_url,
            "title": title,
            "date": date_iso,
            "author": author if author else None,
            "body": body
        }
        records.append(record)

    records.sort(key=lambda r: r["date"], reverse=True)
    return records
