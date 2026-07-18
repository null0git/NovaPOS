from app.extensions import db
from app.models._base import TimestampMixin, SerializerMixin


class Inventory(db.Model, TimestampMixin, SerializerMixin):
    __tablename__ = "inventory"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), unique=True, nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    low_stock_threshold = db.Column(db.Integer, nullable=False, default=5)
    reorder_quantity = db.Column(db.Integer, nullable=False, default=20)

    product = db.relationship("Product", back_populates="inventory")
    history = db.relationship("InventoryHistory", back_populates="inventory",
                               cascade="all, delete-orphan", order_by="InventoryHistory.created_at.desc()")

    @property
    def is_low_stock(self):
        return self.quantity <= self.low_stock_threshold

    def to_dict(self, exclude=None):
        data = super().to_dict(exclude)
        data["is_low_stock"] = self.is_low_stock
        data["product_name"] = self.product.name if self.product else None
        return data

    def __repr__(self):
        return f"<Inventory product_id={self.product_id} qty={self.quantity}>"
