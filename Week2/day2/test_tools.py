import pytest

from tools import calculate_basket_total, get_product_details, search_products
from tool_selector import select_tool


def test_search_and_price_filter():
    assert [p["product_id"] for p in search_products("rice", 20)] == ["P101"]
    assert search_products("rice", 10) == []


def test_details_known_product():
    assert get_product_details("P101")["name"] == "Rice"


def test_basket_total():
    result = calculate_basket_total([{"product_id": "P101", "quantity": 2}, {"product_id": "P102", "quantity": 1}])
    assert result["total"] == 49.0


@pytest.mark.parametrize("call", [lambda: search_products(" "), lambda: search_products("rice", -1), lambda: get_product_details("missing"), lambda: calculate_basket_total([]), lambda: calculate_basket_total([{"product_id": "P101", "quantity": True}])])
def test_invalid_arguments_rejected(call):
    with pytest.raises(ValueError):
        call()


def test_selector_examples():
    assert select_tool("Find rice under 20.").tool_name == "search_products"
    assert select_tool("Show details for product P101.").arguments == {"product_id": "P101"}
    selection = select_tool("Calculate the total for 2 units of P101 and 1 unit of P102.")
    assert selection.tool_name == "calculate_basket_total"
    assert selection.arguments["items"] == [{"quantity": 2, "product_id": "P101"}, {"quantity": 1, "product_id": "P102"}]


@pytest.mark.parametrize("user_text", ["Do something helpful", "Deliver this order", "Find under 20"])
def test_unclear_or_unsupported_requests_do_not_select(user_text):
    assert select_tool(user_text).tool_name is None
