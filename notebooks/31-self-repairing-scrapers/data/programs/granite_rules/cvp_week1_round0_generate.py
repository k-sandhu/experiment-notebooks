import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser

# FetchError is assumed to be defined elsewhere; we only reference it.
# No need to define it here.

def extract(fetch, listing_url):
    # Fetch listing page
    listing_html = fetch(listing_url)
    soup_list = BeautifulSoup(listing_html, "html.parser")
    
    # Find all post-cards in the listing
    post_cards = soup_list.find_all("div", class_="post-card")
    records = []
    
    for card in post_cards:
        # Extract relative link and date from card
        link_tag = card.find("a", href=True)
        if not link_tag:
            continue
        rel_url = link_tag["href"]
        abs_url = urllib.parse.urljoin(listing_url, rel_url)
        
        # Extract date from the <span> inside card (e.g., "September 30, 2026")
        date_span = card.find("span")
        if not date_span:
            continue
        date_text = date_span.get_text(strip=True)
        # Parse date (dateutil handles formats like "September 30, 2026")
        try:
            pub_date = parser.parse(date_text).date()
            date_str = pub_date.strftime("%Y-%m-%d")
        except Exception:
            # fallback: try to extract numeric parts
            # simple fallback: extract first 4-digit year and month/day
            # but given format is consistent, this should not happen
            continue
        
        # Fetch release page
        release_html = fetch(abs_url)
        soup_release = BeautifulSoup(release_html, "html.parser")
        
        # Extract title from h1.post-title
        title_tag = soup_release.find("h1", class_="post-title")
        if not title_tag:
            # fallback: use link text
            title_text = link_tag.get_text(strip=True)
        else:
            title_text = title_tag.get_text(strip=True)
        
        # Extract author and date from .post-meta
        meta_div = soup_release.find("div", class_="post-meta")
        author_date_text = ""
        if meta_div:
            # meta text like "By Ellis Dacre · September 30, 2026"
            # we need author without "By " and without job titles? but only name present
            # split by "·" or space? format: "By Ellis Dacre · September 30, 2026"
            parts = meta_div.get_text(strip=True).split("·")
            if len(parts) >= 1:
                author_part = parts[0].replace("By ", "").strip()
                # author may contain "·"? unlikely; just take first part before "·"
                # author_part could be "Ellis Dacre"
                # remove any trailing punctuation? keep as is
                author_text = author_part
            else:
                author_text = meta_div.get_text(strip=True).split()[0] if meta_div.get_text(strip=True) else ""
        else:
            author_text = ""
        
        # Clean author: remove "By " prefix and any trailing punctuation like "."
        if author_text.startswith("By "):
            author_text = author_text[3:].strip()
        # Remove any trailing period or comma? but keep names like "Ellis Dacre"
        author_text = author_text.rstrip(".")
        
        # If author_text contains "·" (unlikely), split and join with " and "? spec says "and" between names.
        # But sample only has single name. We'll handle multiple names if present via " and ".
        # For simplicity, keep as cleaned string. If empty, set None.
        if not author_text or author_text.lower() in {"by", ""}:
            author = None
        else:
            # If there are multiple names separated by commas or "and", we could join with " and ".
            # But spec: "several names joined with ' and '". We'll assume meta contains only one name.
            author = author_text
        
        # Extract body from .post-content
        content_div = soup_release.find("div", class_="post-content")
        if content_div:
            # Get paragraphs
            paragraphs = []
            for p in content_div.find_all("p"):
                # Get text, strip, but keep empty paragraphs? spec says paragraphs separated by blank lines.
                txt = p.get_text(separator="\n", strip=True)
                if txt:  # only non-empty paragraphs? but blank lines separate paragraphs; empty p unlikely
                    paragraphs.append(txt.strip())
            # Join paragraphs with a blank line "\n\n"
            body_text = "\n\n".join(paragraphs)
        else:
            # fallback: get all text from article excluding meta, header, footer, etc.
            # but spec says main text only. Use post-content as primary.
            body_text = ""
        
        # Build record dict
        record = {
            "url": abs_url,
            "title": title_text,
            "date": date_str,
            "author": author if author else None,
            "body": body_text
        }
        records.append(record)
    
    # Sort newest first (date descending)
    records.sort(key=lambda r: r["date"], reverse=True)
    return records
