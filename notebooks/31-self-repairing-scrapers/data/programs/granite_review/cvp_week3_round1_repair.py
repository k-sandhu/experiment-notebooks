import urllib.parse
from bs4 import BeautifulSoup
from dateutil import parser

def extract(fetch, listing_url):
    listing_html = fetch(listing_url)
    soup_list = BeautifulSoup(listing_html, "html.parser")
    
    post_cards = soup_list.find_all("div", class_="post-card")
    records = []
    
    for card in post_cards:
        link_tag = card.find("a", href=True)
        if not link_tag:
            continue
        rel_url = link_tag["href"]
        abs_url = urllib.parse.urljoin(listing_url, rel_url)
        
        date_span = card.find("span")
        if not date_span:
            continue
        date_text = date_span.get_text(strip=True)
        try:
            pub_date = parser.parse(date_text).date()
            date_str = pub_date.strftime("%Y-%m-%d")
        except Exception:
            continue
        
        release_html = fetch(abs_url)
        soup_release = BeautifulSoup(release_html, "html.parser")
        
        title_tag = soup_release.find("h1", class_="post-title")
        if title_tag:
            title_text = title_tag.get_text(strip=True)
        else:
            title_text = link_tag.get_text(strip=True)
        
        meta_div = soup_release.find("div", class_="post-meta")
        author_text = None
        if meta_div:
            meta_text = meta_div.get_text(strip=True)
            # split by "·" (U+2010) or "·" (U+00B7) or simple space? use "·"
            parts = meta_text.split("·")
            if parts:
                first = parts[0].strip()
                if first.startswith("By "):
                    first = first[3:].strip()
                # remove trailing punctuation like "."
                first = first.rstrip(".")
                if first and not first.lower() in {"by", ""}:
                    author_text = first
            else:
                # fallback
                words = meta_text.split()
                if words and words[0].lower() == "by":
                    author_text = " ".join(words[1:])
                else:
                    author_text = " ".join(words)
        
        if author_text is None or author_text.strip() == "":
            author = None
        else:
            # normalize: join multiple names with " and " if commas? simple keep as is
            author = author_text.strip()
        
        content_div = soup_release.find("div", class_="post-content")
        body_text = ""
        if content_div:
            # remove newsletter box and inline related within content_div
            for elem in content_div.find_all(class_=lambda x: x and ("newsletter" in x or "inline-related" in x)):
                elem.decompose()
            # also remove post-tags if inside? tags are outside content_div? in sample tags are after content_div, but safe to remove inside
            for elem in content_div.find_all(class_=lambda x: x and "post-tags" in x):
                elem.decompose()
            paragraphs = []
            for p in content_div.find_all("p"):
                txt = p.get_text(separator="\n", strip=True)
                if txt:
                    paragraphs.append(txt.strip())
            body_text = "\n\n".join(paragraphs)
        
        record = {
            "url": abs_url,
            "title": title_text,
            "date": date_str,
            "author": author if author else None,
            "body": body_text
        }
        records.append(record)
    
    records.sort(key=lambda r: r["date"], reverse=True)
    return records
