"""
Shared line-item pricing logic for anything that builds a sale: the direct
one-shot checkout (SalesService) and the customer-display draft/session
checkout (CheckoutSessionService). Kept here so variant/unit/discount
handling behaves identically in both flows.
"""
from decimal import Decimal

from app.core.middleware.error_handler import ConflictError, NotFoundError
from app.repositories.product_repository import ProductRepository
from app.repositories.variant_repository import VariantRepository
from app.repositories.unit_repository import UnitRepository


class ResolvedLine:
    def __init__(self, product, variant, unit, quantity, unit_price, tax_rate,
                 discount_amount, line_total, base_stock_deduction, stock_holder):
        self.product = product
        self.variant = variant
        self.unit = unit
        self.quantity = quantity
        self.unit_price = unit_price
        self.tax_rate = tax_rate
        self.discount_amount = discount_amount
        self.line_total = line_total
        self.base_stock_deduction = base_stock_deduction  # how much to deduct from the base stock holder
        self.stock_holder = stock_holder  # "inventory" (Product.inventory) or "variant"


def resolve_sale_line(item_data):
    """
    item_data keys: product_id (required), variant_id (optional), unit_id (optional),
    quantity (required, in the *sold* unit), discount_amount (optional, flat amount off this line),
    discount_type (optional: 'percentage' | 'fixed'), discount_reason (optional).
    """
    product_repo = ProductRepository()
    variant_repo = VariantRepository()
    unit_repo = UnitRepository()

    product = product_repo.get_by_id(item_data["product_id"])
    if not product or not product.is_active:
        raise NotFoundError(f"Product #{item_data['product_id']} not found or inactive.")

    quantity = item_data["quantity"]
    variant = None
    unit = None
    base_price = Decimal(str(product.price))
    tax_rate = Decimal(str(product.tax_rate))
    if product.is_tax_exempt:
        tax_rate = Decimal("0")

    if item_data.get("variant_id"):
        variant = variant_repo.get_by_id(item_data["variant_id"])
        if not variant or variant.product_id != product.id:
            raise NotFoundError("Variant not found for this product.")
        base_price = Decimal(str(variant.price))

    base_stock_deduction = quantity
    if item_data.get("unit_id"):
        unit = unit_repo.get_by_id(item_data["unit_id"])
        if not unit or unit.product_id != product.id:
            raise NotFoundError("Unit not found for this product.")
        base_price = Decimal(str(unit.price))
        base_stock_deduction = int(quantity * Decimal(str(unit.conversion_ratio)))

    # Stock availability check (variant stock takes precedence over base product inventory).
    if variant:
        available = variant.stock_quantity
        stock_holder = "variant"
    else:
        available = product.inventory.quantity if product.inventory else 0
        stock_holder = "inventory"

    if available < base_stock_deduction:
        raise ConflictError(
            f"Insufficient stock for '{product.name}"
            f"{' (' + variant.name + ')' if variant else ''}'. "
            f"Available: {available}, requested: {base_stock_deduction}."
        )

    # Discount: either a flat discount_amount, or discount_type/value driven.
    discount_amount = Decimal(str(item_data.get("discount_amount", 0)))
    if item_data.get("discount_type") == "percentage" and item_data.get("discount_value"):
        pct = Decimal(str(item_data["discount_value"]))
        discount_amount = (base_price * quantity) * (pct / Decimal("100"))
    elif item_data.get("discount_type") == "fixed" and item_data.get("discount_value"):
        discount_amount = Decimal(str(item_data["discount_value"]))

    line_subtotal = (base_price * quantity) - discount_amount
    if line_subtotal < 0:
        raise ConflictError("Discount cannot exceed the line item's value.")
    line_tax = line_subtotal * (tax_rate / Decimal("100"))
    line_total = line_subtotal + line_tax

    return ResolvedLine(
        product=product, variant=variant, unit=unit, quantity=quantity,
        unit_price=base_price, tax_rate=tax_rate, discount_amount=discount_amount,
        line_total=line_total, base_stock_deduction=base_stock_deduction, stock_holder=stock_holder,
    )
