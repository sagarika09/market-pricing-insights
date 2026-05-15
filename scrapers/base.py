from abc import ABC, abstractmethod
import pandas as pd
from datetime import datetime
from config import SCHEMA_COLUMNS


class BaseScraper(ABC):
    name: str = ""

    @abstractmethod
    def search(self, query: str, condition: str = "All", category: str = "Women's Jeans", brand: str = "") -> pd.DataFrame:
        """Return a DataFrame with columns matching SCHEMA_COLUMNS."""

    def _empty(self) -> pd.DataFrame:
        return pd.DataFrame(columns=SCHEMA_COLUMNS)

    def _make_row(self, title: str, price: float, url: str, image_url: str = "") -> dict:
        return {
            "source": self.name,
            "title": title,
            "price": price,
            "url": url,
            "image_url": image_url,
            "scraped_at": datetime.utcnow().isoformat(),
        }
