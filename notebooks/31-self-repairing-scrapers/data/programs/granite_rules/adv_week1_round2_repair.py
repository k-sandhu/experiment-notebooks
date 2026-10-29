import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser
from datetime import datetime

def extract(fetch, listing_url):
    listing_html = fetch(listing_url)
    soup_list = BeautifulSoup(listing_html, "html.parser")
    
    articles = soup_list.find_all("article", class_="nouvelle")
    records = []
    
    for article in articles:
        h2 = article.find("h2")
        if not h2:
            continue
        link_tag = h2.find("a")
        if not link_tag or not link_tag.get("href"):
            continue
        rel_url = link_tag["href"]
        abs_url = urllib.parse.urljoin(listing_url, rel_url)
        
        release_html = fetch(abs_url)
        soup_release = BeautifulSoup(release_html, "html.parser")
        
        h1 = soup_release.find("h1")
        title = h1.get_text(strip=True) if h1 else ""
        
        date_para = soup_release.find("p", class_="date")
        date_text = date_para.get_text(strip=True) if date_para else ""
        date_iso = None
        if date_text:
            try:
                # Use fuzzy parsing to handle "1er septembre 2026" etc.
                dt = parser.parse(date_text, fuzzy=True)
                # Ensure we get a date (no time component)
                if hasattr(dt, 'date'):
                    date_iso = dt.date().isoformat()
                else:
                    date_iso = dt.strftime("%Y-%m-%d")
            except Exception:
                pass
        
        auteur_para = soup_release.find("p", class_="auteur")
        author = None
        if auteur_para:
            text = auteur_para.get_text(strip=True)
            if text.startswith("Par "):
                text = text[4:].strip()
            # Remove trailing punctuation like period
            text = text.rstrip(".")
            # Clean up possible trailing commas or other punctuation
            text = text.rstrip(",")
            # Join multiple names if present (simple heuristic: split on "et" or "et ")
            # Keep it simple: just strip known prefixes/suffixes
            author = text
        
        contenu_div = soup_release.find("div", class_="contenu")
        body_parts = []
        if contenu_div:
            ps = contenu_div.find_all("p")
            for p in ps:
                p_text = p.get_text(separator="\n", strip=True)
                if p_text:
                    body_parts.append(p_text.strip())
        body = "\n\n".join(body_parts) if body_parts else ""
        
        records.append({
            "url": abs_url,
            "title": title,
            "date": date_iso,  # May be None if parsing failed
            "author": author if author else None,
            "body": body
        })
    
    # Sort newest first by parsed date; include all records (even with None date)
    def get_sort_key(rec):
        date_str = rec["date"]
        if date_str is None or date_str == "":
            # If date parsing failed, try to extract from title or fallback to far past
            # but for sorting, put them at the end (oldest)
            return datetime.min
        try:
            dt = parser.parse(date_str, fuzzy=True)
            return dt
        except Exception:
            return datetime.min
    
    records.sort(key=get_sort_key, reverse=True)
    return records
