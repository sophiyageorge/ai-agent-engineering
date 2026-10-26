"""
Pydantic v2 Schema Validation Lab
==================================================

Learning goals:
- Basic Pydantic models and contracts
- Required, optional, nullable fields and defaults
- Field types, constraints, Literal, Enum and unions
- Field and model validators
- Nested models and collection validation
- Strict mode, extra fields, frozen models, default factories
- ValidationError inspection
- Serialization and JSON Schema
- TypeAdapter and discriminated unions
- Partial-update semantics
- shopping safety boundaries


Install:
    python -m pip install "pydantic>=2,<3"

Run:
    python smartbasket_pydantic_lab.py
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    StringConstraints,
    TypeAdapter,
    ValidationError,
    field_validator,
    model_validator,
)


# ---------------------------------------------------------------------------
# 1. REUSABLE TYPES
# ---------------------------------------------------------------------------

# Product identifiers such as PRD-1234
ProductID = Annotated[
    str,
    StringConstraints(pattern=r"^PRD-[0-9]{4}$", strip_whitespace=True),
]

# Shopper identifiers such as USR-1234
UserID = Annotated[
    str,
    StringConstraints(pattern=r"^USR-[0-9]{4}$", strip_whitespace=True),
]

# Positive quantities; integer values only
Quantity = Annotated[int, Field(ge=1, le=100)]

# AED amounts: use Decimal rather than float for money.
# This constrains the numeric range. Currency rounding/precision policy should
# also be explicitly implemented by the application.
Money = Annotated[Decimal, Field(ge=Decimal("0"), le=Decimal("100000"))]

# Percentages between 0 and 100
Percentage = Annotated[float, Field(ge=0, le=100)]


class DietaryPreference(str, Enum):
    NONE = "none"
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    GLUTEN_FREE = "gluten_free"
    DAIRY_FREE = "dairy_free"


class PurchaseStatus(str, Enum):
    DRAFT = "draft"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    CANCELLED = "cancelled"


# ---------------------------------------------------------------------------
# 2. BASIC CONTRACTS: REQUIRED, OPTIONAL, NULLABLE, DEFAULTS
# ---------------------------------------------------------------------------

class ShopperProfile(BaseModel):
    """A shopper's profile and preferences."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    user_id: UserID
    name: str = Field(min_length=2, max_length=80)

    # Required, but may explicitly be None.
    # To make it optional too, add "= None".
    nickname: str | None

    # Optional because it has a default.
    dietary_preference: DietaryPreference = DietaryPreference.NONE

    # A new list is created for each instance.
    favorite_categories: list[str] = Field(default_factory=list)

    # Optional field; when supplied, validate email syntax.
    # Requires: pip install "pydantic[email]"
    # To keep the core lab runnable without that extra, see ContactExample
    # below, which demonstrates EmailStr only when the optional package exists.


# ---------------------------------------------------------------------------
# 3. FIELD CONSTRAINTS, PATTERNS, LITERAL, COLLECTIONS
# ---------------------------------------------------------------------------

class ProductSearchInput(BaseModel):
    """Arguments for discovering grocery products."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    query: str = Field(min_length=2, max_length=100)
    category: Literal[
        "fruit",
        "vegetables",
        "dairy",
        "bakery",
        "pantry",
        "frozen",
        "household",
        "other",
    ] | None = None

    max_results: int = Field(default=10, ge=1, le=50)
    preferred_brands: list[str] = Field(default_factory=list, max_length=10)


class Product(BaseModel):
    """A product record returned by a mock product catalogue."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    product_id: ProductID
    name: str = Field(min_length=2, max_length=120)
    category: str = Field(min_length=2, max_length=40)
    price_aed: Money
    unit: str = Field(min_length=1, max_length=30)
    in_stock: bool = True
    dietary_tags: list[DietaryPreference] = Field(default_factory=list)
    rating: Percentage | None = None


class BasketItem(BaseModel):
    """A selected product and requested quantity."""

    model_config = ConfigDict(extra="forbid")

    product_id: ProductID
    quantity: Quantity


class BudgetBasketRequest(BaseModel):
    """A request to build a basket within a budget."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    user_id: UserID
    budget_aed: Decimal = Field(gt=Decimal("0"), le=Decimal("5000"))
    items: list[BasketItem] = Field(min_length=1, max_length=50)
    delivery_fee_aed: Decimal = Field(
        default=Decimal("0.00"),
        ge=Decimal("0"),
        le=Decimal("100"),
    )
    dietary_preference: DietaryPreference = DietaryPreference.NONE

    @model_validator(mode="after")
    def reject_duplicate_product_ids(self):
        """Avoid accidental duplicate lines; quantities should be combined."""
        ids = [item.product_id for item in self.items]
        if len(ids) != len(set(ids)):
            raise ValueError(
                "Duplicate product IDs are not allowed; combine quantities."
            )
        return self


# ---------------------------------------------------------------------------
# 4. FIELD VALIDATOR: NORMALIZE AND VALIDATE USER INPUT
# ---------------------------------------------------------------------------

class CouponInput(BaseModel):
    """Coupon code supplied by a shopper."""

    code: str = Field(min_length=4, max_length=20)

    @field_validator("code")
    @classmethod
    def normalize_coupon(cls, value: str) -> str:
        value = value.strip().upper()
        if not value.isalnum():
            raise ValueError("Coupon must contain only letters and numbers.")
        return value


# ---------------------------------------------------------------------------
# 5. MODEL VALIDATOR: RULES ACROSS MULTIPLE FIELDS
# ---------------------------------------------------------------------------

class DeliveryWindow(BaseModel):
    """A requested delivery time window."""

    start: datetime
    end: datetime

    @model_validator(mode="after")
    def validate_window(self):
        # Comparing naive and aware datetimes raises TypeError, so explicitly
        # require timezone-aware values for this demo.
        if self.start.tzinfo is None or self.end.tzinfo is None:
            raise ValueError("Delivery times must include a timezone.")
        if self.end <= self.start:
            raise ValueError("Delivery end must be after delivery start.")
        return self


class BudgetSummary(BaseModel):
    """A validated budget breakdown."""

    budget_aed: Decimal = Field(gt=Decimal("0"))
    subtotal_aed: Decimal = Field(ge=Decimal("0"))
    delivery_fee_aed: Decimal = Field(ge=Decimal("0"))
    total_aed: Decimal = Field(ge=Decimal("0"))
    remaining_aed: Decimal
    within_budget: bool

    @model_validator(mode="after")
    def check_totals(self):
        expected_total = self.subtotal_aed + self.delivery_fee_aed
        if self.total_aed != expected_total:
            raise ValueError("Total must equal subtotal plus delivery fee.")

        expected_remaining = self.budget_aed - self.total_aed
        if self.remaining_aed != expected_remaining:
            raise ValueError("Remaining amount does not match the budget math.")

        if self.within_budget != (self.total_aed <= self.budget_aed):
            raise ValueError("within_budget does not match the calculated total.")

        return self


# ---------------------------------------------------------------------------
# 6. NESTED MODELS: A COMPLETE PROPOSED BASKET
# ---------------------------------------------------------------------------

class BasketLine(BaseModel):
    """A basket line with product snapshot and quantity."""

    model_config = ConfigDict(extra="forbid")

    product: Product
    quantity: Quantity
    line_total_aed: Decimal = Field(ge=Decimal("0"))

    @model_validator(mode="after")
    def check_line_total(self):
        expected = self.product.price_aed * self.quantity
        if self.line_total_aed != expected:
            raise ValueError("Line total must equal product price × quantity.")
        return self


class ProposedBasket(BaseModel):
    """A complete, proposed basket—not an executed purchase."""

    model_config = ConfigDict(extra="forbid")

    user_id: UserID
    lines: list[BasketLine] = Field(min_length=1, max_length=50)
    budget: BudgetSummary
    status: PurchaseStatus = PurchaseStatus.AWAITING_APPROVAL
    notes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_basket_matches_summary(self):
        subtotal = sum(
            (line.line_total_aed for line in self.lines),
            start=Decimal("0"),
        )
        if subtotal != self.budget.subtotal_aed:
            raise ValueError("Basket lines do not match the subtotal.")
        return self


# ---------------------------------------------------------------------------
# 7. STRICT MODE, EXTRA FIELDS, FROZEN MODELS
# ---------------------------------------------------------------------------

class StrictQuantityInput(BaseModel):
    """Reject values such as the string '2' for an integer quantity."""

    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)

    quantity: int = Field(ge=1, le=100)


# frozen=True blocks normal attribute reassignment. It is not deep
# immutability and does not replace security controls.


# ---------------------------------------------------------------------------
# 8. DISCRIMINATED UNIONS: DIFFERENT TOOL ARGUMENT SHAPES
# ---------------------------------------------------------------------------

class SearchAction(BaseModel):
    action: Literal["search_products"]
    query: str = Field(min_length=2, max_length=100)
    max_results: int = Field(default=10, ge=1, le=50)


class OptimizeBasketAction(BaseModel):
    action: Literal["optimize_basket"]
    user_id: UserID
    budget_aed: Decimal = Field(gt=Decimal("0"), le=Decimal("5000"))
    product_ids: list[ProductID] = Field(min_length=1, max_length=50)


class SuggestAlternativesAction(BaseModel):
    action: Literal["suggest_alternatives"]
    product_id: ProductID
    max_price_aed: Decimal = Field(gt=Decimal("0"))
    dietary_preference: DietaryPreference = DietaryPreference.NONE


SmartBasketAction = Annotated[
    SearchAction | OptimizeBasketAction | SuggestAlternativesAction,
    Field(discriminator="action"),
]

smartbasket_action_adapter = TypeAdapter(SmartBasketAction)


# ---------------------------------------------------------------------------
# 9. PARTIAL UPDATES: UNSET VS EXPLICIT NULL
# ---------------------------------------------------------------------------

class ShopperPreferencesUpdate(BaseModel):
    """Fields omitted from a patch should remain unchanged."""

    model_config = ConfigDict(extra="forbid")

    nickname: str | None = None
    dietary_preference: DietaryPreference | None = None
    favorite_categories: list[str] | None = None


# ---------------------------------------------------------------------------
# 10. OUTPUT MODEL AND SERIALIZATION
# ---------------------------------------------------------------------------

class AlternativeSuggestion(BaseModel):
    """A proposed lower-cost alternative; it does not change the basket."""

    original_product_id: ProductID
    alternative_product_id: ProductID
    original_price_aed: Money
    alternative_price_aed: Money
    estimated_savings_aed: Decimal = Field(ge=Decimal("0"))
    reason: str = Field(min_length=3, max_length=250)

    @model_validator(mode="after")
    def check_savings(self):
        expected = self.original_price_aed - self.alternative_price_aed
        if expected < 0:
            raise ValueError("Alternative must not cost more than the original.")
        if self.estimated_savings_aed != expected:
            raise ValueError("Savings must equal original price minus alternative.")
        return self


# ---------------------------------------------------------------------------
# 11. MOCK PRODUCT CATALOGUE AND SAFE BUDGET CALCULATION
# ---------------------------------------------------------------------------

MOCK_PRODUCTS: dict[str, Product] = {
    "PRD-1001": Product(
        product_id="PRD-1001",
        name="Bananas",
        category="fruit",
        price_aed=Decimal("6.50"),
        unit="1 kg",
        in_stock=True,
        dietary_tags=[DietaryPreference.VEGETARIAN, DietaryPreference.VEGAN],
        rating=92,
    ),
    "PRD-1002": Product(
        product_id="PRD-1002",
        name="Rolled Oats",
        category="pantry",
        price_aed=Decimal("12.00"),
        unit="500 g",
        in_stock=True,
        dietary_tags=[DietaryPreference.VEGETARIAN, DietaryPreference.VEGAN],
        rating=88,
    ),
    "PRD-1003": Product(
        product_id="PRD-1003",
        name="Milk",
        category="dairy",
        price_aed=Decimal("8.00"),
        unit="1 L",
        in_stock=True,
        dietary_tags=[DietaryPreference.VEGETARIAN],
        rating=90,
    ),
    "PRD-1004": Product(
        product_id="PRD-1004",
        name="Plant-Based Drink",
        category="dairy-alternative",
        price_aed=Decimal("7.00"),
        unit="1 L",
        in_stock=True,
        dietary_tags=[DietaryPreference.VEGETARIAN, DietaryPreference.VEGAN,
                      DietaryPreference.DAIRY_FREE],
        rating=85,
    ),
    "PRD-1005": Product(
        product_id="PRD-1005",
        name="Rice",
        category="pantry",
        price_aed=Decimal("10.00"),
        unit="2 kg",
        in_stock=True,
        dietary_tags=[DietaryPreference.VEGETARIAN, DietaryPreference.VEGAN,
                      DietaryPreference.GLUTEN_FREE],
        rating=91,
    ),
}


def calculate_basket_summary(
    request: BudgetBasketRequest,
    catalogue: dict[str, Product],
) -> BudgetSummary:
    """Calculate a budget summary from mock catalogue data.

    This validates the request and checks catalogue existence, stock and
    dietary compatibility. A production service must re-check authoritative
    live prices and availability immediately before checkout.
    """
    subtotal = Decimal("0.00")

    for item in request.items:
        product = catalogue.get(item.product_id)
        if product is None:
            raise ValueError(f"Unknown product ID: {item.product_id}")

        if not product.in_stock:
            raise ValueError(f"Product is out of stock: {product.name}")

        if (
            request.dietary_preference != DietaryPreference.NONE
            and request.dietary_preference not in product.dietary_tags
        ):
            raise ValueError(
                f"{product.name} does not match "
                f"{request.dietary_preference.value} preference."
            )

        subtotal += product.price_aed * item.quantity

    total = subtotal + request.delivery_fee_aed

    # Use explicit money quantization in a real pricing service, with a
    # documented currency precision and rounding policy.
    subtotal = subtotal.quantize(Decimal("0.01"))
    total = total.quantize(Decimal("0.01"))
    remaining = (request.budget_aed - total).quantize(Decimal("0.01"))

    return BudgetSummary(
        budget_aed=request.budget_aed,
        subtotal_aed=subtotal,
        delivery_fee_aed=request.delivery_fee_aed,
        total_aed=total,
        remaining_aed=remaining,
        within_budget=(total <= request.budget_aed),
    )


# ---------------------------------------------------------------------------
# 12. VALIDATION ERROR DETAILS
# ---------------------------------------------------------------------------

def show_validation_error(label: str, func) -> None:
    """Run a test and display structured Pydantic errors."""
    print(f"\n--- {label} ---")
    try:
        result = func()
        print("VALID:", result)
    except ValidationError as error:
        print("REJECTED:")
        for issue in error.errors():
            print(
                f"  location={issue['loc']}, "
                f"type={issue['type']}, "
                f"message={issue['msg']}"
            )


# ---------------------------------------------------------------------------
# 13. RUN ALL EXAMPLES
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 72)
    print("SMARTBASKET AI — PYDANTIC V2 VALIDATION LAB")
    print("Mock data only: no Careem MCP calls and no purchases.")
    print("=" * 72)

    # Basic model with required and default fields
    print("\n[1] Shopper profile")
    shopper = ShopperProfile(
        user_id="USR-1234",
        name="Sophiya",
        nickname=None,  # required but nullable
        dietary_preference=DietaryPreference.VEGETARIAN,
        favorite_categories=["fruit", "pantry"],
    )
    print(shopper.model_dump())

    # Valid product search and invalid search arguments
    print("\n[2] Product search contract")
    search = ProductSearchInput(query="oats", category="pantry")
    print(search.model_dump())

    show_validation_error(
        "Search query too short",
        lambda: ProductSearchInput(query="x"),
    )

    show_validation_error(
        "Unsupported category",
        lambda: ProductSearchInput(query="milk", category="electronics"),
    )

    # Pattern, quantity and extra-field constraints
    print("\n[3] Basket item contract")
    print(BasketItem(product_id="PRD-1001", quantity=2))

    show_validation_error(
        "Invalid product ID",
        lambda: BasketItem(product_id="BANANA", quantity=2),
    )
    show_validation_error(
        "Quantity below minimum",
        lambda: BasketItem(product_id="PRD-1001", quantity=0),
    )
    show_validation_error(
        "Unexpected argument",
        lambda: StudentLikeUnexpectedField(),
    )

    # Coupon field validator
    print("\n[4] Field validator: coupon normalization")
    print(CouponInput(code="  save20  "))

    show_validation_error(
        "Invalid coupon characters",
        lambda: CouponInput(code="SAVE-20"),
    )

    # Cross-field validation
    print("\n[5] Model validator: delivery window")
    window = DeliveryWindow(
        start="2026-10-27T10:00:00+04:00",
        end="2026-10-27T12:00:00+04:00",
    )
    print(window)

    show_validation_error(
        "Delivery end before start",
        lambda: DeliveryWindow(
            start="2026-10-27T12:00:00+04:00",
            end="2026-10-27T10:00:00+04:00",
        ),
    )

    # Budget calculation with catalogue and mock prices
    print("\n[6] Budget calculation")
    request = BudgetBasketRequest(
        user_id="USR-1234",
        budget_aed=Decimal("35.00"),
        items=[
            BasketItem(product_id="PRD-1001", quantity=1),
            BasketItem(product_id="PRD-1002", quantity=1),
            BasketItem(product_id="PRD-1005", quantity=1),
        ],
        delivery_fee_aed=Decimal("3.00"),
        dietary_preference=DietaryPreference.VEGAN,
    )
    summary = calculate_basket_summary(request, MOCK_PRODUCTS)
    print(summary.model_dump(mode="json"))

    show_validation_error(
        "Duplicate product IDs",
        lambda: BudgetBasketRequest(
            user_id="USR-1234",
            budget_aed=Decimal("50"),
            items=[
                BasketItem(product_id="PRD-1001", quantity=1),
                BasketItem(product_id="PRD-1001", quantity=2),
            ],
        ),
    )

    # Nested basket and output checks
    print("\n[7] Nested basket response model")
    line1 = BasketLine(
        product=MOCK_PRODUCTS["PRD-1001"],
        quantity=1,
        line_total_aed=Decimal("6.50"),
    )
    line2 = BasketLine(
        product=MOCK_PRODUCTS["PRD-1002"],
        quantity=1,
        line_total_aed=Decimal("12.00"),
    )
    nested_summary = BudgetSummary(
        budget_aed=Decimal("25.00"),
        subtotal_aed=Decimal("18.50"),
        delivery_fee_aed=Decimal("0.00"),
        total_aed=Decimal("18.50"),
        remaining_aed=Decimal("6.50"),
        within_budget=True,
    )
    basket = ProposedBasket(
        user_id="USR-1234",
        lines=[line1, line2],
        budget=nested_summary,
        status=PurchaseStatus.AWAITING_APPROVAL,
        notes=["Mock prices; confirm live availability before checkout."],
    )
    print(json.dumps(basket.model_dump(mode="json"), indent=2))

    show_validation_error(
        "Incorrect line total",
        lambda: BasketLine(
            product=MOCK_PRODUCTS["PRD-1001"],
            quantity=2,
            line_total_aed=Decimal("6.50"),
        ),
    )

    # Strict mode and frozen assignment
    print("\n[8] Strict mode")
    print(StrictQuantityInput(quantity=2))
    show_validation_error(
        "Strict mode rejects a string quantity",
        lambda: StrictQuantityInput(quantity="2"),
    )

    # Discriminated union
    print("\n[9] Discriminated union for agent actions")
    action = smartbasket_action_adapter.validate_python({
        "action": "search_products",
        "query": "oats",
        "max_results": 5,
    })
    print(type(action).__name__, action.model_dump())

    show_validation_error(
        "Unknown action type",
        lambda: smartbasket_action_adapter.validate_python({
            "action": "buy_everything",
            "query": "oats",
        }),
    )

    # Partial update behavior
    print("\n[10] Partial update: unset vs explicit null")
    update = ShopperPreferencesUpdate(nickname=None)
    print("Fields explicitly set:", update.model_fields_set)
    print("Only explicitly supplied fields:", update.model_dump(exclude_unset=True))

    # Alternative savings validation
    print("\n[11] Alternative suggestion output")
    alternative = AlternativeSuggestion(
        original_product_id="PRD-1003",
        alternative_product_id="PRD-1004",
        original_price_aed=Decimal("8.00"),
        alternative_price_aed=Decimal("7.00"),
        estimated_savings_aed=Decimal("1.00"),
        reason="A lower-cost plant-based option; verify suitability and stock.",
    )
    print(alternative.model_dump(mode="json"))

    show_validation_error(
        "Incorrect claimed savings",
        lambda: AlternativeSuggestion(
            original_product_id="PRD-1003",
            alternative_product_id="PRD-1004",
            original_price_aed=Decimal("8.00"),
            alternative_price_aed=Decimal("7.00"),
            estimated_savings_aed=Decimal("5.00"),
            reason="Test invalid savings calculation",
        ),
    )

    # JSON schema and serialization
    print("\n[12] JSON Schema for a tool")
    print(json.dumps(ProductSearchInput.model_json_schema(), indent=2))

    print("\n[13] JSON parsing and serialization")
    raw_json = '{"query":"apples","category":"fruit","max_results":5}'
    parsed = ProductSearchInput.model_validate_json(raw_json)
    print("Parsed model:", parsed)
    print("Python dictionary:", parsed.model_dump())
    print("JSON string:", parsed.model_dump_json())

    # TypeAdapter for a list of products
    print("\n[14] TypeAdapter for a list of products")
    product_list_adapter = TypeAdapter(list[Product])
    validated_products = product_list_adapter.validate_python(
        [MOCK_PRODUCTS["PRD-1001"].model_dump(),
         MOCK_PRODUCTS["PRD-1002"].model_dump()]
    )
    print("Validated product count:", len(validated_products))

    # EmailStr is an optional extra and is demonstrated without breaking
    # the main lab when pydantic[email] is not installed.
    print("\n[15] Optional EmailStr example")
    try:
        from pydantic import EmailStr  # noqa: F401

        class ContactExample(BaseModel):
            email: EmailStr

        print(ContactExample(email="shopper@example.com"))
    except ImportError:
        print(
            'Optional dependency missing. Install with: '
            'python -m pip install "pydantic[email]"'
        )

    print("\n" + "=" * 72)
    print("LAB COMPLETE")
    print("Remember: schema validation is not authorization or purchase approval.")
    print("This script never places an order.")
    print("=" * 72)


# Helper used to demonstrate rejection of extra fields.
def StudentLikeUnexpectedField():
    # The deliberately unexpected field is rejected because extra="forbid".
    return ProductSearchInput(query="milk", admin=True)


if __name__ == "__main__":
    main()
