"""Trusted, server-created identities for the authorization exercise."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: str
    display_name: str
    role: str
    customer_id: int | None = None
    assigned_store_id: int | None = None
    permissions: frozenset[str] = field(default_factory=frozenset)


# These objects represent identity established by the trusted application layer.
ALICE = AuthenticatedUser("alice", "Alice", "customer", customer_id=101)
BOB = AuthenticatedUser("bob", "Bob", "customer", customer_id=102)
STORE_MANAGER = AuthenticatedUser("manager-1", "Store manager", "store_manager", assigned_store_id=1)
ADMINISTRATOR = AuthenticatedUser("admin", "Administrator", "administrator", permissions=frozenset({"orders:read_all"}))
# Useful for demonstrating that the role label alone grants nothing.
ADMIN_WITHOUT_ORDER_PERMISSION = AuthenticatedUser("admin-limited", "Limited administrator", "administrator")


MOCK_USERS = {user.user_id: user for user in (ALICE, BOB, STORE_MANAGER, ADMINISTRATOR, ADMIN_WITHOUT_ORDER_PERMISSION)}
