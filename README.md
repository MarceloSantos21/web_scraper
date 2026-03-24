# 🕷️ Web Scraper — Quotes

A web scraper that extracts quotes from [quotes.toscrape.com](http://quotes.toscrape.com), with support for pagination, tag filtering, retry logic, and export to CSV and JSON.

## Features
- Multi-page scraping with configurable page limit
- Tag-based filtering (e.g. only "inspirational" quotes)
- Polite scraping: random delay between requests
- Retry logic for failed requests (3 attempts with backoff)
- Export to **CSV** and **JSON**
- Auto-generated summary report (top authors, top tags)

## Requirements
```bash
pip install -r requirements.txt
```

## Usage

```bash
# Scrape 3 pages (default)
python scraper.py

# Scrape 10 pages
python scraper.py --pages 10

# Scrape only "inspirational" tagged quotes
python scraper.py --tag inspirational --pages 5

# Skip generating the report file
python scraper.py --no-report
```

## Output
Files are saved in the `output/` folder:
```
output/
├── quotes_20241201_143022.csv
├── quotes_20241201_143022.json
└── report_20241201_143022.json
```

## Sample Report Output
```
══════════════════════════════════════════
📊 SCRAPING REPORT
══════════════════════════════════════════
  Total quotes  : 50
  Unique authors: 22
  Unique tags   : 86

  Top authors:
    • Albert Einstein            6 quotes
    • Mark Twain                 5 quotes

  Top tags:
    • love               14x
    • inspirational      13x
══════════════════════════════════════════
```

## Skills Demonstrated
- Web scraping with `requests` + `BeautifulSoup`
- HTML parsing and CSS selectors
- Pagination handling
- Retry logic with exponential backoff
- CSV and JSON file export
- Data aggregation with `collections.Counter`
- Argparse CLI interface
