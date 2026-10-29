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
    # Use find_all with class pattern
    news_list_items = soup_listing.find_all("li", class_="NewsList_item__k2Pq9")
    for item in news_list_items:
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
            # Use json.loads instead of eval
            import json
            props_json = json.loads(next_data_script.string)
            props = props_json.get("props", {})
            pageProps = props.get("pageProps", {})
            articles = pageProps.get("articles", [])
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
            date_str = ""
            if meta_div:
                date_span = meta_div.find("span")  # first span inside meta_div
                if date_span:
                    date_text = date_span.get_text(strip=True)
                    try:
                        dt = parser.parse(date_text)
                        date_str = dt.strftime("%Y-%m-%d")
                    except Exception:
                        pass
            
            # Fallback from __NEXT_DATA__ publishedAt
            next_data_script = soup_article.find(attrs={"id": "__NEXT_DATA__", "type": "application/json"})
            if not date_str and next_data_script and next_data_script.string:
                try:
                    import json
                    props_json = json.loads(next_data_script.string)
                    props = props_json.get("props", {})
                    pageProps = props.get("pageProps", {})
                    article_info = pageProps.get("article", {})
                    published_at = article_info.get("publishedAt")
                    if published_at:
                        dt = parser.parse(published_at)
                        date_str = dt.strftime("%Y-%m-%d")
                except Exception:
                    pass
            
            # Author from ArticleMeta author span (e.g., "Daniel Rooke, Corporate Affairs")
            author_text = None
            if meta_div:
                author_span = meta_div.find(class_="ArticleMeta_author__2bN0p")
                if author_span:
                    raw_author = author_span.get_text(strip=True)
                    # Split by comma and take first part
                    parts = raw_author.split(",")
                    name_part = parts[0].strip()
                    # Remove leading "By" etc. simple strip
                    if name_part.lower().startswith("by "):
                        name_part = name_part[3:].strip()
                    # Keep only name (no role). We'll just use name_part as name.
                    author_text = name_part
            
            # Also check __NEXT_DATA__ author field
            if not author_text and next_data_script and next_data_script.string:
                try:
                    import json
                    props_json = json.loads(next_data_script.string)
                    props = props_json.get("props", {})
                    pageProps = props.get("pageProps", {})
                    article_info = pageProps.get("article", {})
                    author_obj = article_info.get("author", {})
                    if author_obj and "name" in author_obj:
                        author_text = author_obj["name"]
                except Exception:
                    pass
            
            # Body from RichText paragraphs
            body_text = ""
            rich_div = soup_article.find(class_="RichText_root__x7Qe3")
            if rich_div:
                p_tags = rich_div.find_all("p", class_="RichText_p__m1Z0c")
                if p_tags:
                    # Get text of each paragraph preserving internal spacing? Use get_text(strip=False) and join with newline
                    paragraphs = [p.get_text(strip=False) for p in p_tags]
                    # Clean up extra newlines? join with single newline
                    body_text = "\n".join(paragraphs)
            else:
                # fallback from __NEXT_DATA__ body array
                if next_data_script and next_data_script.string:
                    try:
                        import json
                        props_json = json.loads(next_data_script.string)
                        props = props_json.get("props", {})
                        pageProps = props.get("pageProps", {})
                        article_info = pageProps.get("article", {})
                        body_blocks = article_info.get("body", [])
                        body_parts = []
                        for block in body_blocks:
                            children = block.get("children", [])
                            for child in children:
                                if "_type" in child and child.get("_type") == "span":
                                    body_parts.append(child.get("text", ""))
                        body_text = "\n".join(body_parts)
                    except Exception:
                        pass
            
            # Ensure body is a string (may be empty)
            final_body = body_text if body_text else ""
            
            # Build record
            record = {
                "url": article_url,
                "title": title,
                "date": date_str if date_str else "",
                "author": author_text if author_text else None,
                "body": final_body
            }
            records.append(record)
        except Exception:
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
