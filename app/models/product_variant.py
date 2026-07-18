from app.extensions import db
from app.models._base import TimestampMixin, SerializerMixin


class ProductVariant(db.Model, TimestampMixin, SerializerMixin):
    """A variant of a product (e.g. Coca-Cola 500ml vs 1L), each with its own stock/pricing."""
    __tablename__ = "product_variants"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)

    name = db.Column(db.String(100), nullable=False)  # e.g. "500ml", "Medium"
    sku = db.Column(db.String(50), unique=True, nullable=False)
    barcode = db.Column(db.String(100), unique=True, nullable=True)
    cost_price = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    price = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    stock_quantity = db.Column(db.Integer, nullable=False, default=0)
    low_stock_threshold = db.Column(db.Integer, nullable=False, default=5)
    image_filename = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    product = db.relationship("Product", back_populates="variants")

    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.low_stock_threshold

    def to_dict(self, exclude=None):
        data = super().to_dict(exclude)
        data["price"] = float(self.price)
        data["cost_price"] = float(self.cost_price)
        data["is_low_stock"] = self.is_low_stock
        data["product_name"] = self.product.name if self.product else None
        return data

    def __repr__(self):
        return f"<ProductVariant {self.sku} {self.name}>"
