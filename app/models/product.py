from app.extensions import db
from app.models._base import TimestampMixin, SerializerMixin


class Product(db.Model, TimestampMixin, SerializerMixin):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=False, index=True)
    barcode = db.Column(db.String(100), nullable=True, index=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    cost_price = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    tax_rate = db.Column(db.Numeric(5, 2), nullable=False, default=0)  # percentage
    image_filename = db.Column(db.String(255))
    barcode_image_filename = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    unit = db.Column(db.String(20), default="pcs")  # pcs, kg, litre, etc.
    is_tax_exempt = db.Column(db.Boolean, default=False, nullable=False)

    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    category = db.relationship("Category", back_populates="products")

    inventory = db.relationship("Inventory", back_populates="product", uselist=False,
                                 cascade="all, delete-orphan")
    sale_items = db.relationship("SaleItem", back_populates="product")
    variants = db.relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")
    units = db.relationship("ProductUnit", back_populates="product", cascade="all, delete-orphan")

    def to_dict(self, exclude=None):
        data = super().to_dict(exclude)
        data["price"] = float(self.price) if self.price is not None else None
        data["cost_price"] = float(self.cost_price) if self.cost_price is not None else None
        data["tax_rate"] = float(self.tax_rate) if self.tax_rate is not None else None
        data["category_name"] = self.category.name if self.category else None
        data["current_stock"] = self.inventory.quantity if self.inventory else 0
        return data

    def __repr__(self):
        return f"<Product {self.sku} {self.name}>"
