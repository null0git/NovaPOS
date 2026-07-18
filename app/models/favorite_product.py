from app.extensions import db
from app.models._base import TimestampMixin, SerializerMixin


class FavoriteProduct(db.Model, TimestampMixin, SerializerMixin):
    """A cashier's pinned favorite product, for quick-access buttons on the POS screen."""
    __tablename__ = "favorite_products"
    __table_args__ = (db.UniqueConstraint("user_id", "product_id", name="uq_user_favorite_product"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)

    user = db.relationship("User")
    product = db.relationship("Product")

    def to_dict(self, exclude=None):
        data = super().to_dict(exclude)
        data["product_name"] = self.product.name if self.product else None
        return data

    def __repr__(self):
        return f"<FavoriteProduct user={self.user_id} product={self.product_id}>"
