import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser

# Assume FetchError is defined elsewhere; we only use fetch as provided

def extract(fetch, listing_url):
    # Fetch listing page
    listing_html = fetch(listing_url)
    soup_list = BeautifulSoup(listing_html, "html.parser")
    
    # Find all article.nouvelle elements
    articles = soup_list.find_all("article", class_="nouvelle")
    
    records = []
    
    for article in articles:
        # Extract relative link from h2 > a
        h2 = article.find("h2")
        if not h2:
            continue
        link_tag = h2.find("a")
        if not link_tag or not link_tag.get("href"):
            continue
        rel_url = link_tag["href"]
        abs_url = urllib.parse.urljoin(listing_url, rel_url)
        
        # Fetch release page
        release_html = fetch(abs_url)
        soup_release = BeautifulSoup(release_html, "html.parser")
        
        # Title: main h1 text
        h1 = soup_release.find("h1")
        title = h1.get_text(strip=True) if h1 else ""
        
        # Date: find .date paragraph, parse "Publié le 17 septembre 2026"
        date_para = soup_release.find("p", class_="date")
        date_text = date_para.get_text(strip=True) if date_para else ""
        # Expected format: "Publié le 17 septembre 2026" or "Publié le 1er septembre 2026"
        # Extract date part after "Publié le " or similar; use dateutil to parse
        # Remove "Publié le " prefix if present
        if date_text.startswith("Publié le "):
            date_str = date_text[12:]  # len("Publié le ") = 11? Actually "Publié le " = 11? Count: P(1)u2b3i4s5é6 (é)6? Let's just split
            # Simpler: extract numeric day and month name
            # Use dateutil.parser on the whole string maybe works
            try:
                dt = parser.parse(date_text, fuzzy=True)
                date_iso = dt.date().isoformat()
            except Exception:
                # fallback: extract manually
                parts = date_str.split()
                if len(parts) >= 2:
                    day_str = parts[0]
                    month_str = parts[1]
                    # handle "1er" case
                    if day_str.startswith("1er"):
                        day = 1
                        month = month_str[2:]  # "septembre"
                    else:
                        # try parse day
                        try:
                            day = int(day_str)
                        except:
                            day = 1
                        month = month_str
                    # map month name to number
                    from dateutil.parser import parse
                    # use parse with dayfirst? month name works
                    dt = parser.parse(f"{day} {month} 2026", dayfirst=False)
                    date_iso = dt.date().isoformat()
                else:
                    date_iso = "1970-01-01"  # fallback
        else:
            try:
                dt = parser.parse(date_text, fuzzy=True)
                date_iso = dt.date().isoformat()
            except Exception:
                date_iso = "1970-01-01"
        
        # Author: find .auteur paragraph, extract name without "Par " prefix
        auteur_para = soup_release.find("p", class_="auteur")
        author = None
        if auteur_para:
            text = auteur_para.get_text(strip=True)
            # Remove "Par " prefix if present
            if text.startswith("Par "):
                text = text[4:].strip()
            # Clean possible trailing punctuation
            author = text
        
        # Body: find .contenu div, get paragraphs text, preserve blank lines
        contenu_div = soup_release.find("div", class_="contenu")
        body_parts = []
        if contenu_div:
            # Get all <p> inside .contenu
            ps = contenu_div.find_all("p")
            for p in ps:
                # Get text, keep line breaks? We'll join with '\n\n' between paragraphs
                p_text = p.get_text(separator="\n", strip=True)
                if p_text:  # skip empty
                    body_parts.append(p_text.strip())
        # Join with blank line separator
        body = "\n\n".join(body_parts) if body_parts else ""
        
        records.append({
            "url": abs_url,
            "title": title,
            "date": date_iso,
            "author": author if author else None,
            "body": body
        })
    
    # Sort newest first by date descending
    records.sort(key=lambda x: x["date"], reverse=True)
    return records
