from dataclasses import dataclass
from typing import List


@dataclass
class Product:
    brand: str
    name: str
    keywords: List[str]
    asp_max: float           # ASP ceiling in the product's native currency
    category: str = "Women's Jeans"
    material: str = ""
    style: str = ""
    condition: str = "All"
    region: str = "US"       # "US" or "UK"
    currency: str = "USD"    # "USD" or "GBP"


US_SOURCES = ["eBay US", "Vinted US", "Poshmark US"]
UK_SOURCES = ["eBay UK", "Vinted UK"]


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
    Product(
        brand="Coach",
        name="Leather Pillow Tabby",
        keywords=["Pillow Tabby", "Coach Tabby Shoulder Bag"],
        asp_max=300.0,
        category="Women's Handbags",
        material="Leather",
    ),
    Product(
        brand="Calvin Klein",
        name="Sheath Dress",
        keywords=["Knee Length Office dress"],
        asp_max=50.0,
        category="Women's Dresses",
        material="Polyester",
        style="Sheath",
    ),
    Product(
        brand="Zara",
        name="Zara Dress",
        keywords=["Zara midi maxi dress", "Zara midi dress viscose"],
        asp_max=50.0,
        category="Women's Dresses",
        material="Viscose",
        style="Midi Maxi",
        condition="Used",
        region="UK",
        currency="GBP",
    ),
    Product(
        brand="M&S",
        name="Women's Puffer Jacket",
        keywords=["M&S puffer jacket women", "Marks Spencer puffa jacket ladies"],
        asp_max=50.0,
        category="Women's Jackets",
        material="Polyester",
        style="Quilted",
        condition="Used",
        region="UK",
        currency="GBP",
    ),
]
