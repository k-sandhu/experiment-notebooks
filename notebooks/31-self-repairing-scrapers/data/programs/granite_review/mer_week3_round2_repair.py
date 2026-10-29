import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser
from typing import List, Dict

# FetchError is assumed to be defined elsewhere

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
    try:
        listing_html = fetch(listing_url)
    except Exception as e:
        raise e

    records = []

    # Prefer RSS feed for static list
    feed_url = urllib.parse.urljoin(listing_url.rstrip('/'), '/press/feed.xml')
    feed_html = None
    try:
        feed_html = fetch(feed_url)
    except Exception:
        pass

    if feed_html:
        # Parse RSS with BeautifulSoup using XML parser
        soup = BeautifulSoup(feed_html, "xml")
        channel = soup.find("channel")
        if channel:
            items = channel.find_all("item")
            for item in items:
                title_tag = item.find("title")
                link_tag = item.find("link")
                pub_date_tag = item.find("pubDate")
                desc_tag = item.find(["description", "content:encoded"])
                author_tag = item.find(["author", "dc:creator"])

                if not title_tag or not link_tag or not pub_date_tag:
                    continue

                link = link_tag.get("href", "")
                if not link.startswith("http"):
                    link = urllib.parse.urljoin(listing_url, link)

                title = title_tag.get_text(strip=True)

                # Parse pubDate (e.g., "29 Sep 2026 12:00:00 +0000")
                pub_date_text = pub_date_tag.get_text(strip=True)
                try:
                    parsed = parser.parse(pub_date_text)
                    date_str = parsed.strftime("%Y-%m-%d")
                except Exception:
                    date_str = None

                # Extract author name without "By" etc.
                author = None
                if author_tag:
                    raw = author_tag.get_text(strip=True).lower()
                    # Remove common prefixes like "written by ", "by "
                    if raw.startswith("written by "):
                        raw = raw[11:].strip()
                    elif raw.startswith("by "):
                        raw = raw[2:].strip()
                    # Clean extra spaces and punctuation
                    raw = raw.strip().rstrip(".")
                    if raw:
                        # Handle commas: replace with " and"
                        if "," in raw:
                            names = [n.strip() for n in raw.split(",")]
                            names = [n for n in names if n]
                            raw = " and ".join(names)
                        author = raw

                # Fetch release page for body and confirm article structure
                try:
                    release_html = fetch(link)
                except Exception:
                    continue

                release_soup = BeautifulSoup(release_html, "html.parser")
                article = release_soup.find("article", class_="pr")
                if not article:
                    continue

                title_tag_rel = article.find("h1")
                title_rel = title_tag_rel.get_text(strip=True) if title_tag_rel else ""
                title = title_rel  # Use page title

                meta_div = article.find("div", class_="pr-meta")
                date_text = ""
                if meta_div:
                    date_span = meta_div.find("span")
                    if date_span:
                        date_text = date_span.get_text(strip=True)
                # Use RSS date if parsing failed, otherwise parse date_text
                if date_str is None and date_text:
                    try:
                        parsed = parser.parse(date_text)
                        date_str = parsed.strftime("%Y-%m-%d")
                    except Exception:
                        pass

                body_div = article.find("div", class_="pr-body")
                body_text = ""
                if body_div:
                    paras = body_div.find_all("p")
                    paras_text = [p.get_text(strip=False) for p in paras]
                    body_text = "\n\n".join(paras_text)
                else:
                    # Fallback: extract text from article excluding meta and disclaimer
                    for child in article.find_all(["div", "span"]):
                        if child.get("class"):
                            cls = child.get("class")
                            if isinstance(cls, list):
                                if any("pr-meta" in c or "disclaimer" in c for c in cls):
                                    child.decompose()
                            else:
                                if "pr-meta" in cls or "disclaimer" in cls:
                                    child.decompose()
                    body_text = article.get_text(separator="\n\n", strip=False)
                    lines = [line.rstrip() for line in body_text.split("\n")]
                    lines = [line for line in lines if line.strip() != ""]
                    body_text = "\n\n".join(lines)

                rec = {
                    "url": link,
                    "title": title,
                    "date": date_str,
                    "author": author if author else None,
                    "body": body_text
                }
                records.append(rec)

    # Fallback to static parsing if feed unavailable or no records from feed
    if not records:
        soup = BeautifulSoup(listing_html, "html.parser")
        base_url = urllib.parse.urljoin(listing_url.rstrip('/'), '/')
        # Find all links that match press release pattern: /press/YYYY/MM/DD/...
        release_links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            full_href = urllib.parse.urljoin(base_url, href)
            path = full_href.split('?')[0]
            parts = path.split('/')
            if len(parts) >= 4 and parts[1].isdigit() and parts[2].isdigit() and parts[3].isdigit():
                release_links.append(full_href)

        seen = set()
        unique_links = []
        for link in release_links:
            if link not in seen:
                seen.add(link)
                unique_links.append(link)

        for link in unique_links:
            try:
                release_html = fetch(link)
            except Exception:
                continue
            release_soup = BeautifulSoup(release_html, "html.parser")
            article = release_soup.find("article", class_="pr")
            if not article:
                continue
            title_tag = article.find("h1")
            title = title_tag.get_text(strip=True) if title_tag else ""
            meta_div = article.find("div", class_="pr-meta")
            date_text = ""
            if meta_div:
                date_span = meta_div.find("span")
                if date_span:
                    date_text = date_span.get_text(strip=True)
            date_str = None
            if date_text:
                try:
                    parsed = parser.parse(date_text)
                    date_str = parsed.strftime("%Y-%m-%d")
                except Exception:
                    pass
            analyst_span = meta_div.find("span", class_="analyst") if meta_div else None
            author = None
            if analyst_span:
                raw = analyst_span.get_text(strip=True)
                if raw.lower().startswith("written by "):
                    raw = raw[11:].strip()
                if raw.lower().startswith("by "):
                    raw = raw[2:].strip()
                author = raw.rstrip(".")
            body_div = article.find("div", class_="pr-body")
            body_text = ""
            if body_div:
                paras = body_div.find_all("p")
                paras_text = [p.get_text(strip=False) for p in paras]
                body_text = "\n\n".join(paras_text)
            else:
                for child in article.find_all(["div", "span"]):
                    if child.get("class") and ("pr-meta" in child.get("class") or "disclaimer" in child.get("class", "")):
                        child.decompose()
                body_text = article.get_text(separator="\n\n", strip=False)
                lines = [line.rstrip() for line in body_text.split("\n")]
                lines = [line for line in lines if line.strip() != ""]
                body_text = "\n\n".join(lines)
            rec = {
                "url": link,
                "title": title,
                "date": date_str,
                "author": author if author else None,
                "body": body_text
            }
            records.append(rec)

    # Sort newest first by date
    def sort_key(rec):
        d = rec["date"]
        if d is None:
            return ""
        try:
            parsed = parser.parse(d)
            return parsed.isoformat()
        except Exception:
            return ""

    records.sort(key=sort_key, reverse=True)
    return records
