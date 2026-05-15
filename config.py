from dotenv import load_dotenv
import os

load_dotenv()

def _secret(key: str) -> str:
    """Read from Streamlit secrets (cloud) or environment variables (local)."""
    try:
        import streamlit as st
        return st.secrets.get(key, os.getenv(key, ""))
    except Exception:
        return os.getenv(key, "")

EBAY_APP_ID = _secret("EBAY_APP_ID")
EBAY_CLIENT_SECRET = _secret("EBAY_CLIENT_SECRET")
EBAY_BROWSE_API_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"
EBAY_TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
EBAY_SCOPE = "https://api.ebay.com/oauth/api_scope"

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
