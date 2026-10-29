import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser
from typing import List, Dict, Optional

# FetchError is assumed to be defined elsewhere in the module's namespace
# from some_module import FetchError  # Not needed here as per instructions

def extract(fetch, listing_url: str):
    """
    Extract all press release records from the Meridian Ratings press listing.
    
    Args:
        fetch: Callable that performs HTTP GET and returns response body as str.
                Raises FetchError for HTTP errors.
        listing_url: URL of the press listing page (e.g., "/press/").
    
    Returns:
        List[Dict] with keys: url, title, date, author, body. Newest first.
    """
    # Fetch listing page
    try:
        listing_html = fetch(listing_url)
    except Exception as e:
        # Re-raise if fetch raises; caller handles FetchError
        raise

    # Parse listing
    soup = BeautifulSoup(listing_html, "html.parser")
    
    # Find press root container; sample shows <div id="press-root">
    press_root = soup.find(id="press-root")
    if not press_root:
        # Fallback: look for article elements under main
        articles = soup.find_all("article", class_="pr")
        if not articles:
            return []
        press_root = soup.body  # use whole body if no container
    else:
        # Ensure press_root is a tag
        if hasattr(press_root, 'contents'):
            pass

    # Collect release links from press_root
    release_links = []
    # Look for links with href containing /press/ and a date pattern or article
    # In sample, links are like /press/2026/09/29/...
    # Find all <a> tags under press_root that point to press releases
    for link_tag in press_root.find_all("a", href=True):
        href = link_tag['href']
        full_url = urllib.parse.urljoin(listing_url.rstrip('/'), href)
        # Only consider links that start with /press/ and contain a date pattern
        if full_url.startswith("/press/"):
            # Avoid internal links like /ratings/, etc.
            # Check if path includes year/month/day pattern
            path = full_url.split('?')[0].split('#')[0]
            parts = path.split('/')
            if len(parts) >= 4 and parts[1] in ('2026', '2025', '2024'):  # simple check
                release_links.append(full_url)

    # Remove duplicates while preserving order
    seen = set()
    unique_links = []
    for link in release_links:
        if link not in seen:
            seen.add(link)
            unique_links.append(link)

    # Sort by date descending (newest first). Extract date from link path.
    def extract_date_from_link(link):
        # link like /press/2026/09/29/...
        path = link.split('?')[0].split('#')[0]
        parts = path.split('/')
        if len(parts) < 4:
            return None
        year_str = parts[1]
        month_str = parts[2]
        day_str = parts[3]
        try:
            # Validate year numeric
            year = int(year_str)
            month = int(month_str)
            day = int(day_str)
            # Use first day of month as placeholder; exact day from link
            # link includes day as parts[3]
            return f"{year:04d}-{month:02d}-{day:02d}"
        except ValueError:
            return None

    dated_links = []
    for link in unique_links:
        date_str = extract_date_from_link(link)
        if date_str:
            dated_links.append((date_str, link))
        else:
            # fallback: try to parse from page title? skip for now
            pass

    # Sort by date descending
    dated_links.sort(key=lambda x: x[0], reverse=True)
    sorted_links = [link for _, link in dated_links]

    # Extract each release
    records = []
    for link in sorted_links:
        try:
            release_html = fetch(link)
        except Exception:
            continue  # skip if fetch fails

        rel_soup = BeautifulSoup(release_html, "html.parser")

        # Find article with class "pr"
        article = rel_soup.find("article", class_="pr")
        if not article:
            continue

        # Title: h1 inside article
        h1 = article.find("h1")
        title = h1.get_text(strip=True) if h1 else ""

        # Meta date: <span class="pr-meta"> contains date like "29 September 2026"
        meta_div = article.find("div", class_="pr-meta")
        date_raw = None
        if meta_div:
            # Find <span> without class or with class? sample: <span>29 September 2026</span>
            date_span = meta_div.find("span")
            if date_span:
                date_text = date_span.get_text(strip=True)
                # Parse "29 September 2026" -> "2026-09-29"
                try:
                    # dateutil parser handles natural language
                    parsed = parser.parse(date_text)
                    # Ensure it's a date (no time)
                    date_str = parsed.strftime("%Y-%m-%d")
                    date_raw = date_str
                except Exception:
                    pass

        # Fallback if date parsing fails: extract from URL path
        if not date_raw:
            # parse from link path
            path = link.split('?')[0].split('#')[0]
            parts = path.split('/')
            if len(parts) >= 4:
                year = parts[1]
                month = parts[2]
                day = parts[3]
                try:
                    date_raw = f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
                except ValueError:
                    pass

        # Author: <span class="analyst">Written by Tomas Belwick</span>
        author_span = article.find("span", class_="analyst")
        author_raw = None
        if author_span:
            # text like "Written by Tomas Belwick"
            text = author_span.get_text(strip=True)
            # Remove "Written by " prefix
            if text.startswith("Written by "):
                author_raw = text[12:].strip()  # len("Written by ") = 12
            else:
                author_raw = text

        # Clean author: remove job titles? sample only name. Keep as is.
        # Remove trailing punctuation? keep as is.
        # If author_raw contains "and"? unlikely. We'll just use raw.
        # If None, set None
        author = author_raw if author_raw else None

        # Body: <div class="pr-body"> paragraphs
        body_div = article.find("div", class_="pr-body")
        body_text_parts = []
        if body_div:
            # Get all <p> children
            paragraphs = body_div.find_all("p")
            for p in paragraphs:
                # Get text, normalize whitespace
                p_text = p.get_text(separator="\n", strip=True)
                if p_text:
                    body_text_parts.append(p_text.strip())
            # Join with blank line (i.e., "\n\n")
            body = "\n\n".join(body_text_parts)
        else:
            # fallback: get all text from article excluding meta and disclaimer
            # Remove meta and disclaimer
            # Find all text nodes between pr-meta and disclaimer? simple: get article text minus meta and disclaimer
            # Remove meta div and disclaimer div
            for meta in article.find_all("div", class_lambda=lambda x: x and "pr-meta" in x):
                meta.decompose()
            for disc in article.find_all("div", class_lambda=lambda x: x and "disclaimer" in x):
                disc.decompose()
            # Now get article text
            article.decompose()  # no, we need body text
            # Simpler: get all text from article children except meta and disclaimer
            # Already removed meta and disclaimer via decompose? but we already have body_div
            # Fallback body empty
            body = ""

        # Ensure body has at least some text; if empty, maybe fallback to article text without meta/disclaimer
        if not body:
            # fallback: get all text from article excluding meta and disclaimer
            for meta in article.find_all("div", class_lambda=lambda x: x and "pr-meta" in x):
                meta.decompose()
            for disc in article.find_all("div", class_lambda=lambda x: x and "disclaimer" in x):
                disc.decompose()
            # Now get text from remaining
            body_text = article.get_text(separator="\n\n", strip=True)
            # Split by blank lines? get_text with separator adds newlines between tags
            body = body_text

        # Normalize body: ensure paragraphs separated by blank line
        # Already joined with "\n\n"
        # Remove leading/trailing newlines
        body = body.strip()

        # Build record
        record = {
            "url": link,
            "title": title,
            "date": date_raw if date_raw else None,
            "author": author,
            "body": body
        }
        # Only include if date not None and body non-empty
        if record["date"] and record["body"]:
            records.append(record)

    return records
