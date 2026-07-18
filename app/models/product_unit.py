from app.extensions import db
from app.models._base import TimestampMixin, SerializerMixin


class ProductUnit(db.Model, TimestampMixin, SerializerMixin):
    """
    An alternate selling unit for a product (e.g. Sugar sold as 'kg', '500g', '250g').

    conversion_ratio is expressed in terms of the product's base inventory unit.
    e.g. if the base unit is grams and this unit is 'kg', conversion_ratio = 1000
    (selling 1 of this unit deducts 1000 base units from inventory).
    """
    __tablename__ = "product_units"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)

    unit_name = db.Column(db.String(30), nullable=False)  # kg, 500g, carton, bottle...
    conversion_ratio = db.Column(db.Numeric(12, 4), nullable=False, default=1)
    price = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    barcode = db.Column(db.String(100), unique=True, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    product = db.relationship("Product", back_populates="units")

    def to_dict(self, exclude=None):
        data = super().to_dict(exclude)
        data["conversion_ratio"] = float(self.conversion_ratio)
        data["price"] = float(self.price)
        data["product_name"] = self.product.name if self.product else None
        return data

    def __repr__(self):
        return f"<ProductUnit {self.unit_name} of product={self.product_id}>"
