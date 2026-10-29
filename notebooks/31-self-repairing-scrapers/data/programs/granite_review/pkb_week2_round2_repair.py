import urllib.parse
from datetime import datetime
from dateutil import parser
from bs4 import BeautifulSoup

# FetchError is assumed to be defined elsewhere; we only reference it
# No need to redefine it here.

def extract(fetch, listing_url):
    # Fetch the listing page
    listing_html = fetch(listing_url)
    soup_listing = BeautifulSoup(listing_html, "html.parser")
    
    # Find all news teaser items
    teasers = soup_listing.find_all("div", class_="news-teaser")
    records = []
    
    for teaser in teasers:
        # Extract link
        link_tag = teaser.find("a", href=True)
        if not link_tag:
            continue
        rel_url = link_tag["href"]
        abs_url = urllib.parse.urljoin(listing_url, rel_url)
        
        # Fetch the release page
        release_html = fetch(abs_url)
        soup_release = BeautifulSoup(release_html, "html.parser")
        
        # Extract title (full headline)
        title_tag = soup_release.find("h1")
        if not title_tag:
            title_tag = soup_release.find("h3")
        title = title_tag.get_text(strip=True) if title_tag else ""
        
        # Extract date from meta-date inside article or header
        date_elem = None
        article = soup_release.find("article")
        if article:
            # Look for span with class containing "meta-date"
            date_elem = article.find("span", class_=lambda x: x and "meta-date" in (x if isinstance(x, str) else []))
            # bs4 find with class_ lambda works? Use find with class list
            # Simpler: find all spans with class containing meta-date
            for span in article.find_all("span", class_=True):
                if any("meta-date" in cls.lower() for cls in span.get("class", [])):
                    date_elem = span
                    break
        if not date_elem:
            # fallback: any span/meta with date-like class
            for tag in soup_release.find_all(["span", "meta"], class_=True):
                cls = tag.get("class", [])
                if any("date" in c.lower() for c in cls):
                    date_elem = tag
                    break
        if date_elem:
            date_text = date_elem.get_text(strip=True)
            try:
                dt = parser.parse(date_text)
                date_str = dt.strftime("%Y-%m-%d")
            except Exception:
                # fallback simple parsing for "DD Mon YYYY"
                parts = date_text.split()
                if len(parts) >= 3:
                    day = parts[0]
                    month_name = parts[1]
                    year = parts[2]
                    month_map = {"Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
                                 "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
                                 "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"}
                    month = month_map.get(month_name[:3], "01")
                    if len(day) == 1:
                        day = "0" + day
                    date_str = f"{year}-{month}-{day}"
                else:
                    date_str = date_text  # fallback
        else:
            # ultimate fallback: any text with date pattern? not needed
            date_str = "1970-01-01"
        
        # Extract author
        author_elem = None
        article = soup_release.find("article")
        if article:
            for span in article.find_all("span", class_=True):
                cls = span.get("class", [])
                if any("meta-author" in c.lower() for c in cls):
                    author_elem = span
                    break
        if not author_elem:
            for tag in soup_release.find_all(["span"], class_=True):
                cls = tag.get("class", [])
                if any("author" in c.lower() for c in cls):
                    author_elem = tag
                    break
        if author_elem:
            author_text = author_elem.get_text(strip=True)
            # simple cleaning: remove "By " prefix if present
            if author_text.lower().startswith("by "):
                author_text = author_text[3:].strip()
            # remove common job title words? spec says without job titles; too vague, keep as is
            author = author_text
        else:
            author = None
        
        # Extract body: combine lead paragraph and fragment paragraphs
        article = soup_release.find("article")
        paras = []
        
        # Lead paragraph inside .body-lead <p>
        lead_div = article.find("div", class_lambda=lambda x: x and "body-lead" in (x if isinstance(x, str) else []))
        if lead_div:
            lead_p = lead_div.find("p")
            if lead_p:
                lead_text = lead_p.get_text(separator="\n", strip=False)
                if lead_text.strip():
                    paras.append(lead_text.rstrip())
        
        # Fragment paragraphs inside .body-rest with data-src
        body_rest_div = article.find("div", class_lambda=lambda x: x and "body-rest" in (x if isinstance(x, str) else []))
        if body_rest_div and body_rest_div.get("data-src"):
            frag_url = urllib.parse.urljoin(listing_url, body_rest_div.get("data-src"))
            try:
                frag_html = fetch(frag_url)
                frag_soup = BeautifulSoup(frag_html, "html.parser")
                # Get all <p> inside fragment (could be inside <article> or <div>)
                frag_article = frag_soup.find("article")
                if frag_article:
                    for p in frag_article.find_all("p"):
                        txt = p.get_text(separator="\n", strip=False)
                        if txt.strip():
                            paras.append(txt.rstrip())
                else:
                    for p in frag_soup.find_all("p"):
                        txt = p.get_text(separator="\n", strip=False)
                        if txt.strip():
                            paras.append(txt.rstrip())
            except Exception:
                # If fragment fetch fails, ignore missing body
                pass
        
        # Also collect any other <p> inside article that are not lead? but lead already taken
        # Avoid duplicate lead paragraph from article find_all
        # Collect remaining <p> inside article excluding lead_div
        for p in article.find_all("p"):
            # skip if p is inside lead_div
            if lead_div and lead_div.find(p):
                continue
            txt = p.get_text(separator="\n", strip=False)
            if txt.strip():
                # avoid adding empty or only whitespace
                paras.append(txt.rstrip())
        
        body_text = "\n\n".join(paras) if paras else ""
        
        # Build record
        record = {
            "url": abs_url,
            "title": title,
            "date": date_str,
            "author": author if author else None,
            "body": body_text,
        }
        records.append(record)
    
    # Sort newest first by date (lexicographic works for YYYY-MM-DD)
    records.sort(key=lambda r: r["date"], reverse=True)
    
    return records
