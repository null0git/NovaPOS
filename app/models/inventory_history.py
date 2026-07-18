from app.extensions import db
from app.models._base import TimestampMixin, SerializerMixin


class InventoryHistory(db.Model, TimestampMixin, SerializerMixin):
    """Immutable log of every stock change (sale, restock, manual adjustment, refund)."""
    __tablename__ = "inventory_history"

    id = db.Column(db.Integer, primary_key=True)
    inventory_id = db.Column(db.Integer, db.ForeignKey("inventory.id"), nullable=False, index=True)
    change_type = db.Column(db.String(30), nullable=False)  # sale, restock, adjustment, refund
    quantity_change = db.Column(db.Integer, nullable=False)  # negative for deductions
    quantity_after = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(255))
    reference_type = db.Column(db.String(30))  # e.g. "sale", "refund"
    reference_id = db.Column(db.Integer)

    performed_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    performed_by = db.relationship("User")

    inventory = db.relationship("Inventory", back_populates="history")

    def __repr__(self):
        return f"<InventoryHistory {self.change_type} {self.quantity_change}>"
