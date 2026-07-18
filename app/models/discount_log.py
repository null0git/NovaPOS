from app.extensions import db
from app.models._base import TimestampMixin, SerializerMixin


class DiscountLog(db.Model, TimestampMixin, SerializerMixin):
    """Audit trail for every manual discount applied (cart-level or line-item-level)."""
    __tablename__ = "discount_logs"

    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey("sales.id"), nullable=False)
    sale_item_id = db.Column(db.Integer, db.ForeignKey("sale_items.id"), nullable=True)  # null = cart-level

    discount_type = db.Column(db.String(20), nullable=False)  # percentage, fixed
    scope = db.Column(db.String(20), nullable=False)  # product, cart
    original_amount = db.Column(db.Numeric(12, 2), nullable=False)
    discount_amount = db.Column(db.Numeric(12, 2), nullable=False)
    reason = db.Column(db.String(255))

    cashier_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    cashier = db.relationship("User")

    def to_dict(self, exclude=None):
        data = super().to_dict(exclude)
        data["original_amount"] = float(self.original_amount)
        data["discount_amount"] = float(self.discount_amount)
        data["cashier_name"] = self.cashier.full_name if self.cashier else None
        return data

    def __repr__(self):
        return f"<DiscountLog sale={self.sale_id} amount={self.discount_amount}>"
