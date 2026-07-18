from app.models.inventory import Inventory
from app.models.inventory_history import InventoryHistory
from app.repositories.base_repository import BaseRepository


class InventoryRepository(BaseRepository):
    model = Inventory

    def get_by_product_id(self, product_id):
        return Inventory.query.filter_by(product_id=product_id).first()

    def get_low_stock(self):
        return Inventory.query.filter(Inventory.quantity <= Inventory.low_stock_threshold)

    def add_history(self, **kwargs):
        entry = InventoryHistory(**kwargs)
        from app.extensions import db
        db.session.add(entry)
        db.session.commit()
        return entry

    def get_history_for_product(self, inventory_id):
        return InventoryHistory.query.filter_by(inventory_id=inventory_id).order_by(
            InventoryHistory.created_at.desc()
        )
