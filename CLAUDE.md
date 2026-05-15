# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the dashboard
streamlit run app.py

# Run from a specific port
streamlit run app.py --server.port 8502
```

No test suite yet. Validate scraper output manually:
```python
from scrapers.ebay import EbayScraper
df = EbayScraper().search("Levi's 501 women")
print(df)
```

## Architecture

**Entry point:** `app.py` → calls `ui/components.py` (sidebar) → `ui/comparison.py` (main view) → `data/processor.py` (fetch + merge) → scrapers + cache.

**Products** are defined statically in `products.py` as `Product` dataclasses. Each product has a list of search keywords and an ASP ceiling (`asp_max`). The processor iterates all keywords for a product across each selected source.

**Scrapers** (`scrapers/`) all subclass `BaseScraper` and implement `search(query) -> pd.DataFrame` returning the canonical schema: `[source, title, price, url, scraped_at]`. eBay uses its Browse API if `EBAY_APP_ID` is set, otherwise falls back to HTML scraping. Poshmark and Vinted are HTML scrapers only.

**Cache** (`data/cache.py`) is a local SQLite database (`price_cache.db`) keyed by `(query, source)` with a 1-hour TTL. This prevents redundant requests on every Streamlit re-render.

**Processor** (`data/processor.py`) runs all keywords through all active scrapers (cache-first), deduplicates by URL, filters to `price <= asp_max`, and sorts by price ascending.

## Configuration

Copy `.env.example` to `.env` and fill in:
- `EBAY_APP_ID` — optional eBay Browse API credential. Without it, eBay falls back to HTML scraping.

Key constants in `config.py`: `CACHE_TTL_SECONDS` (default 3600), `CACHE_DB_PATH`, `SCHEMA_COLUMNS`.

## Adding a New Scraper

1. Create `scrapers/your_source.py` subclassing `BaseScraper`
2. Implement `search(query: str) -> pd.DataFrame` returning `SCHEMA_COLUMNS`
3. Add to `ALL_SCRAPERS` list in `scrapers/__init__.py`

## Adding a New Product

Add a `Product(...)` entry to the `PRODUCTS` list in `products.py`. The dashboard picks it up automatically.

## Known Limitations

- Poshmark and Vinted scraping depends on their HTML structure; selectors may break if they update their pages.
- eBay HTML scraping is rate-limited; the API path is preferred for production use.
- Vinted is primarily a European platform — USD pricing availability may be limited.
