import urllib.parse
import re
from bs4 import BeautifulSoup
from dateutil import parser
from typing import List, Dict, Optional

class FetchError(Exception):
    def __init__(self, status: int):
        self.status = status
        super().__init__(f"HTTP {status}")

def extract(fetch, listing_url: str) -> List[Dict]:
    try:
        listing_html = fetch(listing_url)
    except FetchError as e:
        raise e

    soup = BeautifulSoup(listing_html, "html.parser")
    pr_divs = soup.find_all("div", class_="pr")
    records = []

    for pr_div in pr_divs:
        link_tag = pr_div.find("a", href=True)
        if not link_tag:
            continue
        rel_url = link_tag["href"]
        release_url = urllib.parse.urljoin(listing_url, rel_url)

        try:
            release_html = fetch(release_url)
        except FetchError:
            continue

        release_soup = BeautifulSoup(release_html, "html.parser")

        title_tag = release_soup.find("h1")
        title = title_tag.get_text(strip=True) if title_tag else ""

        # Find date in first <strong> tag inside first paragraph or first <p>
        date_str = None
        text = release_soup.get_text()
        # Look for pattern like "Sept. 28, 2026" or "Sept 28, 2026"
        m = re.search(r"([A-Za-z]{3,9})\.\s*\d{1,2},\s*\d{4}", text)
        if not m:
            m = re.search(r"([A-Za-z]{3,9})\s*\d{1,2},\s*\d{4}", text)
        if m:
            raw = m.group(0)
            try:
                dt = parser.parse(raw, fuzzy=True)
                date_str = dt.strftime("%Y-%m-%d")
            except Exception:
                pass
        if date_str is None:
            # Last resort: try to find YYYY-MM-DD pattern
            m = re.search(r"\d{4}-\d{2}-\d{2}", text)
            if m:
                date_str = m.group(0)

        # Author: look for byline? sample has no explicit author; return None
        author = None

        # Body: get .pr-text div content, exclude paragraphs with class about, contact, source
        text_div = release_soup.find("div", class_="pr-text")
        body_parts = []
        if text_div:
            paras = text_div.find_all("p")
            for p in paras:
                p_class = p.get("class")
                if p_class:
                    p_class_list = p_class if isinstance(p_class, list) else [p_class]
                    if any(cls.lower() in ["about", "contact", "source"] for cls in p_class_list):
                        continue
                # Get text without stripping internal whitespace? Use get_text with separator None then split?
                # Use get_text(strip=False) to keep line breaks? But <p> already separate.
                txt = p.get_text(strip=False).strip()
                if txt:
                    body_parts.append(txt)
        # Join paragraphs with blank line (\n\n)
        body = "\n\n".join(body_parts) if body_parts else ""

        records.append({
            "url": release_url,
            "title": title,
            "date": date_str if date_str else "",  # fallback empty; caller may filter
            "author": author,
            "body": body
        })

    # Sort newest first by date descending; filter out records with empty date? Not required but safe
    def safe_date_key(rec):
        d = rec["date"]
        if not d or d == "":
            return "1970-01-01"  # oldest
        try:
            # Ensure format YYYY-MM-DD
            return d
        except:
            return "1970-01-01"

    records.sort(key=lambda x: safe_date_key(x), reverse=True)
    return records
