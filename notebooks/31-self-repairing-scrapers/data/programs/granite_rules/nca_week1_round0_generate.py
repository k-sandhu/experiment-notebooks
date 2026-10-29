import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser

# FetchError is assumed to be defined elsewhere; we only reference it
# class FetchError:
#     def __init__(self, status):
#         self.status = status

def extract(fetch, listing_url):
    """
    Extract all press releases from the Northstar Credit Analytics listing page.
    
    Args:
        fetch: callable that takes a URL and returns HTML as a string.
        listing_url: the URL of the listing page (e.g., "https://research.northstar-credit.example/insights/press-releases").
    
    Returns:
        List[dict]: each dict contains keys 'url', 'title', 'date', 'author', 'body',
                    sorted newest first.
    """
    # Fetch the listing page
    try:
        listing_html = fetch(listing_url)
    except Exception as e:
        # If fetch raises FetchError (or any exception), re-raise
        raise e

    soup = BeautifulSoup(listing_html, "html.parser")
    
    # Find all card elements that contain press release links
    cards = soup.find_all("div", class_="card")
    records = []
    
    for card in cards:
        # Extract the link (card-link)
        link_tag = card.find("a", class_="card-link")
        if not link_tag:
            continue
        rel_url = link_tag.get("href")
        if not rel_url:
            continue
        abs_url = urllib.parse.urljoin(listing_url, rel_url)
        
        # Extract title from card-title
        title_tag = card.find("h4", class_="card-title")
        if not title_tag:
            continue
        # Get text and clean minimal whitespace
        title = title_tag.get_text(strip=True)
        
        # Extract authors from card-authors
        authors_tag = card.find("div", class_="card-authors")
        author_raw = None
        if authors_tag:
            # Get text, then clean: remove "By" and "and" handling
            raw_text = authors_tag.get_text(strip=True)
            # Remove leading "By " if present
            if raw_text.lower().startswith("by "):
                raw_text = raw_text[3:].strip()
            # Split by commas or "and"? In sample it's "Elise Dorne, Dario Selven"
            # We'll split by commas and "and" but keep simple: split by commas and "and"
            # Actually sample uses comma separated names without "and" in card-authors.
            # In sample: "Elise Dorne, Dario Selven"
            # In sample release page authors are "By Elise Dorne and Dario Selven"
            # We'll just take the raw text after removing "By " and normalize " and "
            # Remove any trailing commas? We'll split by commas and "and"
            parts = []
            # Simple approach: replace " and " with ", " then split by commas
            # But keep original order and join with " and "
            # We'll extract names from <a rel="author"> tags on release page later.
            # For listing, we just store raw text after "By " removal.
            author_raw = raw_text
        
        # Fetch the release page
        try:
            release_html = fetch(abs_url)
        except Exception:
            # Skip if cannot fetch
            continue
        
        release_soup = BeautifulSoup(release_html, "html.parser")
        
        # Extract title from headline (h1.headline)
        headline_tag = release_soup.find("h1", class_="headline")
        if not headline_tag:
            # fallback to title tag? but spec says full headline as plain text
            # Use h1 without class? In sample it's h1.headline
            # If not found, use link title? but spec says full headline as release page shows it.
            # We'll use headline_tag text
            title = title_tag.get_text(strip=True)  # fallback to listing title
        else:
            title = headline_tag.get_text(strip=True)
        
        # Extract date from dateline (class="dateline")
        dateline_tag = release_soup.find("div", class_="dateline")
        date_raw = None
        if dateline_tag:
            date_raw = dateline_tag.get_text(strip=True)
            # Parse to date (YYYY-MM-DD). dateutil can parse "September 24, 2026"
            try:
                date_parsed = parser.parse(date_raw, fuzzy=True)
                # Use date only
                date_str = date_parsed.strftime("%Y-%m-%d")
            except Exception:
                # fallback: extract first 10 chars? but better skip
                date_str = None
        else:
            # fallback: maybe from meta? but spec says dateline present
            date_str = None
        
        # Extract author from .authors div (class="authors")
        authors_div = release_soup.find("div", class_="authors")
        author_final = None
        if authors_div:
            # Get text, remove "By " prefix and any job titles? spec says without job titles and without "By"
            raw_auth = authors_div.get_text(strip=True)
            # Remove leading "By " if present
            if raw_auth.lower().startswith("by "):
                raw_auth = raw_auth[3:].strip()
            # Now raw_auth might be "Elise Dorne and Dario Selven" or "Elise Dorne, Dario Selven"
            # We need to join with " and " and ensure no job titles.
            # In sample: "By <a rel="author">Elise Dorne</a> and <a rel="author">Dario Selven</a>"
            # So text becomes "Elise Dorne and Dario Selven"
            # We'll split by commas and "and" but keep simple: replace commas with " and "? Not needed.
            # We'll extract author names from <a rel="author"> tags
            author_links = authors_div.find_all("a", rel="author")
            names = []
            for link in author_links:
                # link text is the name (e.g., "Elise Dorne")
                name = link.get_text(strip=True)
                names.append(name)
            if len(names) == 1:
                author_final = names[0]
            elif len(names) == 2:
                author_final = f"{names[0]} and {names[1]}"
            else:
                # join with ", " and replace last comma with " and "? but spec says "and"
                # For >2, join first N-1 with ", " and last with " and "
                if len(names) > 2:
                    # join all but last with ", "
                    joined = ", ".join(names[:-1])
                    author_final = f"{joined} and {names[-1]}"
                else:
                    author_final = ", ".join(names)
        else:
            # fallback to listing authors? but spec says release page author
            # If none, set None
            author_final = None
        
        # Extract body from .article-body
        body_div = release_soup.find("div", class_="article-body")
        body_text = ""
        if body_div:
            # Get paragraphs, get text, join with blank line
            paras = body_div.find_all("p")
            paras_texts = [p.get_text(strip=False) for p in paras]
            # Clean each paragraph: keep line breaks? We need paragraphs separated by blank lines.
            # Join with "\n\n"
            body_text = "\n\n".join([p.get_text(strip=False) for p in paras])
        else:
            # fallback: maybe whole main? but spec says article-body
            # skip
            pass
        
        # Build record
        record = {
            "url": abs_url,
            "title": title,
            "date": date_str if date_str else None,  # should not be None
            "author": author_final if author_final else None,
            "body": body_text
        }
        # Only include if date and title present
        if record["date"] and record["title"]:
            records.append(record)
    
    # Sort newest first: date string YYYY-MM-DD sorts lexicographically descending
    records.sort(key=lambda x: x["date"], reverse=True)
    return records
