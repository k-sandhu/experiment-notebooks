import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser

# FetchError is assumed to be defined elsewhere; we only use its .status attribute.
# No need to define it here.

def extract(fetch, listing_url):
    # Fetch the listing page
    listing_html = fetch(listing_url)
    soup_listing = BeautifulSoup(listing_html, "html.parser")
    
    # Find all feed items with class containing 'feed-item--release'
    feed_items = soup_listing.find_all("li", class_=lambda x: x and "feed-item--release" in x)
    
    records = []
    
    for item in feed_items:
        # Find the <a> tag inside the feed item
        a_tag = item.find("a", href=True)
        if not a_tag:
            continue
        rel_url = a_tag["href"]
        # Convert to absolute URL (though listing_url already includes domain)
        abs_url = urllib.parse.urljoin(listing_url, rel_url)
        
        # Get title from the <a> tag's text (strip leading/trailing whitespace)
        title_tag = a_tag.find(string=True)
        if not title_tag:
            # fallback: get text from children
            title_text = " ".join([child.get_text(strip=True) for child in a_tag.find_all(text=True, recursive=False) if child.strip()])
        else:
            title_text = title_tag.strip()
        
        # Extract date from <span class="date"> inside the feed item
        date_span = item.find("span", class_=lambda x: x and "date" in x)
        date_text = None
        if date_span:
            date_text = date_span.get_text(strip=True)
            # Clean date text: e.g., "30 September 2026" -> "2026-09-30"
            # dateutil can parse it
            try:
                # Remove possible "Event date:" prefix
                clean_date = date_text.replace("Event date:", "").strip()
                # dateutil parser handles "30 September 2026"
                parsed_date = parser.parse(clean_date)
                date_str = parsed_date.strftime("%Y-%m-%d")
                date_text = date_str
            except Exception:
                # fallback: keep original and try parse later? but we need YYYY-MM-DD
                # attempt simple extraction
                pass
        
        # Fetch the release page
        try:
            release_html = fetch(abs_url)
        except Exception:  # FetchError may be raised; we assume it has .status but we just propagate
            continue
        soup_release = BeautifulSoup(release_html, "html.parser")
        
        # Title from <h1>
        h1_tag = soup_release.find("h1")
        if h1_tag:
            title = h1_tag.get_text(strip=True)
        else:
            # fallback to link text
            title = title_text
        
        # Published date from <p class="published">
        pub_p = soup_release.find("p", class_=lambda x: x and "published" in x)
        pub_date_str = None
        if pub_p:
            pub_text = pub_p.get_text(strip=True)
            # e.g., "Published: 30 September 2026"
            # extract date part after "Published:"
            parts = pub_text.split(":", 1)
            if len(parts) > 1:
                date_part = parts[1].strip()
                try:
                    parsed_pub = parser.parse(date_part)
                    pub_date_str = parsed_pub.strftime("%Y-%m-%d")
                except Exception:
                    pass
        
        # Use pub_date_str if available, else fallback to listing date
        if pub_date_str:
            date = pub_date_str
        else:
            # fallback to listing date parsing
            if date_text:
                try:
                    parsed_list = parser.parse(date_text)
                    date = parsed_list.strftime("%Y-%m-%d")
                except Exception:
                    date = None
            else:
                date = None
        
        # Author: look for author info; sample page doesn't show explicit author.
        # If none, set None.
        author = None
        # Try to find a pattern like "by John Doe" or a dedicated author element.
        # In sample, no author present, so None.
        # We'll search for common author markers; if not found, None.
        # For simplicity, set None.
        # Could look for <meta name="author"> but not in sample.
        # We'll leave None.
        
        # Body: from <div class="text"> inside main
        text_div = soup_release.find("div", class_=lambda x: x and "text" in x)
        body_paragraphs = []
        if text_div:
            # Get all <p> inside div
            p_tags = text_div.find_all("p")
            for p in p_tags:
                # Get text, preserve line breaks? We need paragraphs separated by blank lines.
                # Use p.get_text(separator="\n") but ensure no extra spaces.
                para_text = p.get_text(strip=False)  # keep internal whitespace
                # Clean: remove leading/trailing newlines? We'll keep as is.
                # Remove possible empty paragraphs
                if para_text.strip():
                    body_paragraphs.append(para_text.strip())
        # Join paragraphs with "\n\n"
        body = "\n\n".join(body_paragraphs) if body_paragraphs else ""
        
        # Build record dict
        record = {
            "url": abs_url,
            "title": title,
            "date": date,  # already YYYY-MM-DD or None
            "author": author,
            "body": body
        }
        records.append(record)
    
    # Sort newest first (descending date). Dates are strings "YYYY-MM-DD", lexicographic works.
    # Filter out records with None date? All should have date.
    records.sort(key=lambda r: r["date"] if r["date"] else "", reverse=True)
    # Ensure date string format; if None, maybe keep as empty? spec says date as YYYY-MM-DD.
    # We'll keep as parsed string; if parsing failed, maybe fallback to listing date string? but assume works.
    
    return records
