import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser
from typing import List, Dict

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
    except Exception:
        return []

    # Check for RSS feed
    feed_url = urllib.parse.urljoin(listing_url.rstrip('/'), '/press/feed.xml')
    try:
        feed_html = fetch(feed_url)
        # Parse as XML
        feed_soup = BeautifulSoup(feed_html, "html.parser")
        channel = feed_soup.find("channel") or feed_soup.find("rss")
        if channel:
            items = channel.find_all("item")
            records = []
            for item in items:
                link_tag = item.find("link")
                title_tag = item.find("title")
                pub_date_tag = item.find("pubDate")
                desc_tag = item.find("description") or item.find("content")
                # Author may be in author tag or dc:creator
                author_tag = item.find("author")
                dc_creator_tag = item.find("dc:creator")
                # Get link
                if link_tag and link_tag.string:
                    link = urllib.parse.urljoin(listing_url.rstrip('/'), link_tag.string)
                else:
                    continue
                # Title
                title = title_tag.string.strip() if title_tag and title_tag.string else ""
                # Date
                date = None
                if pub_date_tag and pub_date_tag.string:
                    try:
                        pub_date = parser.parse(pub_date_tag.string)
                        date = pub_date.strftime("%Y-%m-%d")
                    except Exception:
                        pass
                # Author
                author = None
                if dc_creator_tag and dc_creator_tag.string:
                    raw = dc_creator_tag.string.strip()
                    # Remove "By " prefix if present (unlikely in dc:creator)
                    if raw.lower().startswith("by "):
                        raw = raw[3:].strip()
                    author = raw
                elif author_tag and author_tag.string:
                    raw = author_tag.string.strip()
                    if raw.lower().startswith("by "):
                        raw = raw[3:].strip()
                    author = raw
                # Body: use description if available, else fetch release page
                body = ""
                if desc_tag and (desc_tag.string or desc_tag.get_text()):
                    desc_text = desc_tag.get_text(separator="\n\n", strip=True)
                    body = desc_text.strip()
                # If body empty or insufficient, fetch release page
                if not body or body.strip() == "":
                    try:
                        release_html = fetch(link)
                        rel_soup = BeautifulSoup(release_html, "html.parser")
                        article = rel_soup.find("article", class_="pr")
                        if article:
                            # Remove meta and disclaimer
                            for meta in article.find_all("div", class_lambda=lambda x: x and "pr-meta" in x):
                                meta.decompose()
                            for disc in article.find_all("div", class_lambda=lambda x: x and "disclaimer" in x):
                                disc.decompose()
                            body_div = article.find("div", class_="pr-body")
                            if body_div:
                                paragraphs = body_div.find_all("p")
                                parts = []
                                for p in paragraphs:
                                    pt = p.get_text(strip=True)
                                    if pt:
                                        parts.append(pt)
                                body = "\n\n".join(parts)
                            else:
                                body = article.get_text(separator="\n\n", strip=True)
                        body = body.strip()
                    except Exception:
                        pass
                # Normalize author: keep as is, ensure no leading/trailing spaces
                if author:
                    author = author.strip()
                # Only include if date not None and body non-empty
                if date and body:
                    records.append({
                        "url": link,
                        "title": title,
                        "date": date,
                        "author": author if author else None,
                        "body": body
                    })
            # Sort by date descending
            records.sort(key=lambda r: r["date"], reverse=True)
            return records
    except Exception:
        pass

    # Fallback to HTML parsing if feed not usable
    soup = BeautifulSoup(listing_html, "html.parser")
    # Look for press releases via pagination or direct links
    press_root = soup.find(id="press-root")
    if not press_root:
        press_root = soup.body

    release_links = []
    for link_tag in press_root.find_all("a", href=True):
        href = link_tag['href']
        full_url = urllib.parse.urljoin(listing_url.rstrip('/'), href)
        if full_url.startswith("/press/"):
            # Accept any /press/ link
            release_links.append(full_url)

    # Deduplicate
    seen = set()
    unique_links = []
    for link in release_links:
        if link not in seen:
            seen.add(link)
            unique_links.append(link)

    # Sort by date from URL descending
    def extract_date_from_link(link):
        path = link.split('?')[0].split('#')[0]
        parts = path.split('/')
        if len(parts) < 4:
            return None
        year_str, month_str, day_str = parts[1], parts[2], parts[3]
        try:
            year = int(year_str)
            month = int(month_str)
            day = int(day_str)
            return f"{year:04d}-{month:02d}-{day:02d}"
        except ValueError:
            return None

    dated_links = []
    for link in unique_links:
        date_str = extract_date_from_link(link)
        if date_str:
            dated_links.append((date_str, link))

    dated_links.sort(key=lambda x: x[0], reverse=True)
    sorted_links = [link for _, link in dated_links]

    records = []
    for link in sorted_links:
        try:
            release_html = fetch(link)
        except Exception:
            continue

        rel_soup = BeautifulSoup(release_html, "html.parser")
        article = rel_soup.find("article", class_="pr")
        if not article:
            continue

        h1 = article.find("h1")
        title = h1.get_text(strip=True) if h1 else ""

        meta_div = article.find("div", class_="pr-meta")
        date_raw = None
        if meta_div:
            date_span = meta_div.find("span")
            if date_span:
                date_text = date_span.get_text(strip=True)
                try:
                    parsed = parser.parse(date_text)
                    date_raw = parsed.strftime("%Y-%m-%d")
                except Exception:
                    pass

        if not date_raw:
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

        author_span = article.find("span", class_="analyst")
        author_raw = None
        if author_span:
            text = author_span.get_text(strip=True)
            if text.lower().startswith("written by "):
                author_raw = text[12:].strip()
            else:
                author_raw = text

        body_div = article.find("div", class_="pr-body")
        body_text_parts = []
        if body_div:
            paragraphs = body_div.find_all("p")
            for p in paragraphs:
                pt = p.get_text(strip=True)
                if pt:
                    body_text_parts.append(pt)
            body = "\n\n".join(body_text_parts)
        else:
            # fallback
            for meta in article.find_all("div", class_lambda=lambda x: x and "pr-meta" in x):
                meta.decompose()
            for disc in article.find_all("div", class_lambda=lambda x: x and "disclaimer" in x):
                disc.decompose()
            body = article.get_text(separator="\n\n", strip=True)
        body = body.strip()

        if date_raw and body:
            author = author_raw if author_raw else None
            records.append({
                "url": link,
                "title": title,
                "date": date_raw,
                "author": author,
                "body": body
            })

    records.sort(key=lambda r: r["date"], reverse=True)
    return records
