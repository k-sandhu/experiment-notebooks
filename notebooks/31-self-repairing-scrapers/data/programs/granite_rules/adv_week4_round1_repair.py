import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser

# FetchError is assumed to be defined elsewhere; we import it if exists,
# but for completeness we define a minimal version if not present.
try:
    from fetch import FetchError
except ImportError:
    class FetchError(Exception):
        def __init__(self, status):
            self.status = status

def extract(fetch, listing_url):
    """
    Extract all news releases from the listing page and return records.
    """
    # Fetch the listing page
    listing_html = fetch(listing_url)
    soup = BeautifulSoup(listing_html, "html.parser")
    
    # Find all article elements with class "nouvelle"
    articles = soup.find_all("article", class_="nouvelle")
    
    records = []
    
    for article in articles:
        # Extract the link (relative URL) from the <h2><a> tag
        h2 = article.find("h2")
        if not h2:
            continue
        link_tag = h2.find("a", href=True)
        if not link_tag:
            continue
        rel_url = link_tag["href"]
        abs_url = urllib.parse.urljoin(listing_url, rel_url)
        
        # Skip if it's not a news release page (should be /nouvelles/... but safe)
        if not abs_url.startswith("https://www.devvalbrume.example/nouvelles/"):
            continue
        
        # Fetch the release page
        try:
            release_html = fetch(abs_url)
        except FetchError as e:
            # Skip releases that cannot be fetched
            continue
        release_soup = BeautifulSoup(release_html, "html.parser")
        
        # Extract title: the <h1> inside <main>
        main = release_soup.find("main")
        h1 = main.find("h1") if main else None
        if h1:
            title = h1.get_text(strip=True)
        else:
            # fallback: take the first <a> inside h2? but spec says full headline as release page shows it
            # use h2's text? but h2 contains link; safer to use h1
            title = ""
        
        # Extract date: <p class="date"> with text like "Publié le 17 septembre 2026"
        date_p = main.find("p", class_="date") if main else None
        date_iso = None
        if date_p:
            date_text = date_p.get_text(strip=True)
            # Use dateutil parser with fuzzy=True to handle "Publié le ..."
            try:
                dt = parser.parse(date_text, fuzzy=True)
                date_iso = dt.date().isoformat()  # YYYY-MM-DD
            except Exception:
                # fallback: try without fuzzy
                try:
                    dt = parser.parse(date_text, fuzzy=False)
                    date_iso = dt.date().isoformat()
                except Exception:
                    pass
        
        # Extract author: <p class="auteur"> like "Par Bastien Corvelin"
        author = None
        author_p = main.find("p", class_="auteur") if main else None
        if author_p:
            text = author_p.get_text(strip=True)
            # Remove "Par " prefix if present
            if text.startswith("Par "):
                text = text[4:].strip()
            # Remove trailing punctuation like commas? keep as is
            # Join with " and " if multiple names? Usually single name.
            # We'll keep the cleaned text.
            author = text
        
        # Extract body: inside <div class="contenu">
        body = ""
        contenu_div = main.find("div", class_="contenu") if main else None
        if contenu_div:
            # Get all <p> inside contenu_div
            ps = contenu_div.find_all("p")
            body_paragraphs = []
            for p in ps:
                txt = p.get_text(separator="\n", strip=False)
                stripped = txt.strip()
                if stripped:
                    body_paragraphs.append(stripped)
            body = "\n\n".join(body_paragraphs)
        
        # Build record dict
        record = {
            "url": abs_url,
            "title": title if title else "",
            "date": date_iso,  # may be None if parsing failed
            "author": author,  # may be None
            "body": body if body else "",
        }
        records.append(record)
    
    # Sort newest first: filter out records with valid date, sort by date descending,
    # then append records with missing date at the end (oldest assumed)
    def sort_key(rec):
        d = rec["date"]
        if d and isinstance(d, str) and len(d) == 10 and d[4] == "-" and d[7] == "-":
            try:
                return datetime.strptime(d, "%Y-%m-%d").date()
            except Exception:
                return datetime.min.date()
        else:
            # if date is None or invalid, treat as far past? but we should still include
            # use a very early date so they appear after valid ones
            return datetime.min.date()
    
    from datetime import datetime
    # Separate valid and invalid dates
    valid_records = [r for r in records if r["date"] and isinstance(r["date"], str) and len(r["date"]) == 10 and r["date"][4] == "-" and r["date"][7] == "-"]
    invalid_records = [r for r in records if r not in valid_records]
    
    # Sort valid records descending
    valid_records.sort(key=sort_key, reverse=True)
    # Invalid records keep original order (as encountered) or sort by title? spec doesn't specify; keep as is
    records = valid_records + invalid_records
    
    return records
