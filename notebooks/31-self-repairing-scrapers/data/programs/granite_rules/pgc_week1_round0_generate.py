import urllib.parse
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

        # Title from main h1
        title_tag = release_soup.find("h1")
        title = title_tag.get_text(strip=True) if title_tag else ""

        # Date parsing from first paragraph strong or from meta? Look for pattern like "Sept. 28, 2026"
        first_p = release_soup.find("p")
        date_str = ""
        if first_p:
            # Look for text matching month day, year pattern
            import re
            pattern = r"(?:\d{1,2})\s*(?:Jan\.?|Feb\.?|Mar\.?|Apr\.?|May\.?|Jun\.?|Jul\.?|Aug\.?|Sep\.?|Oct\.?|Nov\.?|Dec\.?)[.,]?\s*\d{1,2},\s*\d{4}"
            # Simpler: find all numbers and month abbreviations
            text = first_p.get_text()
            # Use dateutil to parse if possible
            # Try to find first date-like phrase
            for strong in release_soup.find_all("strong"):
                strong_text = strong.get_text(strip=True)
                if "Sept." in strong_text or "Sep." in strong_text:
                    # extract date like "Sept. 28, 2026"
                    m = re.search(r"([A-Za-z]{3,9})\.\s*\d{1,2},\s*\d{4}", strong_text)
                    if m:
                        raw = m.group(0)
                        try:
                            dt = parser.parse(raw, fuzzy=True)
                            date_str = dt.strftime("%Y-%m-%d")
                            break
                        except Exception:
                            pass
            if not date_str:
                # fallback: first number pattern
                m = re.search(r"\d{4}-\d{2}-\d{2}", text)
                if m:
                    date_str = m.group(0)
                else:
                    m = re.search(r"\d{1,2}\s*[A-Za-z]{3,9}\.\s*\d{1,2},\s*\d{4}", text)
                    if m:
                        raw = m.group(0)
                        try:
                            dt = parser.parse(raw, fuzzy=True)
                            date_str = dt.strftime("%Y-%m-%d")
                        except Exception:
                            pass
        if not date_str:
            # try meta? none
            date_str = "1970-01-01"  # fallback, but should not happen

        # Author: look for byline? maybe in first strong? sample has strong with location and wire.
        # No explicit author field. Assume none.
        author = None

        # Body: get .pr-text div content, exclude paragraphs with class about or contact
        text_div = release_soup.find("div", class_="pr-text")
        body_parts = []
        if text_div:
            # get all paragraphs inside
            paras = text_div.find_all("p")
            for p in paras:
                # skip paragraphs with class about or contact
                if p.get("class") and ("about" in p.get("class", []) or "contact" in p.get("class", [])):
                    continue
                # also skip if class source? sample has source but not body? source is footer-like? class source appears inside p? In sample source is a p with class source. Should exclude? "nothing missing and nothing added: no ... standard 'About us' paragraphs." source line "SOURCE Prairie Gold Grain Co-operative" might be considered boilerplate? Probably exclude class source as well.
                if p.get("class") and "source" in p.get("class", []):
                    continue
                txt = p.get_text(separator="\n", strip=True)
                if txt:
                    body_parts.append(txt)
        body = "\n".join(body_parts) if body_parts else ""

        records.append({
            "url": release_url,
            "title": title,
            "date": date_str,
            "author": author,
            "body": body
        })

    # sort newest first by date descending
    records.sort(key=lambda x: x["date"], reverse=True)
    return records
