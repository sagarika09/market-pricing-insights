import requests
import pandas as pd
from bs4 import BeautifulSoup
from config import HEADERS
from .base import BaseScraper

class VintedScraper(BaseScraper):
    name = "Vinted"
    _search_url = "https://www.vinted.com/catalog"
    # Vinted catalog IDs: Women > Bottoms > Jeans, Women > Tops
    _CATEGORY_MAP = {"Women's Jeans": "1206"}

    def search(self, query: str, condition: str = "All", category: str = "Women's Jeans", brand: str = "", material: str = "") -> pd.DataFrame:
        if brand and brand.lower() not in query.lower():
            query = f"{brand} {query}"
        if material and material.lower() not in query.lower():
            query = f"{query} {material}"
        params = {"search_text": query, "currency": "USD"}
        cat_id = self._CATEGORY_MAP.get(category)
        if cat_id:
            params["catalog[]"] = cat_id
        try:
            resp = requests.get(
                self._search_url,
                params=params,
                headers={**HEADERS, "Accept-Language": "en-US,en;q=0.9"},
                timeout=10,
            )
            resp.raise_for_status()
        except requests.RequestException:
            return self._empty()

        soup = BeautifulSoup(resp.text, "html.parser")
        rows = []

        for card in soup.select('[data-testid="grid-item"]')[:20]:
            title_el = card.select_one('[data-testid*="--description-title"]')
            price_el = card.select_one('[data-testid*="--price-text"]')
            link_el = card.select_one('a[href*="vinted.com/items"]')

            if not (title_el and price_el and link_el):
                continue

            price_text = price_el.text.replace("$", "").replace(",", "").strip()
            try:
                price = float(price_text)
            except ValueError:
                continue

            href = link_el.get("href", "")
            url = f"https://www.vinted.com{href}" if href.startswith("/") else href

            img_el = card.select_one(f'[data-testid*="--image--img"]')
            image_url = img_el.get("src", "") if img_el else ""
            rows.append(self._make_row(title_el.text.strip(), price, url, image_url))

        return pd.DataFrame(rows) if rows else self._empty()
