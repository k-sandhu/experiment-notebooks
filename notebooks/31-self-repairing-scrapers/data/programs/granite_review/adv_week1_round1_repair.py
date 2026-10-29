import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser

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
        try:
            dt = parser.parse(date_text, fuzzy=True)
            date_iso = dt.date().isoformat()
        except Exception:
            date_iso = None
        
        auteur_para = soup_release.find("p", class_="auteur")
        author = None
        if auteur_para:
            text = auteur_para.get_text(strip=True)
            if text.startswith("Par "):
                text = text[4:].strip()
            # Remove trailing punctuation like period
            text = text.rstrip(".")
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
            "date": date_iso if date_iso else "",
            "author": author if author else None,
            "body": body
        })
    
    # Sort newest first by date descending; filter out records with invalid date
    valid_records = []
    for rec in records:
        if rec["date"]:
            try:
                dt = parser.parse(rec["date"], fuzzy=True)
                valid_records.append(rec)
            except Exception:
                pass
    
    valid_records.sort(key=lambda x: parser.parse(x["date"], fuzzy=True), reverse=True)
    return valid_records
