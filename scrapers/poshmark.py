import requests
import pandas as pd
from bs4 import BeautifulSoup
from config import HEADERS
from .base import BaseScraper


class PoshmarkScraper(BaseScraper):
    name = "Poshmark"
    _search_url = "https://poshmark.com/search"
    _CATEGORY_MAP = {
        "Women's Jeans":     {"category": "Bottoms", "subcategory": "Jeans"},
        "Women's Tops":      {"category": "Tops", "subcategory": "Crop+Tops"},
        "Women's Handbags":  {"category": "Handbags"},
    }

    def search(self, query: str, condition: str = "All", category: str = "Women's Jeans", brand: str = "", material: str = "") -> pd.DataFrame:
        if material and material.lower() not in query.lower():
            query = f"{query} {material}"
        cat = self._CATEGORY_MAP.get(category, self._CATEGORY_MAP["Women's Jeans"])
        params = {
            "query": query,
            "type": "listings",
            "src": "dir",
            "department": "Women",
            **cat,
        }
        if brand:
            params["brand[]"] = brand
        try:
            resp = requests.get(
                self._search_url,
                params=params,
                headers=HEADERS,
                timeout=10,
            )
            resp.raise_for_status()
        except requests.RequestException:
            return self._empty()

        soup = BeautifulSoup(resp.text, "html.parser")
        rows = []

        for card in soup.select('[data-et-name="listing"]')[:20]:
            title_el = card.select_one(".tile-grid-redesign__title")
            price_el = card.select_one(".tile-grid-redesign__price-current")
            link_el = card.select_one("a[href]")

            if not (title_el and price_el and link_el):
                continue

            price_text = price_el.text.replace("$", "").replace(",", "").strip()
            try:
                price = float(price_text)
            except ValueError:
                continue

            href = link_el.get("href", "")
            url = f"https://poshmark.com{href}" if href.startswith("/") else href

            img_el = card.select_one("img")
            image_url = img_el.get("src", "") if img_el else ""
            rows.append(self._make_row(title_el.text.strip(), price, url, image_url))

        return pd.DataFrame(rows) if rows else self._empty()
