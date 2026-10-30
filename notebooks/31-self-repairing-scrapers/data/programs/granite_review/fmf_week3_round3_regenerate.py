import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser

# Assume FetchError is defined elsewhere; we only use fetch as provided.

def extract(fetch, listing_url):
    # Fetch listing page
    listing_html = fetch(listing_url)
    soup_listing = BeautifulSoup(listing_html, "html.parser")
    
    # Find all media-item containers
    media_items = soup_listing.find_all("div", class_="media-item")
    
    records = []
    
    for item in media_items:
        # Extract href (relative) from the <a> tag inside
        link_tag = item.find("a", {"itemprop": "url"})
        if not link_tag:
            continue
        rel_url = link_tag["href"]
        abs_url = urllib.parse.urljoin(listing_url, rel_url)
        
        # Get headline from <span itemprop="headline"> or fallback
        headline_tag = item.find("span", {"itemprop": "headline"})
        if headline_tag:
            title = headline_tag.get_text(strip=True)
        else:
            # fallback: link text
            title = link_tag.get_text(strip=True)
        
        # Get datePublished from meta itemprop="datePublished"
        date_meta = item.find("meta", {"itemprop": "datePublished"})
        if date_meta and date_meta.get("content"):
            pub_date_str = date_meta["content"]
            # parse to date (YYYY-MM-DD)
            try:
                dt = parser.parse(pub_date_str)
                date_str = dt.strftime("%Y-%m-%d")
            except Exception:
                # fallback: extract from .when span if needed
                when_span = item.find("span", class_="when")
                if when_span:
                    # format like "12 Oct" -> "2026-10-12"? need year from meta? use datePublished year
                    # we already have year from meta, so ignore when
                    date_str = None
                else:
                    date_str = None
        else:
            date_str = None
        
        # Fetch release page
        release_html = fetch(abs_url)
        soup_release = BeautifulSoup(release_html, "html.parser")
        
        # Extract author
        author_name = None
        byline_div = soup_release.find("div", class_="byline")
        if byline_div:
            # Look for itemprop="author" Person name
            author_item = byline_div.find("span", {"itemprop": "author", "itemscope": True})
            if author_item:
                name_tag = author_item.find("span", {"itemprop": "name"})
                if name_tag:
                    raw_name = name_tag.get_text(strip=True)
                    # Remove "Media centre · " prefix if present
                    if raw_name.startswith("Media centre · "):
                        raw_name = raw_name[15:].strip()
                    # Remove trailing job titles? e.g., "Elise Marvaux, technical affairs manager"
                    # We need only name, not job title. Simple: split on comma and take first part
                    parts = raw_name.split(",")
                    name_only = parts[0].strip()
                    author_name = name_only
                else:
                    # fallback: any text inside byline excluding "Media centre ·"
                    byline_text = byline_div.get_text(separator=" ").strip()
                    if "Media centre" in byline_text:
                        # remove "Media centre ·" prefix
                        cleaned = byline_text.replace("Media centre ·", "").strip()
                        # split by comma and take first
                        parts = cleaned.split(",")
                        author_name = parts[0].strip()
                    else:
                        author_name = byline_text
            else:
                # fallback: any author meta?
                pass
        # If no author found, set None
        
        # Extract body: itemprop="articleBody"
        body_tag = soup_release.find("div", {"itemprop": "articleBody"})
        if body_tag:
            # Get paragraphs and join with blank line
            paragraphs = []
            for p in body_tag.find_all("p"):
                txt = p.get_text(separator="\n", strip=True)
                if txt:  # avoid empty paragraphs
                    paragraphs.append(txt)
            body_text = "\n\n".join(paragraphs)
        else:
            # fallback: find all <p> under article? but spec says main text only
            # Use article body div? We'll take all <p> inside article except member-cta etc.
            article = soup_release.find("article", {"itemscope": True})
            if article:
                # exclude .member-cta and footer? simple collect <p> inside article not in .member-cta
                for p in article.find_all("p"):
                    # skip if p inside .member-cta? check parent class
                    if p.find_parent(class_="member-cta"):
                        continue
                    txt = p.get_text(separator="\n", strip=True)
                    if txt:
                        paragraphs.append(txt)
                body_text = "\n\n".join(paragraphs)
            else:
                body_text = ""
        
        # Build record
        record = {
            "url": abs_url,
            "title": title,
            "date": date_str,
            "author": author_name,
            "body": body_text
        }
        records.append(record)
    
    # Sort newest first by date (YYYY-MM-DD)
    def get_sort_key(rec):
        d = rec["date"]
        if d and len(d) == 10 and "-" in d:
            try:
                return parser.parse(d)
            except Exception:
                return None
        return None
    
    records.sort(key=get_sort_key, reverse=True)
    
    return records
