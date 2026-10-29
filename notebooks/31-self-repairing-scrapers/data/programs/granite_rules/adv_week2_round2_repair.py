import re
from urllib.parse import urljoin
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
        # Extract the part after "Publié le "
        match = re.search(r"Publié\s+le\s+(.+)", date_text, re.IGNORECASE)
        if not match:
            continue
        date_part = match.group(1)
        try:
            # dateutil can parse "8 octobre 2026", "6 octobre 2026", "17 septembre 2026", "1er septembre 2026"
            dt = date_parser.parse(date_part, fuzzy=True)
            date_iso = dt.date().isoformat()
        except Exception:
            continue

        author_tag = soup_release.find("p", class_="auteur")
        if author_tag:
            author_text = author_tag.get_text(strip=True)
            # Remove leading "Par " (case insensitive) and any trailing punctuation
            if author_text.lower().startswith("par "):
                author_text = author_text[4:].strip()
            author_text = author_text.rstrip(".")
            # Keep only words (no job titles etc.; simple cleaning)
            words = author_text.split()
            # Remove common "Par" prefix already handled; keep all words
            # Join with " and " if multiple names? The site uses single author names like "Bastien Corvelin".
            # If there are multiple names separated by commas or "et", we join with " and ".
            # Simple approach: keep as is, but ensure no "Par " prefix.
            author = " ".join(words) if words else None
        else:
            author = None

        contenu_div = soup_release.find("div", class_="contenu")
        if contenu_div:
            paras = []
            for p in contenu_div.find_all("p"):
                # Get text without extra newline conversion; keep paragraph separation
                paras.append(p.get_text(strip=False))
            # Join paragraphs with a blank line; ensure no extra spaces at start/end of paragraphs
            body_lines = [p.get_text(strip=False).rstrip() for p in paras]
            # Remove empty paragraphs that may arise from tags
            body_lines = [line for line in body_lines if line.strip() != ""]
            body = "\n\n".join(body_lines)
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

    # Sort by date descending (newest first)
    records.sort(key=lambda r: r["date"], reverse=True)
    return records
