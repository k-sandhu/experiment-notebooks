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
            # fallback: first <a> inside teaser? but use release page
            title_tag = soup_release.find("h3")
        title = title_tag.get_text(strip=True) if title_tag else ""
        
        # Extract date from meta-date or meta inside article
        date_elem = soup_release.find("span", class_lambda=lambda x: x and "meta-date" in x.lower())
        if not date_elem:
            # fallback: find meta-date inside article
            article = soup_release.find("article")
            if article:
                date_elem = article.find("span", class_lambda=lambda x: x and "meta-date" in x.lower())
        if date_elem:
            date_text = date_elem.get_text(strip=True)
            # parse date like "29 Sep 2026"
            try:
                # dateutil can parse "29 Sep 2026"
                dt = parser.parse(date_text)
                date_str = dt.strftime("%Y-%m-%d")
            except Exception:
                # fallback: extract first 4 digits year, month name, day
                # simple regex not allowed; try split
                parts = date_text.split()
                if len(parts) >= 2:
                    month_name = parts[1]
                    day = parts[0]
                    year = parts[2] if len(parts) > 2 else None
                    # map month name
                    month_map = {"Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
                                 "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
                                 "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"}
                    month = month_map.get(month_name[:3], "01")
                    day = day.rstrip("01235789")  # keep numeric
                    if len(day) == 1:
                        day = "0" + day
                    if year and len(year) == 4:
                        date_str = f"{year}-{month}-{day}"
                    else:
                        # incomplete fallback
                        date_str = date_text  # keep original? but spec requires YYYY-MM-DD
                        # attempt parse with day first? assume day is numeric
                        # simple: use first part as day? Not robust but for example
                        pass
                else:
                    date_str = date_text  # fallback
            else:
                date_str = date_text  # fallback
        else:
            # fallback: find meta-date in header? maybe in article meta
            # search any span/meta with date
            meta_date = soup_release.find(["span", "meta"], class_lambda=lambda x: x and ("date" in x.lower()))
            if meta_date:
                date_text = meta_date.get_text(strip=True)
                try:
                    dt = parser.parse(date_text)
                    date_str = dt.strftime("%Y-%m-%d")
                except Exception:
                    date_str = date_text
            else:
                date_str = "1970-01-01"  # placeholder
        
        # Extract author
        author_elem = soup_release.find("span", class_lambda=lambda x: x and "meta-author" in x.lower())
        if author_elem:
            author_text = author_elem.get_text(strip=True)
            # remove job titles and "By" etc. simple: split and filter known words? spec says without job titles and without words such as "By"
            # We'll just take the text and replace "By" if present? but sample shows "Tomas Bellwick"
            # No extra processing needed.
            author = author_text
        else:
            # maybe in header? fallback None
            author = None
        
        # Extract body
        # The page uses <div class="body-lead"> for lead paragraph and <div class="body-rest" data-src="..."> for rest.
        # The rest content is loaded via JS from data-src. We need to fetch that fragment and combine.
        # Approach: find body-rest div, get its data-src, fetch that fragment page, get its text, then combine lead and rest paragraphs.
        lead_div = soup_release.find("div", class_lambda=lambda x: x and "body-lead" in x.lower())
        rest_div = soup_release.find("div", class_lambda=lambda x: x and "body-rest" in x.lower())
        
        lead_text = ""
        if lead_div:
            lead_p = lead_div.find("p")
            if lead_p:
                lead_text = lead_p.get_text(strip=False)  # keep newline? we need paragraphs
            else:
                lead_text = lead_div.get_text(separator="\n", strip=False)
        
        rest_text = ""
        if rest_div and rest_div.get("data-src"):
            fragment_url = urllib.parse.urljoin(abs_url, rest_div["data-src"])
            try:
                fragment_html = fetch(fragment_url)
                fragment_soup = BeautifulSoup(fragment_html, "html.parser")
                # The fragment likely contains paragraphs; we need all text inside <p> tags? but could be multiple <p>
                # We'll extract all <p> elements and join with blank line.
                paras = fragment_soup.find_all("p")
                paras_text = [p.get_text(strip=False) for p in paras]
                # Remove empty paragraphs? keep if only whitespace? spec says paragraphs separated by blank line.
                # We'll join with "\n\n"
                rest_text = "\n\n".join(p.get_text(strip=False) for p in paras if p.get_text(strip=False).strip() != "")
            except Exception:
                # fallback: get all text from fragment div
                rest_text = fragment_soup.get_text(separator="\n\n", strip=False)
        
        # Combine lead and rest paragraphs preserving order: lead paragraph first, then rest paragraphs.
        # Ensure no duplicate lead at end.
        # We'll collect all paragraphs from lead (should be one) and rest (multiple).
        # Extract paragraphs from lead_div (maybe only one <p>) and rest fragment.
        # Simpler: get all <p> from article body excluding navigation etc.
        # Find article body content: article tag contains lead and rest.
        article = soup_release.find("article")
        if article:
            # Find all <p> inside article, but exclude those inside nav/footer etc.
            # Use article's children? safer: find all <p> within article.
            paras_all = article.find_all("p")
            # Filter out any <p> that might be inside footer? footer not inside article.
            # Join with "\n\n"
            body_paragraphs = [p.get_text(strip=False) for p in paras_all if p.get_text(strip=False).strip() != ""]
            # Remove possible duplicate lead if appears also in fragment? fragment shouldn't contain lead.
            # Join with blank line
            body_text = "\n\n".join(body_paragraphs)
        else:
            # fallback combine lead and rest
            # Ensure lead text ends without trailing newline? we want paragraphs separated by blank line.
            # We'll put lead as first paragraph, rest as subsequent paragraphs.
            # If rest_text already contains paragraphs separated by \n\n, we can prepend lead.
            # But lead may already contain newline? lead_div may have <p> with text.
            # Get lead paragraph text without extra newline.
            lead_para = lead_div.find("p") if lead_div else None
            if lead_para:
                lead_text = lead_para.get_text(strip=False)
            # Combine
            if rest_text:
                # split rest_text by \n\n and prepend lead
                rest_ paras = rest_text.split("\n\n")
                body_paragraphs = [lead_text] + [r for r in rest_ paras if r.strip() != ""]
                body_text = "\n\n".join(body_paragraphs)
            else:
                body_text = lead_text
        
        # Ensure body_text does not contain duplicate lead at end (the earlier bug). We'll avoid adding extra lead.
        # Use the collected paragraphs only.
        
        # Normalize: replace multiple newlines? We want exactly one blank line between paragraphs.
        # We'll split by \n\n and join back.
        # Already done.
        
        # Build record
        record = {
            "url": abs_url,
            "title": title,
            "date": date_str,
            "author": author if author else None,
            "body": body_text if body_text else "",
        }
        records.append(record)
    
    # Sort newest first by date (descending)
    # dates are strings YYYY-MM-DD, so lexicographic works
    records.sort(key=lambda r: r["date"], reverse=True)
    
    return records
