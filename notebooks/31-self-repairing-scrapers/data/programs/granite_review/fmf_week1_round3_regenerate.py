import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser

# FetchError is assumed to be defined elsewhere; we only reference it
# No need to redefine it here

def extract(fetch, listing_url):
    # Fetch listing page
    listing_html = fetch(listing_url)
    soup_listing = BeautifulSoup(listing_html, "html.parser")
    
    # Find all media-item divs with itemprop="NewsArticle"
    media_items = soup_listing.find_all("div", class_="media-item", itemprop="NewsArticle")
    
    records = []
    
    for item in media_items:
        # Extract href from the <a> tag inside
        link_tag = item.find("a", itemprop="url")
        if not link_tag:
            continue
        rel_url = link_tag["href"]
        abs_url = urllib.parse.urljoin(listing_url, rel_url)
        
        # Get title from span with itemprop="headline"
        title_tag = item.find("span", itemprop="headline")
        if not title_tag:
            continue
        title = title_tag.get_text(strip=True)
        
        # Get datePublished from meta itemprop="datePublished"
        date_meta = item.find("meta", itemprop="datePublished")
        if not date_meta:
            continue
        date_str = date_meta.get("content", "")
        try:
            # datePublished may be like "2026-09-21" or "2026-09-21T07:00:00+01:00"
            # Use dateutil to parse and get date part
            dt = parser.parse(date_str)
            date = dt.date().isoformat()  # "YYYY-MM-DD"
        except Exception:
            # fallback: try to extract from .when span if needed
            when_span = item.find("span", class_="when")
            if when_span:
                # parse "21 Sep" -> "2026-09-21"? but we need year from meta?
                # Since meta has full date, fallback not used
                date = None
            else:
                continue
        
        # Fetch release page
        try:
            release_html = fetch(abs_url)
        except Exception as e:
            # If fetch fails, skip this record
            continue
        soup_release = BeautifulSoup(release_html, "html.parser")
        
        # Extract author from byline with itemprop="author"
        author_names = []
        # Find byline div
        byline_div = soup_release.find("div", class_="byline")
        if byline_div:
            # Look for itemprop="author" Person inside
            author_meta = byline_div.find("span", itemprop="Person")
            if author_meta:
                name_tag = author_meta.find("span", itemprop="name")
                if name_tag:
                    raw_name = name_tag.get_text(strip=True)
                    # Remove possible "Media centre · " prefix
                    # The byline text might be "Media centre · Elise Marvaux"
                    # We want only the author name(s). Use schema.org author.
                    # If multiple authors? Assume single for now.
                    # Clean: split by "·" and take last part, strip.
                    parts = raw_name.split("·")
                    # Keep only non-empty parts that are not "Media centre"
                    cleaned = [p.strip() for p in parts if p.strip() and p.strip() != "Media centre"]
                    # Join with " and " if multiple? Probably one.
                    if cleaned:
                        author = cleaned[0]  # take first cleaned (author name)
                        # If there are multiple names like "John Doe and Jane Smith", they'd be in same span? unlikely.
                        # We'll just take the first cleaned part that is not empty and not "Media centre"
                        # But if byline includes "Media centre · Elise Marvaux", cleaned = ["Elise Marvaux"]
                        author_names.append(author)
                    # else fallback to None
            # Also fallback: search for all Person items in article
            # Find article with itemprop="NewsArticle"
            article = soup_release.find("article", itemprop="NewsArticle")
            if article:
                authors = article.find_all(itemprop="author")
                for auth in authors:
                    name_tag = auth.find(itemprop="name")
                    if name_tag:
                        name = name_tag.get_text(strip=True)
                        # skip if name is "Media centre" etc. simple filter
                        if name != "Media centre":
                            author_names.append(name)
        # If no author found via schema, set None
        if not author_names:
            author = None
        else:
            # Join multiple names with " and "
            # Remove duplicates? keep order
            # Simple join: " and ".join(author_names)
            author = " and ".join(author_names)
        
        # Extract body from itemprop="articleBody"
        body_div = soup_release.find("div", itemprop="articleBody")
        if body_div:
            # Get paragraphs text, preserve blank lines between paragraphs
            paragraphs = []
            for p in body_div.find_all("p"):
                text = p.get_text(separator="\n", strip=True)
                if text:  # avoid empty paragraphs
                    paragraphs.append(text)
            # Join paragraphs with a blank line between
            body = "\n\n".join(paragraphs)
        else:
            # fallback: get text from article excluding header/footer? but spec says main text only.
            # Use article body children? Not reliable. Skip.
            body = ""
        
        records.append({
            "url": abs_url,
            "title": title,
            "date": date,
            "author": author,
            "body": body
        })
    
    # Sort newest first by date (string YYYY-MM-DD sorts lexicographically)
    records.sort(key=lambda x: x["date"], reverse=True)
    return records
