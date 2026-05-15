import requests
import pandas as pd
from bs4 import BeautifulSoup
from config import EBAY_APP_ID, EBAY_BROWSE_API_URL, HEADERS
from .base import BaseScraper


class EbayScraper(BaseScraper):
    name = "eBay"

    # eBay condition IDs
    _CONDITION_MAP = {"Used": "3000", "New": "1000"}
    # eBay category IDs
    _CATEGORY_MAP = {"Women's Jeans": "11554", "Women's Tops": "53159", "Women's Handbags": "169291"}

    def search(self, query: str, condition: str = "All", category: str = "Women's Jeans", brand: str = "", material: str = "") -> pd.DataFrame:
        if brand and brand.lower() not in query.lower():
            query = f"{brand} {query}"
        if material and material.lower() not in query.lower():
            query = f"{query} {material}"
        if EBAY_APP_ID:
            return self._search_api(query, condition, category)
        return self._search_scrape(query, condition, category)

    def _search_api(self, query: str, condition: str, category: str) -> pd.DataFrame:
        cat_id = self._CATEGORY_MAP.get(category, "11554")
        params = {"q": query, "limit": 20, "category_ids": cat_id}
        if condition in self._CONDITION_MAP:
            params["filter"] = f"conditionIds:{{{self._CONDITION_MAP[condition]}}}"
        try:
            resp = requests.get(
                EBAY_BROWSE_API_URL,
                headers={
                    "Authorization": f"Bearer {EBAY_APP_ID}",
                    "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
                },
                params=params,
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
        except (requests.RequestException, ValueError):
            return self._empty()

        rows = []
        for item in data.get("itemSummaries", []):
            try:
                price = float(item["price"]["value"])
            except (KeyError, ValueError):
                continue
            rows.append(self._make_row(item.get("title", ""), price, item.get("itemWebUrl", "")))

        return pd.DataFrame(rows) if rows else self._empty()

    def _search_scrape(self, query: str, condition: str, category: str) -> pd.DataFrame:
        cat_id = self._CATEGORY_MAP.get(category, "11554")
        params = {"_nkw": query, "_sacat": cat_id}
        if condition in self._CONDITION_MAP:
            params["LH_ItemCondition"] = self._CONDITION_MAP[condition]
        try:
            resp = requests.get(
                "https://www.ebay.com/sch/i.html",
                params=params,
                headers=HEADERS,
                timeout=10,
            )
            resp.raise_for_status()
        except requests.RequestException:
            return self._empty()

        soup = BeautifulSoup(resp.text, "html.parser")
        rows = []

        for item in soup.select("li[data-viewport]")[:25]:
            title_el = item.select_one(".s-card__title")
            price_el = item.select_one(".s-card__price")
            link_el = item.select_one('a[href*="ebay.com/itm"]')

            if not (title_el and price_el and link_el):
                continue

            title = title_el.text.strip()
            if title.lower() == "shop on ebay":
                continue

            price_text = price_el.text.replace("$", "").replace(",", "").strip()
            try:
                price = float(price_text.split(" to ")[0])
            except ValueError:
                continue

            img_el = item.select_one("img")
            image_url = img_el.get("src", "") if img_el else ""
            # eBay uses a static placeholder in SSR; discard it
            if "ebaystatic.com" in image_url:
                image_url = ""
            rows.append(self._make_row(title, price, link_el["href"], image_url))

        return pd.DataFrame(rows) if rows else self._empty()
