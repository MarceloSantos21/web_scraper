"""
Web Scraper — Quotes & News
============================
Scrapes quotes from quotes.toscrape.com and saves results to CSV and JSON.
Includes pagination, tag filtering, retry logic and a summary report.
"""

import requests
from bs4 import BeautifulSoup
import csv
import json
import time
import random
import sys
from datetime import datetime
from pathlib import Path
from collections import Counter

BASE_URL = "http://quotes.toscrape.com"
OUTPUT_DIR = Path("output")
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


# ── HTTP ──────────────────────────────────────────────────────────────────────

def fetch_page(url: str, retries: int = 3, delay: float = 1.5) -> BeautifulSoup | None:
    """Fetch a page with retry logic and polite delay."""
    for attempt in range(1, retries + 1):
        try:
            print(f"  ↳ Fetching: {url}  (attempt {attempt})")
            resp = requests.get(url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            time.sleep(delay + random.uniform(0, 0.5))  # polite delay
            return BeautifulSoup(resp.text, "html.parser")
        except requests.RequestException as e:
            print(f"  ⚠ Error: {e}")
            if attempt < retries:
                time.sleep(delay * attempt)
    return None


# ── Parsing ───────────────────────────────────────────────────────────────────

def parse_quotes(soup: BeautifulSoup) -> list[dict]:
    """Extract all quotes from a page."""
    quotes = []
    for block in soup.select("div.quote"):
        text = block.select_one("span.text")
        author = block.select_one("small.author")
        tags = block.select("a.tag")
        about_link = block.select_one("a[href*='/author/']")

        quotes.append({
            "text": text.get_text(strip=True).strip("\u201c\u201d") if text else "",
            "author": author.get_text(strip=True) if author else "",
            "tags": [t.get_text(strip=True) for t in tags],
            "author_url": BASE_URL + about_link["href"] if about_link else "",
        })
    return quotes


def get_next_page(soup: BeautifulSoup) -> str | None:
    """Return the next page URL or None."""
    next_btn = soup.select_one("li.next > a")
    return BASE_URL + next_btn["href"] if next_btn else None


# ── Author detail ─────────────────────────────────────────────────────────────

def fetch_author_bio(url: str) -> str:
    """Scrape a short author bio."""
    soup = fetch_page(url, retries=2, delay=1.0)
    if not soup:
        return ""
    born_date = soup.select_one(".author-born-date")
    born_loc = soup.select_one(".author-born-location")
    desc = soup.select_one(".author-description")
    parts = []
    if born_date:
        parts.append(f"Born: {born_date.get_text(strip=True)}")
    if born_loc:
        parts.append(born_loc.get_text(strip=True))
    if desc:
        parts.append(desc.get_text(strip=True)[:200] + "…")
    return " | ".join(parts)


# ── Scraping ──────────────────────────────────────────────────────────────────

def scrape_quotes(max_pages: int = 5, tag_filter: str = "") -> list[dict]:
    """Scrape quotes across multiple pages."""
    all_quotes: list[dict] = []
    url = f"{BASE_URL}/tag/{tag_filter}/" if tag_filter else BASE_URL
    page = 1

    print(f"\n🕷️  Starting scraper — target: {url}")
    print(f"   Max pages: {max_pages}  |  Tag filter: '{tag_filter or 'none'}'\n")

    while url and page <= max_pages:
        print(f"📄 Page {page}/{max_pages}")
        soup = fetch_page(url)
        if not soup:
            print("  ✖ Failed to fetch page. Stopping.")
            break

        page_quotes = parse_quotes(soup)
        all_quotes.extend(page_quotes)
        print(f"  ✔ {len(page_quotes)} quotes scraped (total: {len(all_quotes)})")

        url = get_next_page(soup)
        page += 1

    return all_quotes


# ── Export ────────────────────────────────────────────────────────────────────

def save_csv(quotes: list[dict], path: Path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "author", "tags", "author_url"])
        writer.writeheader()
        for q in quotes:
            writer.writerow({**q, "tags": ", ".join(q["tags"])})
    print(f"  💾 CSV saved → {path}")


def save_json(data: object, path: Path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  💾 JSON saved → {path}")


def generate_report(quotes: list[dict]) -> dict:
    """Build a summary report."""
    all_tags = [tag for q in quotes for tag in q["tags"]]
    tag_counts = Counter(all_tags)
    author_counts = Counter(q["author"] for q in quotes)

    return {
        "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_quotes": len(quotes),
        "unique_authors": len(author_counts),
        "unique_tags": len(tag_counts),
        "top_authors": author_counts.most_common(5),
        "top_tags": tag_counts.most_common(10),
    }


def print_report(report: dict):
    print("\n" + "═" * 50)
    print("📊 SCRAPING REPORT")
    print("═" * 50)
    print(f"  Scraped at    : {report['scraped_at']}")
    print(f"  Total quotes  : {report['total_quotes']}")
    print(f"  Unique authors: {report['unique_authors']}")
    print(f"  Unique tags   : {report['unique_tags']}")
    print("\n  Top authors:")
    for author, count in report["top_authors"]:
        print(f"    • {author:<25} {count} quotes")
    print("\n  Top tags:")
    for tag, count in report["top_tags"]:
        print(f"    • {tag:<20} {count}x")
    print("═" * 50 + "\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="🕷️  Quotes Web Scraper")
    parser.add_argument("-p", "--pages", type=int, default=3,
                        help="Number of pages to scrape (default: 3)")
    parser.add_argument("-t", "--tag", default="",
                        help="Filter by tag (e.g. 'inspirational', 'humor')")
    parser.add_argument("--no-report", action="store_true",
                        help="Skip saving the report")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(exist_ok=True)

    quotes = scrape_quotes(max_pages=args.pages, tag_filter=args.tag)

    if not quotes:
        print("No quotes scraped. Exiting.")
        sys.exit(1)

    print("\n💾 Saving results...")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_csv(quotes, OUTPUT_DIR / f"quotes_{ts}.csv")
    save_json(quotes, OUTPUT_DIR / f"quotes_{ts}.json")

    report = generate_report(quotes)
    if not args.no_report:
        save_json(report, OUTPUT_DIR / f"report_{ts}.json")

    print_report(report)
    print(f"✅ Done! Files saved to ./{OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
