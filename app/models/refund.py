from app.extensions import db
from app.models._base import TimestampMixin, SerializerMixin


class Refund(db.Model, TimestampMixin, SerializerMixin):
    __tablename__ = "refunds"

    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey("sales.id"), nullable=False)
    sale_item_id = db.Column(db.Integer, db.ForeignKey("sale_items.id"), nullable=True)

    quantity = db.Column(db.Integer, nullable=False, default=0)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    reason = db.Column(db.String(255))
    status = db.Column(db.String(20), nullable=False, default="completed")

    processed_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    processed_by = db.relationship("User")

    sale = db.relationship("Sale", back_populates="refunds")
    sale_item = db.relationship("SaleItem")

    def to_dict(self, exclude=None):
        data = super().to_dict(exclude)
        data["amount"] = float(self.amount)
        data["processed_by_name"] = self.processed_by.full_name if self.processed_by else None
        return data

    def __repr__(self):
        return f"<Refund sale={self.sale_id} amount={self.amount}>"
