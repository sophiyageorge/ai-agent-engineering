# Week 2, Day 3: Authentication and authorization at the tool boundary

Run from this directory with `python -m pytest -q` (or from the repository root with `python -m pytest Week2/day3 -q -p no:cacheprovider`). The exercise uses local in-memory data only.

## Files and security boundaries

- `users.py` defines frozen `AuthenticatedUser` records and mock identities. In a real service, the application would construct/pass this object after authentication; the model never supplies it. Alice and Bob have customer IDs 101 and 102, the manager is assigned store 1, and the administrator has the explicit `orders:read_all` grant. A second administrator fixture demonstrates role-only denial.
- `protected_tools.py` stores mock data and enforces checks inside each tool. Each function takes the trusted user object separately from untrusted IDs. It validates the ID first, checks ownership/assignment/permission, and only then returns protected records. Failed checks raise `PermissionError` before data is returned.
- `test_authorization.py` tests allowed access, denied access, invalid IDs, and rejection of a forged identity string. The Alice/Bob test demonstrates that changing the LLM-supplied `customer_id` does not change the trusted caller identity.

Try `get_order_history(ALICE, 102)` (denied), `get_store_inventory(STORE_MANAGER, 2)` (denied), and `admin_view_orders(ADMIN_WITHOUT_ORDER_PERMISSION, 101)` (denied). The trusted context is an exercise fixture, not real authentication.
