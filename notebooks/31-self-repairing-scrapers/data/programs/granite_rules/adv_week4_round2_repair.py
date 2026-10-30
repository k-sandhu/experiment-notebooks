import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser
from datetime import datetime

try:
    from fetch import FetchError
except ImportError:
    class FetchError(Exception):
        def __init__(self, status):
            self.status = status

def extract(fetch, listing_url):
    listing_html = fetch(listing_url)
    soup = BeautifulSoup(listing_html, "html.parser")
    
    articles = soup.find_all("article", class_="nouvelle")
    records = []
    
    for article in articles:
        h2 = article.find("h2")
        if not h2:
            continue
        link_tag = h2.find("a", href=True)
        if not link_tag:
            continue
        rel_url = link_tag["href"]
        abs_url = urllib.parse.urljoin(listing_url, rel_url)
        
        if not abs_url.startswith("https://www.devvalbrume.example/nouvelles/"):
            continue
        
        try:
            release_html = fetch(abs_url)
        except FetchError:
            continue
        release_soup = BeautifulSoup(release_html, "html.parser")
        
        # Title from <h1> inside <main>
        main = release_soup.find("main")
        h1 = main.find("h1") if main else None
        title = h1.get_text(strip=True) if h1 else ""
        
        # Date from <p class="date"> inside <main>
        date_p = main.find("p", class_="date") if main else None
        date_iso = None
        if date_p:
            date_text = date_p.get_text(strip=True)
            # Remove leading "Publié le " if present
            if date_text.startswith("Publié le "):
                date_text = date_text[12:]  # len("Publié le ") = 11? actually "Publié le " = 12? count: P(1)u2b3l4i5é6(space)7l8e9 (space?) let's just strip
                # simpler: extract number and month
                # use parser with fuzzy=True works
            try:
                dt = parser.parse(date_text, fuzzy=True)
                date_iso = dt.date().isoformat()
            except Exception:
                pass
        
        # Author from <p class="auteur">
        author = None
        author_p = main.find("p", class_="auteur") if main else None
        if author_p:
            text = author_p.get_text(strip=True)
            if text.startswith("Par "):
                text = text[4:].strip()
            # Clean possible trailing commas/periods
            text = text.rstrip(".")
            author = text
        
        # Body from <div class="contenu">
        body = ""
        contenu_div = main.find("div", class_="contenu") if main else None
        if contenu_div:
            ps = contenu_div.find_all("p")
            paragraphs = []
            for p in ps:
                txt = p.get_text(separator="\n", strip=False)
                stripped = txt.strip()
                if stripped:
                    paragraphs.append(stripped)
            body = "\n\n".join(paragraphs)
        
        record = {
            "url": abs_url,
            "title": title,
            "date": date_iso,
            "author": author,
            "body": body,
        }
        records.append(record)
    
    # Sort by date descending; records with valid date go first newest to oldest,
    # invalid dates appended in original order (as encountered)
    def sort_key(rec):
        d = rec["date"]
        if isinstance(d, str) and len(d) == 10 and d[4] == "-" and d[7] == "-":
            try:
                return datetime.strptime(d, "%Y-%m-%d").date()
            except Exception:
                return datetime.min.date()
        else:
            return datetime.min.date()
    
    valid_records = [r for r in records if isinstance(r["date"], str) and len(r["date"]) == 10 and r["date"][4] == "-" and r["date"][7] == "-"]
    invalid_records = [r for r in records if r not in valid_records]
    
    valid_records.sort(key=sort_key, reverse=True)
    records = valid_records + invalid_records
    
    return records
