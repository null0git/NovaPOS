"""Business logic for stock levels: deductions, restocks, manual adjustments, alerts."""
from app.core.middleware.error_handler import ConflictError, NotFoundError
from app.extensions import db
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.product_repository import ProductRepository
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService


class InventoryService:
    def __init__(self):
        self.repo = InventoryRepository()
        self.product_repo = ProductRepository()
        self.audit_service = AuditService()
        self.notification_service = NotificationService()

    def get_for_product(self, product_id):
        inventory = self.repo.get_by_product_id(product_id)
        if not inventory:
            raise NotFoundError("No inventory record for this product.")
        return inventory

    def list_all(self):
        return self.repo.get_all()

    def list_low_stock(self):
        return self.repo.get_low_stock()

    def get_history(self, product_id):
        inventory = self.get_for_product(product_id)
        return self.repo.get_history_for_product(inventory.id)

    def _apply_change(self, inventory, quantity_change, change_type, reason, actor_id,
                       reference_type=None, reference_id=None):
        new_quantity = inventory.quantity + quantity_change
        if new_quantity < 0:
            raise ConflictError("This change would result in negative stock.")

        inventory.quantity = new_quantity
        db.session.commit()

        self.repo.add_history(
            inventory_id=inventory.id,
            change_type=change_type,
            quantity_change=quantity_change,
            quantity_after=new_quantity,
            reason=reason,
            reference_type=reference_type,
            reference_id=reference_id,
            performed_by_id=actor_id,
        )

        if inventory.quantity == 0:
            self.notification_service.create(
                type_="out_of_stock",
                title=f"Out of stock: {inventory.product.name if inventory.product else 'Product'}",
                message="This product is now completely out of stock.",
                severity="critical",
                meta={"product_id": inventory.product_id},
            )
        elif inventory.is_low_stock:
            self.notification_service.notify_low_stock(inventory)

        return inventory

    def restock(self, actor_id, product_id, quantity, reason="Restock"):
        inventory = self.get_for_product(product_id)
        result = self._apply_change(inventory, quantity, "restock", reason, actor_id)
        self.audit_service.log(actor_id, "inventory.restock", "inventory", inventory.id,
                                details={"quantity": quantity})
        return result

    def adjust(self, actor_id, product_id, quantity_change, reason):
        inventory = self.get_for_product(product_id)
        result = self._apply_change(inventory, quantity_change, "adjustment", reason, actor_id)
        self.audit_service.log(actor_id, "inventory.adjust", "inventory", inventory.id,
                                details={"quantity_change": quantity_change, "reason": reason})
        return result

    def deduct_for_sale(self, actor_id, product_id, quantity, sale_id):
        inventory = self.get_for_product(product_id)
        return self._apply_change(
            inventory, -quantity, "sale", f"Sale #{sale_id}", actor_id,
            reference_type="sale", reference_id=sale_id,
        )

    def restore_for_refund(self, actor_id, product_id, quantity, refund_id):
        inventory = self.get_for_product(product_id)
        return self._apply_change(
            inventory, quantity, "refund", f"Refund #{refund_id}", actor_id,
            reference_type="refund", reference_id=refund_id,
        )

    def update_thresholds(self, actor_id, product_id, **fields):
        inventory = self.get_for_product(product_id)
        for key, value in fields.items():
            if value is not None:
                setattr(inventory, key, value)
        db.session.commit()
        self.audit_service.log(actor_id, "inventory.update_thresholds", "inventory", inventory.id,
                                details=fields)
        return inventory
