import pytest

from protected_tools import admin_view_orders, get_order_history, get_store_inventory
from users import ALICE, BOB, STORE_MANAGER, ADMINISTRATOR, ADMIN_WITHOUT_ORDER_PERMISSION


def test_customer_reads_own_orders():
    assert get_order_history(ALICE, 101)[0]["order_id"] == "O-101-A"


def test_alice_cannot_read_bobs_orders_even_if_tool_argument_names_bob():
    # customer_id is LLM/tool input; authenticated caller remains trusted Alice.
    with pytest.raises(PermissionError):
        get_order_history(ALICE, 102)


def test_manager_reads_assigned_store():
    assert get_store_inventory(STORE_MANAGER, 1)[0]["product_id"] == "P101"


def test_manager_cannot_read_other_store():
    with pytest.raises(PermissionError):
        get_store_inventory(STORE_MANAGER, 2)


def test_explicit_admin_permission_allows_view():
    assert admin_view_orders(ADMINISTRATOR, 102)[0]["order_id"] == "O-102-A"


def test_admin_role_without_permission_is_denied():
    with pytest.raises(PermissionError):
        admin_view_orders(ADMIN_WITHOUT_ORDER_PERMISSION, 101)


@pytest.mark.parametrize("call", [lambda: get_order_history(ALICE, 0), lambda: get_store_inventory(STORE_MANAGER, -1), lambda: admin_view_orders(ADMINISTRATOR, True)])
def test_bad_ids_are_rejected(call):
    with pytest.raises(ValueError):
        call()


def test_untrusted_identity_string_cannot_impersonate_user():
    with pytest.raises(PermissionError):
        get_order_history("bob", 102)
