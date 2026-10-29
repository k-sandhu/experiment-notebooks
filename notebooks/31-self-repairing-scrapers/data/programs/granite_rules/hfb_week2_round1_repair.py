import urllib.parse
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

    # Parse listing page
    soup = BeautifulSoup(listing_html, "html.parser")
    
    # Look for script that fetches JSON; extract slugs via regex
    script_tag = None
    for tag in soup.find_all("script", string=lambda s: s and "api/v2/news" in s):
        if "fetch('/api/v2/news'" in tag.string:
            script_tag = tag
            break
    
    slugs = []
    if script_tag:
        import re
        pattern = r'"/about/newsroom/article/([^"]+)"'
        matches = re.findall(pattern, script_tag.string)
        slugs = matches
    
    # If no script tag found, fallback to <li> under #newsroom
    if not slugs:
        newsroom_elem = soup.find(id="newsroom")
        if newsroom_elem:
            for li in newsroom_elem.find_all("li"):
                a_tag = li.find("a", href=True)
                if a_tag and "/about/newsroom/article/" in a_tag["href"]:
                    # extract slug from href
                    href = a_tag["href"]
                    # href may be relative like "/about/newsroom/article/slug"
                    # parse to get slug part
                    parts = href.split("/")
                    if len(parts) >= 4 and parts[0] == "" and parts[1] == "about" and parts[2] == "newsroom" and parts[3] == "article":
                        slug = parts[4] if len(parts) > 4 else None
                        if slug:
                            slugs.append(slug)
        # sort slugs by date? we will fetch API for each to get date
    # Deduplicate slugs
    slugs = sorted(set(slugs), reverse=True)  # keep order? we will sort by date later
    
    records = []
    
    for slug in slugs:
        article_url = urllib.parse.urljoin(listing_url, f"/about/newsroom/article/{slug}")
        # Try to fetch article page; if fails, try API endpoint
        article_html = None
        api_url = urllib.parse.urljoin(listing_url, f"/api/v2/news/{slug}")  # API uses id not slug? sample uses 3837
        # Actually API uses numeric id; slug may not match. Use article page fetch.
        try:
            article_html = fetch(article_url)
        except FetchError:
            pass
        
        # If article page fetch failed (maybe 404), try API
        if article_html is None:
            try:
                api_resp = fetch(api_url)
                # parse JSON? fetch returns HTML? API returns JSON; but fetch returns str; we need to parse JSON.
                # Since fetch returns HTML string, we cannot get JSON directly.
                # However sample shows script fetches /api/v2/news/3837 and sets fields.
                # We cannot get JSON via fetch because it's JSON endpoint? The fetch returns HTML? Actually API returns JSON.
                # But fetch returns response body as str; we can eval? Not allowed.
                # So fallback: skip if article page fetch fails.
                pass
            except FetchError:
                pass
        
        # Parse article page
        article_soup = BeautifulSoup(article_html, "html.parser") if article_html else None
        
        # Extract title
        title = None
        if article_soup:
            h1_tag = article_soup.find("h1")
            if h1_tag:
                title = h1_tag.get_text(strip=True)
            else:
                # fallback: first <a> with title? not reliable
                pass
        
        # Extract date and author from meta .meta
        date_iso = None
        author = None
        if article_soup:
            meta_tag = article_soup.find("p", class_="meta")
            if meta_tag:
                meta_text = meta_tag.get_text(strip=True)
                # format like "Author · Mon, 01 Jan 2026"
                parts = meta_text.split("·")
                if len(parts) >= 2:
                    date_part = parts[1].strip()
                    try:
                        date_obj = parser.parse(date_part, fuzzy=True)
                        date_iso = date_obj.date().isoformat()
                    except Exception:
                        # fallback regex
                        import re
                        m = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", date_part)
                        if m:
                            date_iso = f"{m.group(1)}-{m.group(2).zfill(2)}-{m.group(3).zfill(2)}"
                if len(parts) >= 1:
                    author_part = parts[0].strip()
                    # clean "By ..."
                    if "By" in author_part:
                        author_part = author_part.replace("By", "").strip()
                    # split by "and"
                    names = [n.strip() for n in author_part.split("and")]
                    # filter empty
                    names = [n for n in names if n]
                    # simple job title removal? not required precise
                    author = " and ".join(names)
        
        # Extract body from .body div
        body = None
        if article_soup:
            body_div = article_soup.find("div", class_="body")
            if body_div:
                paragraphs = body_div.find_all("p")
                paras_text = []
                for p in paragraphs:
                    txt = p.get_text(separator="\n", strip=True)
                    if txt:
                        paras_text.append(txt)
                body = "\n".join(paras_text)
            else:
                # fallback: main content
                main = article_soup.find("main")
                if main:
                    texts = []
                    for child in main.find_all(["p", "h2", "h3"]):
                        txt = child.get_text(separator="\n", strip=True)
                        if txt:
                            texts.append(txt)
                    body = "\n".join(texts)
        
        if title and date_iso and article_url:
            records.append({
                "url": article_url,
                "title": title,
                "date": date_iso,
                "author": author if author else None,
                "body": body if body else ""
            })
    
    # Sort by date descending (newest first)
    # filter out records with missing date
    records = [r for r in records if r["date"]]
    records.sort(key=lambda x: x["date"], reverse=True)
    return records
