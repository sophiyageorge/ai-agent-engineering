"""Standalone mock shopping tools with explicit contracts and validation."""

from typing import Any

PRODUCTS = {
    "P101": {"product_id": "P101", "name": "Rice", "price": 18.50, "description": "1 kg bag of rice"},
    "P102": {"product_id": "P102", "name": "Lentils", "price": 12.00, "description": "1 kg bag of lentils"},
    "P103": {"product_id": "P103", "name": "Olive oil", "price": 24.00, "description": "500 ml bottle"},
}

TOOL_DESCRIPTIONS = {
    "search_products": "Find products by a name/query and optionally a maximum price. Use for product discovery or budget filtering; do not use to retrieve a specific item's full details or calculate a basket. Arguments: query (non-empty string), max_price (optional non-negative number). Returns matching product dictionaries.",
    "get_product_details": "Retrieve the full mock record for one known product. Use when the user asks about a specific product ID; do not use for searching, price filtering, or basket totals. Argument: product_id (known ID such as P101). Returns a product dictionary.",
    "calculate_basket_total": "Calculate a basket subtotal from product IDs and positive integer quantities. Use for explicit total/subtotal requests; do not use to discover products or fetch details. Argument: items (non-empty list of {product_id, quantity}). Returns itemized amounts and total.",
}


def _validate_price(value: Any) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise ValueError("max_price must be a non-negative number")


def search_products(query: str, max_price: float | None = None) -> list[dict]:
    """Find matching mock products, optionally capped by price."""
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a non-empty string")
    if max_price is not None:
        _validate_price(max_price)
    matches = []
    for product in PRODUCTS.values():
        if query.strip().casefold() in product["name"].casefold() and (max_price is None or product["price"] <= max_price):
            matches.append(product.copy())
    return matches


def get_product_details(product_id: str) -> dict:
    """Return one known product record."""
    if not isinstance(product_id, str) or not product_id.strip():
        raise ValueError("product_id must be a non-empty string")
    product = PRODUCTS.get(product_id.strip().upper())
    if product is None:
        raise ValueError(f"unknown product_id: {product_id}")
    return product.copy()


def calculate_basket_total(items: list[dict]) -> dict:
    """Return itemized costs and the basket total."""
    if not isinstance(items, list) or not items:
        raise ValueError("items must be a non-empty list")
    itemized = []
    total = 0.0
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"items[{index}] must be a dictionary")
        product_id, quantity = item.get("product_id"), item.get("quantity")
        if not isinstance(product_id, str) or not product_id.strip():
            raise ValueError(f"items[{index}].product_id must be a non-empty string")
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
            raise ValueError(f"items[{index}].quantity must be a positive integer")
        product = get_product_details(product_id)
        subtotal = round(product["price"] * quantity, 2)
        total += subtotal
        itemized.append({"product_id": product["product_id"], "quantity": quantity, "subtotal": subtotal})
    return {"items": itemized, "total": round(total, 2)}
