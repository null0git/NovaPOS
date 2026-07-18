from app.extensions import db
from app.models._base import TimestampMixin, SerializerMixin


class Category(db.Model, TimestampMixin, SerializerMixin):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))
    parent_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    parent = db.relationship("Category", remote_side=[id], backref="subcategories")
    products = db.relationship("Product", back_populates="category")

    def __repr__(self):
        return f"<Category {self.name}>"
