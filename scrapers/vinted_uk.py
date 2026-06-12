import requests
import pandas as pd
from bs4 import BeautifulSoup
from config import HEADERS
from .base import BaseScraper


class VintedUKScraper(BaseScraper):
    name = "Vinted UK"
    _search_url = "https://www.vinted.co.uk/catalog"
    # Vinted UK uses different catalog IDs from Vinted US — rely on text search only
    _CATEGORY_MAP: dict = {}

    def search(self, query: str, condition: str = "All", category: str = "Women's Jeans", brand: str = "", material: str = "", style: str = "") -> pd.DataFrame:
        if brand and brand.lower() not in query.lower():
            query = f"{brand} {query}"
        if material and material.lower() not in query.lower():
            query = f"{query} {material}"
        if style and style.lower() not in query.lower():
            query = f"{query} {style}"

        params = {"search_text": query, "currency": "GBP"}
        cat_id = self._CATEGORY_MAP.get(category)
        if cat_id:
            params["catalog[]"] = cat_id

        try:
            resp = requests.get(
                self._search_url,
                params=params,
                headers={**HEADERS, "Accept-Language": "en-GB,en;q=0.9"},
                timeout=10,
            )
            resp.raise_for_status()
        except requests.RequestException:
            return self._empty()

        soup = BeautifulSoup(resp.text, "html.parser")
        rows = []

        for card in soup.select('[data-testid="grid-item"]')[:20]:
            title_el    = card.select_one('[data-testid*="--description-title"]')
            subtitle_el = card.select_one('[data-testid*="--description-subtitle"]')
            price_el    = card.select_one('[data-testid*="--price-text"]')
            link_el     = card.select_one('a[data-testid*="--overlay-link"]') or card.select_one('a[href*="/items/"]')

            if not (title_el and price_el and link_el):
                continue

            title = title_el.text.strip()
            if subtitle_el:
                title = f"{title} {subtitle_el.text.strip()}"

            price_text = price_el.text.replace("£", "").replace(",", "").strip()
            try:
                price = float(price_text)
            except ValueError:
                continue

            href = link_el.get("href", "")
            url = f"https://www.vinted.co.uk{href}" if href.startswith("/") else href

            img_el = card.select_one('[data-testid*="--image--img"]')
            image_url = img_el.get("src", "") if img_el else ""
            rows.append(self._make_row(title, price, url, image_url))

        return pd.DataFrame(rows) if rows else self._empty()
