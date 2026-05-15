from dataclasses import dataclass
from typing import List


@dataclass
class Product:
    brand: str
    name: str
    keywords: List[str]
    asp_max: float       # Average Selling Price ceiling in USD
    category: str = "Women's Jeans"


PRODUCTS: List[Product] = [
    Product(
        brand="Zara",
        name="Crop Top",
        keywords=["Black cropped long sleeve top"],
        asp_max=50.0,
        category="Women's Tops",
    ),
    Product(
        brand="Levi's",
        name="501 Original",
        keywords=["Levi's 501 Series Women's Straight Jeans Slim High Rise"],
        asp_max=50.0,
    ),
]
