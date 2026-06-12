import json
import os
from products import Product, PRODUCTS

STORE_PATH = os.path.join(os.path.dirname(__file__), "..", "products_data.json")

CATEGORIES = [
    "Women's Jeans",
    "Women's Tops",
    "Women's Dresses",
    "Women's Skirts",
    "Women's Handbags",
    "Women's Jackets",
    "Women's Shoes",
    "Women's Accessories",
]


def _to_dict(p: Product) -> dict:
    return {
        "brand": p.brand, "name": p.name, "keywords": p.keywords,
        "asp_max": p.asp_max, "category": p.category, "material": p.material,
        "style": p.style, "condition": p.condition, "region": p.region, "currency": p.currency,
    }


def _from_dict(d: dict) -> Product:
    return Product(**{k: v for k, v in d.items() if k in Product.__dataclass_fields__})


def _init_store():
    if not os.path.exists(STORE_PATH):
        data: dict = {"US": [], "UK": []}
        for p in PRODUCTS:
            data[p.region].append(_to_dict(p))
        _write(data)


def _read() -> dict:
    _init_store()
    with open(STORE_PATH, encoding="utf-8") as f:
        return json.load(f)


def _write(data: dict):
    with open(STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_products(region: str) -> list[Product]:
    return [_from_dict(d) for d in _read().get(region, [])]


def add_product(product: Product):
    data = _read()
    data.setdefault(product.region, []).append(_to_dict(product))
    _write(data)


def update_product(region: str, index: int, product: Product):
    data = _read()
    data[region][index] = _to_dict(product)
    _write(data)


def delete_product(region: str, index: int):
    data = _read()
    data[region].pop(index)
    _write(data)
