"""Mock protected tools. Identity comes from trusted server-side user objects."""

ORDERS = {
    101: [{"order_id": "O-101-A", "items": ["P101"]}],
    102: [{"order_id": "O-102-A", "items": ["P102"]}],
}
INVENTORY = {
    1: [{"product_id": "P101", "quantity": 40}],
    2: [{"product_id": "P102", "quantity": 25}],
}


def _validate_positive_id(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")


def _require_user(user: object) -> None:
    # Actual callers pass objects from the trusted authentication context.
    from users import AuthenticatedUser

    if not isinstance(user, AuthenticatedUser):
        raise PermissionError("A trusted authenticated user is required")


def get_order_history(authenticated_user, customer_id: int) -> list[dict]:
    """Return order history only when caller owns the requested customer ID.

    `authenticated_user` is supplied by trusted application context, never by
    generated tool arguments. `customer_id` is untrusted tool input.
    """
    _require_user(authenticated_user)
    _validate_positive_id(customer_id, "customer_id")
    if authenticated_user.customer_id != customer_id:
        raise PermissionError("Customers may access only their own order history")
    return [order.copy() for order in ORDERS.get(customer_id, [])]


def get_store_inventory(authenticated_user, store_id: int) -> list[dict]:
    """Return inventory only for the store assigned to this manager."""
    _require_user(authenticated_user)
    _validate_positive_id(store_id, "store_id")
    if authenticated_user.role != "store_manager" or authenticated_user.assigned_store_id != store_id:
        raise PermissionError("Store managers may access only their assigned store inventory")
    return [item.copy() for item in INVENTORY.get(store_id, [])]


def admin_view_orders(authenticated_user, customer_id: int) -> list[dict]:
    """Return a customer's orders only with the explicit orders:read_all grant."""
    _require_user(authenticated_user)
    _validate_positive_id(customer_id, "customer_id")
    if "orders:read_all" not in authenticated_user.permissions:
        raise PermissionError("Missing required permission: orders:read_all")
    return [order.copy() for order in ORDERS.get(customer_id, [])]
