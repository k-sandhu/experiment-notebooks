import re
from urllib.parse import urljoin
from datetime import datetime
from dateutil import parser as date_parser
from bs4 import BeautifulSoup

# FetchError and other definitions assumed to exist; we only use fetch.

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
    # Fetch listing page
    listing_html = fetch(listing_url)
    soup_listing = BeautifulSoup(listing_html, "html.parser")

    # Find all article items with class "nouvelle"
    article_items = soup_listing.find_all("article", class_="nouvelle")
    records = []

    for item in article_items:
        # Extract relative link from <a> inside <h2>
        h2 = item.find("h2")
        if not h2:
            continue
        link_tag = h2.find("a", href=True)
        if not link_tag:
            continue
        rel_url = link_tag["href"]
        abs_url = urljoin(listing_url.rstrip("/") + "/", rel_url.lstrip("/"))
        # Fetch release page
        try:
            release_html = fetch(abs_url)
        except Exception as e:
            # If fetch fails, skip this release
            continue
        soup_release = BeautifulSoup(release_html, "html.parser")

        # Title: full headline as plain text, exactly as release page shows it
        # The release page has <h1> with the title
        h1 = soup_release.find("h1")
        if h1:
            title = h1.get_text(strip=True)
        else:
            # fallback: take text from <a> inside <h2> on listing? but spec says full headline as release page shows it
            # Use the <a> text from listing? safer: use <h1>
            title = ""

        # Date: parse "Publié le 17 septembre 2026" or "Publié le 1er septembre 2026"
        date_tag = soup_release.find("p", class_="date")
        if date_tag:
            date_text = date_tag.get_text(strip=True)
            # Expected format: "Publié le <day> <month> <year>" where day may be ordinal like "1er"
            # Remove "Publié le " prefix
            match = re.search(r"Publié\s+le\s+(\d+(?:er)?)\s+(\w+)\s+(\d{4})", date_text, flags=re.IGNORECASE)
            if match:
                day_str = match.group(1)  # may be "1", "1er", "17"
                month_str = match.group(2)  # e.g., "septembre"
                year_str = match.group(3)
                # Normalize day: remove trailing "er" if present
                day_num = int(re.sub(r"e?r$", "", day_str))  # works for "1", "1er" -> 1
                # Map month name to number
                month_map = {
                    "janvier": 1, "février": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
                    "juillet": 7, "août": 8, "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12
                }
                month_num = month_map.get(month_str.lower())
                if month_num is None:
                    # fallback: try partial match? but assume correct
                    continue
                try:
                    # dateutil can parse "17 septembre 2026" but not "1er septembre 2026"? It can.
                    # We'll construct a string "day month year" without ordinal
                    day_clean = str(day_num)
                    date_str = f"{day_clean} {month_str} {year_str}"
                    # Use dateutil to parse
                    dt = date_parser.parse(date_str, fuzzy=True)
                    # Ensure it's a date (no time)
                    date_iso = dt.date().isoformat()  # YYYY-MM-DD
                except Exception:
                    continue
            else:
                continue
        else:
            # No date tag, skip
            continue

        # Author: class "auteur" with text like "Par Bastien Corvelin"
        author_tag = soup_release.find("p", class_="auteur")
        if author_tag:
            author_text = author_tag.get_text(strip=True)
            # Remove "Par " prefix and any trailing punctuation
            if author_text.lower().startswith("par "):
                author_text = author_text[4:].strip()
            # Clean up possible trailing period or comma
            author_text = author_text.rstrip(".")
            # Remove any extra spaces
            author_text = " ".join(author_text.split())
            # If empty, set None
            if author_text:
                author = author_text
            else:
                author = None
        else:
            author = None

        # Body: full main text inside .contenu div, paragraphs separated by blank lines
        contenu_div = soup_release.find("div", class_="contenu")
        if contenu_div:
            # Get all <p> inside .contenu, get text, preserve paragraph breaks
            paras = []
            for p in contenu_div.find_all("p"):
                # Get text with newline separator? We need blank line between paragraphs.
                # Use .get_text(strip=False) to keep internal whitespace? But we want paragraphs separated by blank line.
                # Simple: get text, then split by <p> tags and join with "\n\n"
                paras.append(p.get_text(strip=False).replace("\n", " ").strip())
            # Join with blank line
            body = "\n\n".join(paras)
        else:
            body = ""

        # Build record
        record = {
            "url": abs_url,
            "title": title,
            "date": date_iso,  # already computed
            "author": author if author else None,
            "body": body
        }
        records.append(record)

    # Sort newest first by date (ISO string sorts correctly)
    records.sort(key=lambda r: r["date"], reverse=True)
    return records
