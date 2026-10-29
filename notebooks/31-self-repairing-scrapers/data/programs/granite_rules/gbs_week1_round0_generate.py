import urllib.parse
from datetime import datetime
from dateutil import parser
from bs4 import BeautifulSoup

# FetchError is assumed to be defined elsewhere; we only use its status attribute.
# No need to redefine it here.

def extract(fetch, listing_url):
    # Fetch the listing page
    listing_html = fetch(listing_url)
    soup_listing = BeautifulSoup(listing_html, "html.parser")
    
    # Extract article links from the visible list items
    article_links = []
    news_list = soup_listing.find_class("NewsList_list__aa71L")
    if news_list:
        for item in news_list.find_all("li", class_="NewsList_item__k2Pq9"):
            link_tag = item.find("a", class_="NewsList_link__3vXa1")
            if link_tag and link_tag.get("href"):
                href = link_tag["href"]
                # Resolve relative URL
                abs_url = urllib.parse.urljoin(listing_url, href)
                article_links.append(abs_url)
    
    # Also extract from __NEXT_DATA__ JSON for safety (includes all articles)
    next_data_script = soup_listing.find(attrs={"id": "__NEXT_DATA__", "type": "application/json"})
    if next_data_script and next_data_script.string:
        try:
            props = eval(next_data_script.string)  # Safe in this controlled context
            articles = props.get("props", {}).get("pageProps", {}).get("articles", [])
            for art in articles:
                slug = art.get("slug")
                if slug:
                    href = f"/media/{slug}"
                    abs_url = urllib.parse.urljoin(listing_url, href)
                    if abs_url not in [a["url"] for a in article_links]:  # avoid dupes
                        article_links.append(abs_url)
        except Exception:
            pass
    
    # Collect unique article URLs
    unique_urls = []
    seen = set()
    for url in article_links:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)
    
    # Fetch each article page and extract details
    records = []
    for article_url in unique_urls:
        try:
            article_html = fetch(article_url)
            soup_article = BeautifulSoup(article_html, "html.parser")
            
            # Title from h1
            title_tag = soup_article.find("h1", class_="Heading_h1__a8Xk2")
            title = title_tag.get_text(strip=True) if title_tag else ""
            
            # Date from ArticleMeta span (e.g., "30 September 2026")
            meta_div = soup_article.find(class_="ArticleMeta_meta__9dK1q")
            date_span = meta_div.find("span") if meta_div else None
            date_text = date_span.get_text(strip=True) if date_span else ""
            # Parse date like "30 September 2026" -> "2026-09-30"
            try:
                # dateutil can parse "30 September 2026"
                dt = parser.parse(date_text)
                date_str = dt.strftime("%Y-%m-%d")
            except Exception:
                # fallback: extract from publishedAt in __NEXT_DATA__
                next_data_script = soup_article.find(attrs={"id": "__NEXT_DATA__", "type": "application/json"})
                if next_data_script and next_data_script.string:
                    try:
                        props = eval(next_data_script.string)
                        published_at = props.get("props", {}).get("pageProps", {}).get("article", {}).get("publishedAt")
                        if published_at:
                            dt = parser.parse(published_at)
                            date_str = dt.strftime("%Y-%m-%d")
                        else:
                            date_str = ""
                    except Exception:
                        date_str = ""
                else:
                    date_str = ""
            
            # Author from ArticleMeta author span (e.g., "Daniel Rooke, Corporate Affairs")
            author_span = meta_div.find(class_="ArticleMeta_author__2bN0p") if meta_div else None
            author_text = ""
            if author_span:
                # Get full author text, then strip role/titles like "Corporate Affairs"
                raw_author = author_span.get_text(strip=True)
                # Simple cleaning: split by comma and take first part, then remove "and" etc.
                # Keep only names (letters, spaces, hyphens). Remove job titles after comma.
                parts = raw_author.split(",")
                name_part = parts[0].strip()
                # Remove trailing "and" etc? Not needed; just take name part.
                # Remove common job phrases? We'll just take the first name part.
                # But requirement: without job titles and without words such as "By".
                # We'll extract words that are not typical job titles? Simpler: take first name before comma.
                # Already done.
                author_text = name_part
            # Also check __NEXT_DATA__ author field
            next_data_script = soup_article.find(attrs={"id": "__NEXT_DATA__", "type": "application/json"})
            if next_data_script and next_data_script.string:
                try:
                    props = eval(next_data_script.string)
                    article_info = props.get("props", {}).get("pageProps", {}).get("article", {})
                    author_obj = article_info.get("author", {})
                    if author_obj and "name" in author_obj:
                        # author_obj may have "name" and "role". Use name only.
                        author_text = author_obj["name"]
                    # If author_text still empty, fallback to meta
                except Exception:
                    pass
            
            # Body from RichText paragraphs
            body_paragraphs = []
            rich_div = soup_article.find(class_="RichText_root__x7Qe3")
            if rich_div:
                # Find all p tags with class RichText_p__m1Z0c
                p_tags = rich_div.find_all("p", class_="RichText_p__m1Z0c")
                for p in p_tags:
                    body_paragraphs.append(p.get_text(strip=False))  # keep internal spacing? get_text default collapses whitespace? Use .get_text(separator="\n")
                # Use get_text with separator="\n" to preserve paragraph separation
                # Actually get_text() without separator collapses multiple spaces; better to collect manually.
                # We'll join with "\n" after stripping each paragraph? Keep as is.
                body_text = "\n".join([p.get_text(strip=False) for p in p_tags])
            else:
                # fallback from __NEXT_DATA__ body array
                next_data_script = soup_article.find(attrs={"id": "__NEXT_DATA__", "type": "application/json"})
                if next_data_script and next_data_script.string:
                    try:
                        props = eval(next_data_script.string)
                        body_blocks = props.get("props", {}).get("pageProps", {}).get("article", {}).get("body", [])
                        body_text_parts = []
                        for block in body_blocks:
                            children = block.get("children", [])
                            # flatten spans? simple: get text from first child span
                            for child in children:
                                if "_type" in child and child.get("_type") == "span":
                                    body_text_parts.append(child.get("text", ""))
                        body_text = "\n".join(body_text_parts)
                    except Exception:
                        body_text = ""
                else:
                    body_text = ""
            
            # Use body_text if available, else fallback
            final_body = body_text if body_text else body_text
            
            # Build record
            record = {
                "url": article_url,
                "title": title,
                "date": date_str,
                "author": author_text if author_text else None,
                "body": final_body
            }
            records.append(record)
        except Exception as e:
            # In case of fetch error or parsing error, skip this article
            continue
    
    # Sort newest first by date (YYYY-MM-DD). Use date string comparison or parse.
    def sort_key(rec):
        d = rec["date"]
        if d == "":
            return ""  # will go to end
        try:
            return parser.parse(d)
        except Exception:
            return ""
    
    records.sort(key=sort_key, reverse=True)
    return records
