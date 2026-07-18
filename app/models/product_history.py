from app.extensions import db
from app.models._base import TimestampMixin, SerializerMixin


class ProductHistory(db.Model, TimestampMixin, SerializerMixin):
    """
    Field-level change log for products/variants: price changes, barcode
    changes, image updates, archive/restore. (Stock changes already have
    their own detailed InventoryHistory table.)
    """
    __tablename__ = "product_history"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey("product_variants.id"), nullable=True)

    change_type = db.Column(db.String(30), nullable=False)
    # price, cost_price, barcode, image, archive, restore, variant_change, general

    field_name = db.Column(db.String(50))
    old_value = db.Column(db.String(255))
    new_value = db.Column(db.String(255))

    changed_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    changed_by = db.relationship("User")

    product = db.relationship("Product")
    variant = db.relationship("ProductVariant")

    def to_dict(self, exclude=None):
        data = super().to_dict(exclude)
        data["changed_by_name"] = self.changed_by.full_name if self.changed_by else None
        return data

    def __repr__(self):
        return f"<ProductHistory {self.change_type} product={self.product_id}>"
