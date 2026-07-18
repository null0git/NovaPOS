"""Business logic for product variants (e.g. Coca-Cola 330ml/500ml/1L)."""
from app.core.middleware.error_handler import ConflictError, NotFoundError
from app.extensions import db
from app.repositories.variant_repository import VariantRepository
from app.repositories.product_repository import ProductRepository
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService


class VariantService:
    def __init__(self):
        self.repo = VariantRepository()
        self.product_repo = ProductRepository()
        self.audit_service = AuditService()
        self.notification_service = NotificationService()

    def list_for_product(self, product_id):
        return self.repo.get_for_product(product_id)

    def get_variant(self, variant_id):
        variant = self.repo.get_by_id(variant_id)
        if not variant:
            raise NotFoundError("Variant not found.")
        return variant

    def list_low_stock(self):
        return self.repo.get_low_stock()

    def create_variant(self, actor_id, product_id, name, sku, price, cost_price=0,
                        barcode=None, stock_quantity=0, low_stock_threshold=5):
        product = self.product_repo.get_by_id(product_id)
        if not product:
            raise NotFoundError("Product not found.")
        if self.repo.sku_exists(sku):
            raise ConflictError("A variant with this SKU already exists.")
        if barcode and self.repo.barcode_exists(barcode):
            raise ConflictError("A variant with this barcode already exists.")

        variant = self.repo.create(
            product_id=product_id, name=name, sku=sku, barcode=barcode,
            price=price, cost_price=cost_price, stock_quantity=stock_quantity,
            low_stock_threshold=low_stock_threshold,
        )
        self.audit_service.log(actor_id, "variant.create", "product_variant", variant.id)
        return variant

    def update_variant(self, actor_id, variant_id, **fields):
        variant = self.get_variant(variant_id)
        sku = fields.get("sku")
        barcode = fields.get("barcode")
        if sku and self.repo.sku_exists(sku, exclude_id=variant_id):
            raise ConflictError("A variant with this SKU already exists.")
        if barcode and self.repo.barcode_exists(barcode, exclude_id=variant_id):
            raise ConflictError("A variant with this barcode already exists.")
        for key, value in fields.items():
            if value is not None:
                setattr(variant, key, value)
        db.session.commit()
        self.audit_service.log(actor_id, "variant.update", "product_variant", variant.id, details=fields)
        return variant

    def delete_variant(self, actor_id, variant_id):
        variant = self.get_variant(variant_id)
        variant.is_active = False
        db.session.commit()
        self.audit_service.log(actor_id, "variant.deactivate", "product_variant", variant.id)
        return variant

    def adjust_stock(self, actor_id, variant_id, quantity_change, reason="Adjustment"):
        variant = self.get_variant(variant_id)
        new_quantity = variant.stock_quantity + quantity_change
        if new_quantity < 0:
            raise ConflictError("This change would result in negative stock.")
        variant.stock_quantity = new_quantity
        db.session.commit()

        self.audit_service.log(actor_id, "variant.stock_adjust", "product_variant", variant.id,
                                details={"quantity_change": quantity_change, "reason": reason})

        if variant.stock_quantity == 0:
            self.notification_service.create(
                type_="out_of_stock",
                title=f"Out of stock: {variant.product.name} ({variant.name})",
                message="This variant is now completely out of stock.",
                severity="critical",
                meta={"variant_id": variant.id},
            )
        elif variant.is_low_stock:
            self.notification_service.create(
                type_="low_stock",
                title=f"Low stock: {variant.product.name} ({variant.name})",
                message=f"{variant.name} has {variant.stock_quantity} units left.",
                severity="warning",
                meta={"variant_id": variant.id, "quantity": variant.stock_quantity},
            )
        return variant

    def restock(self, actor_id, variant_id, quantity, reason="Restock"):
        return self.adjust_stock(actor_id, variant_id, quantity, reason)
