from app.extensions import db
from app.models._base import TimestampMixin, SerializerMixin


class SaleItem(db.Model, TimestampMixin, SerializerMixin):
    __tablename__ = "sale_items"

    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey("sales.id"), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False, index=True)
    variant_id = db.Column(db.Integer, db.ForeignKey("product_variants.id"), nullable=True)
    unit_id = db.Column(db.Integer, db.ForeignKey("product_units.id"), nullable=True)

    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(12, 2), nullable=False)  # price at time of sale
    tax_rate = db.Column(db.Numeric(5, 2), nullable=False, default=0)
    discount_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    line_total = db.Column(db.Numeric(12, 2), nullable=False)

    refunded_quantity = db.Column(db.Integer, nullable=False, default=0)

    sale = db.relationship("Sale", back_populates="items")
    product = db.relationship("Product", back_populates="sale_items")
    variant = db.relationship("ProductVariant")
    unit = db.relationship("ProductUnit")

    def to_dict(self, exclude=None):
        data = super().to_dict(exclude)
        for f in ("unit_price", "tax_rate", "discount_amount", "line_total"):
            data[f] = float(getattr(self, f))
        data["product_name"] = self.product.name if self.product else None
        data["sku"] = self.product.sku if self.product else None
        return data

    def __repr__(self):
        return f"<SaleItem sale={self.sale_id} product={self.product_id} qty={self.quantity}>"
