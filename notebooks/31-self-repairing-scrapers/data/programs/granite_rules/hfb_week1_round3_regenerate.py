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
    
    # Find the script tag that contains JSON data for news items
    script_tag = None
    for tag in soup.find_all("script", string=lambda s: s and "api/v2/news" in s):
        if "fetch('/api/v2/news'" in tag.string:
            script_tag = tag
            break
    
    if script_tag is None:
        # Fallback: look for <li> elements under #newsroom
        news_list = soup.find_id("newsroom")
        if news_list:
            items = []
            for li in news_list.find_all("li"):
                # Extract href and title from <a> and <span>
                a_tag = li.find("a")
                span_tag = li.find("span")
                if a_tag and span_tag:
                    rel_url = urllib.parse.urljoin(listing_url, a_tag["href"])
                    title = a_tag.get_text(strip=True)
                    date_str = span_tag.get_text(strip=True)
                    # Parse date from toLocaleDateString format (e.g., "Mon, 01 Jan 2026")
                    # dateutil can parse many formats
                    try:
                        date_obj = parser.parse(date_str, fuzzy=True)
                        date_iso = date_obj.date().isoformat()
                    except Exception:
                        # If parsing fails, skip or use fallback
                        continue
                    items.append({
                        "url": rel_url,
                        "title": title,
                        "date": date_iso,
                        "author": None,  # will be fetched later
                        "body": None
                    })
            # Sort by date descending (newest first)
            items.sort(key=lambda x: x["date"], reverse=True)
            return items
    
    # If script tag found, extract JSON data via JS eval simulation
    # We cannot eval JS, so parse the script content for JSON pattern
    # Look for something like: d.items = [{...}]
    script_content = script_tag.string
    # Simple regex-like extraction using BeautifulSoup find
    # Look for <script> that fetches JSON and then innerHTML assignment
    # Since we cannot run JS, we rely on the API endpoint directly
    # Extract all /about/newsroom/article/<slug> links from script
    # Find all <a> tags with href pattern in the rendered page? Actually script builds them.
    # Alternative: parse the API endpoint directly
    # We'll extract slugs from script by searching for pattern '/about/newsroom/article/'
    import re
    pattern = r'"/about/newsroom/article/([^"]+)"'
    matches = re.findall(pattern, script_content)
    slugs = matches
    
    # Collect absolute URLs for each article
    records = []
    for slug in slugs:
        article_url = urllib.parse.urljoin(listing_url, f"/about/newsroom/article/{slug}")
        try:
            article_html = fetch(article_url)
        except FetchError as e:
            continue  # skip if fetch fails
        
        # Parse article page
        article_soup = BeautifulSoup(article_html, "html.parser")
        
        # Extract title from <h1> or script-filled
        h1_tag = article_soup.find("h1")
        if h1_tag:
            title = h1_tag.get_text(strip=True)
        else:
            # fallback: first <a> with title? or meta?
            # look for script that sets title
            # simple fallback
            title = "Unknown"
        
        # Extract date from meta or script
        meta_tag = article_soup.find("p", class_="meta")
        if meta_tag:
            meta_text = meta_tag.get_text(strip=True)
            # format like "Author · Mon, 01 Jan 2026"
            # split by '·' and take date part
            parts = meta_text.split("·")
            if len(parts) >= 2:
                date_part = parts[1].strip()
                try:
                    date_obj = parser.parse(date_part, fuzzy=True)
                    date_iso = date_obj.date().isoformat()
                except Exception:
                    # fallback: try to extract YYYY-MM-DD from text
                    import re
                    m = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", date_part)
                    if m:
                        date_iso = f"{m.group(1)}-{m.group(2).zfill(2)}-{m.group(3).zfill(2)}"
                    else:
                        date_iso = None
            else:
                date_iso = None
        else:
            # try to find date in script assignment
            # look for new Date(i.published_at) pattern
            # not reliable; skip
            date_iso = None
        
        # Extract author from meta or script
        author = None
        if meta_tag:
            meta_text = meta_tag.get_text(strip=True)
            # format "Author · Mon, 01 Jan 2026"
            parts = meta_text.split("·")
            if len(parts) >= 2:
                author_part = parts[0].strip()
                # remove "By" etc. simple clean
                if "By" in author_part:
                    author_part = author_part.replace("By", "").strip()
                # split by "and"
                names = [n.strip() for n in author_part.split("and")]
                # remove job titles? simple: keep as is
                author = " and ".join([n for n in names if n])
        
        # Extract body from .body div
        body_div = article_soup.find("div", class_="body")
        if body_div:
            # get inner text, preserve paragraph breaks
            # body_div.innerHTML is set via JS; we get text with newlines for paragraphs
            # find all <p> inside body
            paragraphs = body_div.find_all("p")
            paras_text = []
            for p in paragraphs:
                # get text without extra tags
                txt = p.get_text(separator="\n", strip=True)
                if txt:
                    paras_text.append(txt)
            body = "\n".join(paras_text)
        else:
            # fallback: get all text from article excluding header/footer
            main = article_soup.find("main")
            if main:
                # get text of children that are not header/footer
                texts = []
                for child in main.find_all(["p", "h2", "h3"]):
                    txt = child.get_text(separator="\n", strip=True)
                    if txt:
                        texts.append(txt)
                body = "\n".join(texts)
            else:
                body = article_html  # fallback
        
        # Normalize date string
        if date_iso is None:
            # try to extract from meta or script
            # simple fallback: use today? but must be correct; skip if cannot
            continue
        
        records.append({
            "url": article_url,
            "title": title,
            "date": date_iso,
            "author": author if author else None,
            "body": body
        })
    
    # Sort by date descending (newest first)
    records.sort(key=lambda x: x["date"], reverse=True)
    return records
