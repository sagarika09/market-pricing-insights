import pandas as pd
from typing import List
from products import Product
from scrapers import ALL_SCRAPERS
from data.cache import get_cached, save_cache


def fetch_product(product: Product, sources: List[str], condition: str = "All") -> pd.DataFrame:
    """
    For each enabled source, try the cache first, then scrape.
    Runs each keyword query and deduplicates by URL.
    Applies the product's ASP ceiling filter.
    """
    scrapers = [s() for s in ALL_SCRAPERS if s.name in sources]
    frames = []

    for scraper in scrapers:
        source_frames = []
        for keyword in product.keywords:
            cache_key = f"{keyword}||{product.brand}||{product.material}||{product.style}"
            cached = get_cached(cache_key, scraper.name, condition)
            if cached is not None:
                source_frames.append(cached)
            else:
                result = scraper.search(keyword, condition, product.category, product.brand, product.material, product.style)
                if not result.empty:
                    save_cache(cache_key, condition, result)
                    source_frames.append(result)

        if source_frames:
            frames.append(pd.concat(source_frames, ignore_index=True))

    if not frames:
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True)
    df = df.drop_duplicates(subset=["url"])
    df = df[df["price"] <= product.asp_max]
    df = df.sort_values("price").reset_index(drop=True)
    return df


def summary_stats(df: pd.DataFrame) -> dict:
    if df.empty:
        return {}
    return {
        "lowest": df["price"].min(),
        "highest": df["price"].max(),
        "avg": df["price"].mean(),
        "count": len(df),
        "sources": df["source"].nunique(),
    }
