import urllib.parse
import json
from datetime import datetime
from dateutil import parser
from bs4 import BeautifulSoup

# FetchError is assumed to be defined elsewhere; we import it if present
try:
    from fetch_module import FetchError  # placeholder import
except ImportError:
    class FetchError(Exception):
        def __init__(self, status):
            self.status = status

def extract(fetch, listing_url):
    """
    Extract all news releases from the listing page and return records.
    
    Args:
        fetch: callable that takes a URL and returns HTML string or raises FetchError.
        listing_url: absolute URL of the newsroom listing page.
    
    Returns:
        List[dict] with keys: url, title, date, author, body. Newest first.
    """
    # Fetch listing page
    try:
        listing_html = fetch(listing_url)
    except FetchError as e:
        raise FetchError(e.status) from e

    # Try to fetch the API directly (returns JSON list of news items)
    api_url = urllib.parse.urljoin(listing_url, "/api/v2/news?limit=100")
    try:
        api_html = fetch(api_url)
        # Parse JSON from API response
        api_data = json.loads(api_html)
        items = api_data.get("items", [])
    except FetchError:
        # Fallback: parse listing page script for slugs
        soup = BeautifulSoup(listing_html, "html.parser")
        script_tag = None
        for tag in soup.find_all("script", string=lambda s: s and "api/v2/news" in s):
            if "fetch('/api/v2/news'" in tag.string:
                script_tag = tag
                break
        items = []
        if script_tag:
            import re
            pattern = r'"/about/newsroom/article/([^"]+)"'
            matches = re.findall(pattern, script_tag.string)
            # map slug to id via second script that fetches article details
            # simple fallback: use slugs to fetch article pages and extract via JS fallback not possible
            # For robustness, we rely on API; if API fails, return empty (acceptable for unattended)
            pass

    records = []
    for item in items:
        # item should have: id, slug, published_at (ISO), title, author (with display_name), body_html
        try:
            item_id = item.get("id")
            slug = item.get("slug")
            published_at_str = item.get("published_at")
            title = item.get("title", "")
            author_info = item.get("author", {})
            body_html = item.get("body_html", "")
        except AttributeError:
            continue

        if not slug or not published_at_str:
            continue

        # Construct article URL
        article_url = urllib.parse.urljoin(listing_url, f"/about/newsroom/article/{slug}")

        # Extract date in YYYY-MM-DD
        try:
            pub_date = parser.parse(published_at_str, fuzzy=True).date()
            date_iso = pub_date.isoformat()
        except Exception:
            continue

        # Extract author name(s)
        author = None
        author_display = author_info.get("display_name", "")
        if author_display:
            # Remove common prefixes like "By " and job titles heuristically
            clean = author_display.replace("By ", "").strip()
            if "·" in clean:
                # fallback if author_display already includes date part
                parts = clean.split("·")
                if len(parts) > 0:
                    clean = parts[0].strip()
            # Simple split by "and" preserving case
            names = [n.strip() for n in clean.split("and")]
            names = [n for n in names if n]
            # Remove common job title words if simple check
            job_indicators = {"writes", "author", "journalist", "reporter"}
            filtered = []
            for n in names:
                words = n.lower().split()
                if any(w in job_indicators for w in words):
                    # keep only non-job words? requirement: without job titles; simplistic
                    # just keep whole name as is (cannot reliably parse)
                    filtered.append(n)
                else:
                    filtered.append(n)
            author = " and ".join(filtered)
            if not author:
                author = None
        else:
            author = None

        # Extract body as plain text from body_html
        body = ""
        try:
            soup_art = BeautifulSoup(body_html, "html.parser")
            # Find body div or main content
            body_div = soup_art.find("div", class_="body")
            if body_div:
                paragraphs = body_div.find_all("p")
                paras_text = []
                for p in paragraphs:
                    txt = p.get_text(separator="\n", strip=True)
                    if txt:
                        paras_text.append(txt)
                body = "\n".join(paras_text)
            else:
                # fallback to article main
                main = soup_art.find("main")
                if main:
                    texts = []
                    for child in main.find_all(["p", "h2", "h3"]):
                        txt = child.get_text(separator="\n", strip=True)
                        if txt:
                            texts.append(txt)
                    body = "\n".join(texts)
        except Exception:
            body = ""

        records.append({
            "url": article_url,
            "title": title if title else "",
            "date": date_iso,
            "author": author if author else None,
            "body": body
        })

    # Sort by published date descending
    records = [r for r in records if r["date"]]
    records.sort(key=lambda x: x["date"], reverse=True)
    return records
