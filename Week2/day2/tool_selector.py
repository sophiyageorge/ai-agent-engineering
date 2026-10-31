"""Small deterministic selector: phrases are hints, not an LLM."""

import re
from typing import NamedTuple


class Selection(NamedTuple):
    tool_name: str | None
    arguments: dict
    reason: str


def select_tool(request: str) -> Selection:
    """Choose one supported tool, or return no selection when unclear."""
    if not isinstance(request, str) or not request.strip():
        return Selection(None, {}, "Request is empty or not text.")
    text = request.strip()

    if re.search(r"\b(total|calculate|basket|cost of)\b", text, re.I):
        found = re.findall(r"\b(\d+)\s+(?:units?\s+of\s+)?(P\d{3})\b", text, re.I)
        if not found:
            return Selection(None, {}, "A total request needs product IDs and quantities.")
        return Selection("calculate_basket_total", {"items": [{"quantity": int(qty), "product_id": pid.upper()} for qty, pid in found]}, "The request asks for a basket total and includes quantities.")

    product_id = re.search(r"\bP\d{3}\b", text, re.I)
    if product_id and re.search(r"\b(details?|information|describe)\b", text, re.I):
        return Selection("get_product_details", {"product_id": product_id.group(0).upper()}, "The request asks for details about a specific product ID.")

    price_match = re.search(r"\b(?:under|below|less than)\s+(\d+(?:\.\d+)?)\b", text, re.I)
    if re.search(r"\b(find|search|look for)\b", text, re.I):
        query = re.sub(r"\b(find|search|look for|under|below|less than)\b|\d+(?:\.\d+)?", " ", text, flags=re.I)
        query = re.sub(r"\s+", " ", query).strip(" .")
        if not query:
            return Selection(None, {}, "A product search needs a product query.")
        return Selection("search_products", {"query": query, "max_price": float(price_match.group(1)) if price_match else None}, "The request asks to find products.")

    return Selection(None, {}, "No supported tool clearly matches this request; ask a clarifying question or explain the unsupported action.")
