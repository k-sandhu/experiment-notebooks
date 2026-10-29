import urllib.parse
from datetime import datetime
from dateutil import parser
from bs4 import BeautifulSoup

# FetchError is assumed to be defined elsewhere; we import it if present
try:
    from fetch import FetchError
except ImportError:
    class FetchError(Exception):
        def __init__(self, status):
            self.status = status

def extract(fetch, listing_url):
    # Fetch listing page
    html = fetch(listing_url)
    soup = BeautifulSoup(html, "html.parser")
    
    # Find all article items with class "nouvelle"
    articles = soup.find_all("article", class_="nouvelle")
    records = []
    
    for article in articles:
        # Extract relative link from <h2><a>
        h2 = article.find("h2")
        if not h2:
            continue
        link_tag = h2.find("a", href=True)
        if not link_tag:
            continue
        rel_url = link_tag["href"]
        abs_url = urllib.parse.urljoin(listing_url, rel_url)
        
        # Get title from <a> text
        title_tag = link_tag
        title = title_tag.get_text(strip=True)
        
        # Extract date from <p class="date">
        date_p = article.find("p", class_="date")
        date_text = None
        if date_p:
            date_text = date_p.get_text(strip=True)
            # Expected format: "Publié le 17 septembre 2026"
            # Extract numeric day and month name and year
            # Simple parsing with dateutil
            try:
                # Remove "Publié le " prefix
                clean = date_text.replace("Publié le ", "").strip()
                # dateutil can parse "17 septembre 2026"
                dt = parser.parse(clean)
                date_str = dt.strftime("%Y-%m-%d")
            except Exception:
                # Fallback: try regex? but avoid; if fails keep None
                date_str = None
        else:
            date_str = None
        
        # Extract author from <p class="auteur">
        author_p = article.find("p", class_="auteur")
        author = None
        if author_p:
            author_text = author_p.get_text(strip=True)
            # Remove "Par " prefix if present
            if author_text.startswith("Par "):
                author_text = author_text[4:].strip()
            # Remove job titles? Not present; just keep text
            # Join multiple names? Only one expected
            author = author_text
        
        # Fetch full release page
        release_html = fetch(abs_url)
        release_soup = BeautifulSoup(release_html, "html.parser")
        
        # Title from <h1>
        h1 = release_soup.find("h1")
        if h1:
            title = h1.get_text(strip=True)
        else:
            # fallback to link text already have
            pass
        
        # Date from <p class="date"> on release page (same format)
        release_date_p = release_soup.find("p", class_="date")
        if release_date_p:
            release_date_text = release_date_p.get_text(strip=True)
            try:
                clean_release = release_date_text.replace("Publié le ", "").strip()
                dt_release = parser.parse(clean_release)
                date_str = dt_release.strftime("%Y-%m-%d")
            except Exception:
                date_str = None
        else:
            date_str = None
        
        # Author from <p class="auteur"> on release page
        release_author_p = release_soup.find("p", class_="auteur")
        if release_author_p:
            author_text = release_author_p.get_text(strip=True)
            if author_text.startswith("Par "):
                author_text = author_text[4:].strip()
            author = author_text
        else:
            # fallback to listing author if exists
            if author_p:
                author = author_text
        
        # Body from <div class="contenu">
        contenu_div = release_soup.find("div", class_="contenu")
        body_parts = []
        if contenu_div:
            # Get all <p> inside .contenu
            paras = contenu_div.find_all("p")
            for p in paras:
                text = p.get_text(separator="\n", strip=True)
                if text:  # avoid empty
                    body_parts.append(text)
            body = "\n".join(body_parts)
        else:
            # fallback: get all text from main excluding nav/footer? simple
            main = release_soup.find("main")
            if main:
                # get text of all paragraphs inside main excluding share div
                paras = main.find_all("p")
                body_parts = [p.get_text(strip=True) for p in paras if p.get_text(strip=True)]
                body = "\n".join(body_parts)
            else:
                body = ""
        
        # Build record
        record = {
            "url": abs_url,
            "title": title,
            "date": date_str,
            "author": author if author else None,
            "body": body
        }
        records.append(record)
    
    # Sort newest first by date (YYYY-MM-DD string sorts correctly)
    records.sort(key=lambda r: r["date"] or "0000-01-01", reverse=True)
    
    return records
