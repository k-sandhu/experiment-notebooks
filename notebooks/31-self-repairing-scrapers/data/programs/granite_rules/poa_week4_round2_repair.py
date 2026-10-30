import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser

# FetchError is assumed to be defined elsewhere; we only use it via fetch

def extract(fetch, listing_url):
    """Extract all news release records from the listing page.

    Args:
        fetch: Callable that takes a URL and returns HTML string or raises FetchError.
        listing_url: Absolute URL of the news listing page.

    Returns:
        List[dict] with keys: url, title, date, author, body. Newest first.
    """
    try:
        listing_html = fetch(listing_url)
    except Exception as e:
        raise e

    soup = BeautifulSoup(listing_html, "html.parser")
    archive_div = soup.find("div", class_="archive")
    if not archive_div:
        return []

    # Collect all release links with associated month and day from listing
    releases_info = []  # each: (abs_url, month_str, day_str)

    # Find all <ul> inside archive (recursive)
    for ul in archive_div.find_all("ul", recursive=True):
        # Skip footer ul? footer not inside archive
        for li in ul.find_all("li", recursive=False):
            a = li.find("a", href=True)
            if not a:
                continue
            href = a["href"]
            abs_url = urllib.parse.urljoin(listing_url, href)
            if not abs_url.startswith("https://www.pensionsoversight.example/news/"):
                continue

            # Get day <span class="day">
            day_span = li.find("span", class_lambda=lambda x: x and "day" in x.get("class", []))
            day_str = day_span.get_text(strip=True) if day_span else None

            # Find month <h2 class="month"> that is parent of this ul
            # ul is directly under a month heading <h2 class="month">
            # So ul's previous sibling should be the month heading
            prev_sibling = ul.previous_sibling
            month_elem = None
            # Walk backwards to find the nearest preceding h2 with class month
            node = ul.find_parent()
            while node and node != archive_div:
                if node.name == "h2" and "month" in node.get("class", []):
                    month_elem = node
                    break
                node = node.parent
            month_str = month_elem.get_text(strip=True) if month_elem else None

            if day_str and month_str:
                releases_info.append((abs_url, month_str, day_str))

    # Deduplicate by URL (in case of duplicates)
    seen = set()
    unique_info = []
    for abs_url, month_str, day_str in releases_info:
        if abs_url in seen:
            continue
        seen.add(abs_url)
        unique_info.append((abs_url, month_str, day_str))

    records = []

    for abs_url, month_str, day_str in unique_info:
        try:
            release_html = fetch(abs_url)
        except Exception:
            continue

        release_soup = BeautifulSoup(release_html, "html.parser")

        # Title: main <h1>
        title_tag = release_soup.find("h1")
        title = title_tag.get_text(strip=True) if title_tag else ""

        # Date: construct from month_str and day_str (e.g., "October 2026" + "23")
        # month_str like "October 2026"
        try:
            parts = month_str.split()
            if len(parts) == 2:
                month_name = parts[0]
                year_str = parts[1]
                if year_str.isdigit() and len(year_str) == 4:
                    day_int = int(day_str)
                    dt = parser.parse(f"{month_name} {year_str} {day_int}")
                    date_out = dt.date().isoformat()
                else:
                    date_out = None
            else:
                date_out = None
        except Exception:
            date_out = None

        # Author: class "lede-author"
        author_tag = release_soup.find("p", class_lambda=lambda x: x and "lede-author" in x.get("class", []))
        author = None
        if author_tag:
            text = author_tag.get_text(strip=True)
            # Remove "Written by " prefix
            lower_text = text.lower()
            if lower_text.startswith("written by "):
                name_part = text[len("written by "):].strip()
                # Clean trailing punctuation
                name_part = name_part.rstrip(".")
                # Handle "&" -> " and "
                if "&" in name_part:
                    name_part = name_part.replace("&", " and ")
                parts = [p.strip() for p in name_part.split(" and ") if p.strip()]
                author = " and ".join(parts)
            else:
                author = text.strip()
                if author.lower().startswith("by "):
                    author = author[2:].strip()
            # Final cleanup: remove any remaining "by" or "written by" prefixes
            if author:
                lowered = author.lower()
                if lowered.startswith("written by "):
                    author = author[len("written by "):].strip()
                elif lowered.startswith("by "):
                    author = author[2:].strip()
                # Remove trailing job titles? Not required for sample
                author = author.strip()
        if author is None or author == "":
            author = None

        # Body: main text paragraphs inside .article-text
        body_div = release_soup.find("div", class_lambda=lambda x: x and "article-text" in x.get("class", []))
        body = ""
        if body_div:
            paras = []
            for p in body_div.find_all("p", recursive=False):
                txt = p.get_text(separator="\n", strip=True)
                if txt:
                    paras.append(txt)
            body = "\n\n".join(paras)
        else:
            # fallback: main <main> paragraphs excluding lede-author and share
            main = release_soup.find("main")
            if main:
                paras = []
                for p in main.find_all("p", recursive=False):
                    txt = p.get_text(separator="\n", strip=True)
                    if "share" not in txt.lower() and "written by" not in txt.lower():
                        if txt:
                            paras.append(txt)
                body = "\n\n".join(paras)

        # Build record
        record = {
            "url": abs_url,
            "title": title,
            "date": date_out if date_out is not None else None,
            "author": author if author is not None else None,
            "body": body,
        }
        records.append(record)

    # Sort newest first by date constructed from month/day
    sortable = []
    for (abs_url, month_str, day_str), rec in zip(unique_info, records):
        try:
            parts = month_str.split()
            if len(parts) == 2:
                month_name = parts[0]
                year_str = parts[1]
                if year_str.isdigit() and len(year_str) == 4:
                    day_int = int(day_str)
                    dt = parser.parse(f"{month_name} {year_str} {day_int}")
                    sortable.append((dt, rec))
                else:
                    sortable.append((parser.parse("1900-01-01"), rec))
            else:
                sortable.append((parser.parse("1900-01-01"), rec))
        except Exception:
            sortable.append((parser.parse("1900-01-01"), rec))

    sortable.sort(key=lambda x: x[0], reverse=True)
    records = [rec for _, rec in sortable]

    return records
