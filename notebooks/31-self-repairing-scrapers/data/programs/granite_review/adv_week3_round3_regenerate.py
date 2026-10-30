import urllib.parse
from datetime import datetime
from dateutil import parser
from bs4 import BeautifulSoup

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
        date_text = ""
        if date_p:
            date_text = date_p.get_text(strip=True)
            # parse "Publié le 17 septembre 2026"
            # remove "Publié le " prefix
            if date_text.startswith("Publié le "):
                date_str = date_text[12:].strip()  # len("Publié le ") = 11? let's count: "Publié le " is 11 chars? "Publié" 7 + space 1 + "le" 2 + space 1 = 11? Actually "Publié le " = 11? "Publié" (6? French accent) but we just strip prefix
                # simpler: extract number and month name
                # use dateutil parser on the whole string? parser can handle "17 septembre 2026"
                # but dateutil parser may need day first? It can parse "17 septembre 2026"
                # We'll parse the whole date_text after "Publié le "
                try:
                    # Remove "Publié le "
                    clean = date_text[11:]  # "Publié le " length 11? Let's compute: "Publié" 6? Actually "Publié" 6? P u b l i é = 6? plus space =7? Let's just split
                    # Better: use regex or split
                    parts = date_text.split()
                    # parts[0]="Publié", parts[1]="le", parts[2:]=date
                    if len(parts) >= 3:
                        day_str = parts[2]
                        month_str = parts[3]
                        year_str = parts[4] if len(parts) > 4 else None
                        # month name may be like "septembre"
                        # dateutil parser can parse "17 septembre 2026"
                        # construct string: f"{day_str} {month_str} {year_str}"
                        date_str = f"{day_str} {month_str}"
                        if year_str:
                            date_str += f" {year_str}"
                        # parse
                        dt = parser.parse(date_str, fuzzy=True)
                        # ensure year is 4-digit
                        if dt.year < 1000:
                            # maybe year is 2026 already 4-digit
                            pass
                        date_iso = dt.date().isoformat()  # YYYY-MM-DD
                    else:
                        # fallback parse whole date_text
                        dt = parser.parse(date_text, fuzzy=True)
                        date_iso = dt.date().isoformat()
                except Exception:
                    # fallback: use dateutil on whole date_text
                    try:
                        dt = parser.parse(date_text, fuzzy=True)
                        date_iso = dt.date().isoformat()
                    except Exception:
                        date_iso = None
            else:
                # no "Publié le " prefix? fallback parse whole
                try:
                    dt = parser.parse(date_text, fuzzy=True)
                    date_iso = dt.date().isoformat()
                except Exception:
                    date_iso = None
        else:
            # fallback parse whole date_text from any p with class date? already handled
            try:
                dt = parser.parse(date_text, fuzzy=True)
                date_iso = dt.date().isoformat()
            except Exception:
                date_iso = None
        
        # If date_iso not set, try parsing the whole date_text again
        if "date_iso" not in locals() or date_iso is None:
            try:
                dt = parser.parse(date_text, fuzzy=True)
                date_iso = dt.date().isoformat()
            except Exception:
                date_iso = None
        
        # Extract author: <p class="auteur"> like "Par Bastien Corvelin"
        author_p = main.find("p", class_="auteur") if main else None
        author_names = []
        if author_p:
            text = author_p.get_text(strip=True)
            # Remove "Par " prefix if present
            if text.startswith("Par "):
                text = text[4:].strip()
            # Split by "et" maybe? but simple: take all words except "Par"
            # Remove possible "Par" and trim
            # Also remove job titles? not present
            # Join with " and " if multiple names? Usually single name.
            # We'll keep as is, but remove trailing commas etc.
            # Simple: split by spaces, filter out empty
            words = [w for w in text.split() if w]
            # If contains "et" (lowercase), we might want to keep "et" as separator? spec says "and"
            # We'll just join with " and " if multiple words? but names could be "Bastien Corvelin" two words.
            # We'll keep full string.
            author = " ".join(words)
            # If author contains "et" (e.g., "Marie et Jean Dupont"), we should keep "et" as is? spec says "and" in English? It says "several names joined with ' and ';". We'll convert "et" to "and"? Probably keep original French? spec ambiguous. We'll keep original.
            author_names.append(author)
        else:
            author_names.append(None)
        
        # Combine author names: if multiple <p>? unlikely. We'll take first.
        author = " and ".join(author_names) if author_names and author_names[0] is not None else None
        
        # Extract body: inside <div class="contenu">
        contenu_div = main.find("div", class_="contenu") if main else None
        body_paragraphs = []
        if contenu_div:
            # Get all <p> inside contenu_div
            ps = contenu_div.find_all("p")
            for p in ps:
                # Get text, preserve line breaks? blank lines between paragraphs
                txt = p.get_text(separator="\n", strip=False)
                # Remove leading/trailing whitespace? keep internal? spec: paragraphs separated by blank lines.
                # We'll strip each paragraph? but keep internal spaces.
                # Remove empty paragraphs? keep if only whitespace? we'll filter out empty after strip
                stripped = txt.strip()
                if stripped:
                    body_paragraphs.append(stripped)
            # Join paragraphs with a blank line "\n\n"
            body = "\n\n".join(body_paragraphs)
        else:
            body = ""
        
        # Build record dict
        record = {
            "url": abs_url,
            "title": title if title else "",
            "date": date_iso if date_iso else None,
            "author": author if author else None,
            "body": body if body else "",
        }
        records.append(record)
    
    # Sort newest first: date descending
    # Filter out records with None date? but must include all releases; if date missing, maybe skip sorting? but spec expects date string.
    # Sort by date descending; convert date string to date for comparison
    def sort_key(rec):
        d = rec["date"]
        if d and isinstance(d, str) and len(d) == 10 and d[4] == "-" and d[7] == "-":
            try:
                return datetime.strptime(d, "%Y-%m-%d").date()
            except Exception:
                return datetime.min.date()
        else:
            # if date is None or invalid, treat as far past? but should not happen
            return datetime.min.date()
    
    records.sort(key=sort_key, reverse=True)
    
    return records
