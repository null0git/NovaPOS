from app.extensions import db
from app.models._base import TimestampMixin, SerializerMixin


class Customer(db.Model, TimestampMixin, SerializerMixin):
    __tablename__ = "customers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    phone = db.Column(db.String(20), unique=True, nullable=True)
    address = db.Column(db.String(255))
    loyalty_points = db.Column(db.Integer, default=0, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    sales = db.relationship("Sale", back_populates="customer")

    def __repr__(self):
        return f"<Customer {self.name}>"
