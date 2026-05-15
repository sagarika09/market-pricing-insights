import base64
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup
from config import (
    EBAY_APP_ID, EBAY_CLIENT_SECRET,
    EBAY_BROWSE_API_URL, EBAY_TOKEN_URL, EBAY_SCOPE,
    HEADERS,
)
from .base import BaseScraper

# Module-level token cache: (access_token, expiry_timestamp)
_token_cache: tuple[str, float] = ("", 0.0)


def _get_access_token() -> str:
    global _token_cache
    token, expiry = _token_cache
    if token and time.time() < expiry - 60:
        return token

    credentials = base64.b64encode(f"{EBAY_APP_ID}:{EBAY_CLIENT_SECRET}".encode()).decode()
    resp = requests.post(
        EBAY_TOKEN_URL,
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={"grant_type": "client_credentials", "scope": EBAY_SCOPE},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    token = data["access_token"]
    expiry = time.time() + data.get("expires_in", 7200)
    _token_cache = (token, expiry)
    return token


class EbayScraper(BaseScraper):
    name = "eBay"

    _CONDITION_MAP = {"Used": "3000", "New": "1000"}
    _CATEGORY_MAP = {"Women's Jeans": "11554", "Women's Tops": "53159", "Women's Handbags": "169291", "Women's Dresses": "63861"}

    def search(self, query: str, condition: str = "All", category: str = "Women's Jeans", brand: str = "", material: str = "", style: str = "") -> pd.DataFrame:
        if brand and brand.lower() not in query.lower():
            query = f"{brand} {query}"
        if material and material.lower() not in query.lower():
            query = f"{query} {material}"
        if style and style.lower() not in query.lower():
            query = f"{query} {style}"
        if EBAY_APP_ID and EBAY_CLIENT_SECRET:
            return self._search_api(query, condition, category)
        return self._search_scrape(query, condition, category)

    def _search_api(self, query: str, condition: str, category: str) -> pd.DataFrame:
        try:
            token = _get_access_token()
        except Exception:
            return self._search_scrape(query, condition, category)

        cat_id = self._CATEGORY_MAP.get(category, "11554")
        params = {"q": query, "limit": 20, "category_ids": cat_id}
        if condition in self._CONDITION_MAP:
            params["filter"] = f"conditionIds:{{{self._CONDITION_MAP[condition]}}}"

        try:
            resp = requests.get(
                EBAY_BROWSE_API_URL,
                headers={
                    "Authorization": f"Bearer {token}",
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
            image_url = item.get("image", {}).get("imageUrl", "")
            rows.append(self._make_row(item.get("title", ""), price, item.get("itemWebUrl", ""), image_url))

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
            if "ebaystatic.com" in image_url:
                image_url = ""
            rows.append(self._make_row(title, price, link_el["href"], image_url))

        return pd.DataFrame(rows) if rows else self._empty()
