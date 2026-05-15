from dotenv import load_dotenv
import os

load_dotenv()

EBAY_APP_ID = os.getenv("EBAY_APP_ID", "")
EBAY_BROWSE_API_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"

CACHE_DB_PATH = "price_cache.db"
CACHE_TTL_SECONDS = 3600  # 1 hour

# Canonical schema returned by every scraper
SCHEMA_COLUMNS = ["source", "title", "price", "url", "image_url", "scraped_at"]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}
