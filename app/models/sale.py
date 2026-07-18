from app.extensions import db
from app.models._base import TimestampMixin, SerializerMixin


class Sale(db.Model, TimestampMixin, SerializerMixin):
    __tablename__ = "sales"

    id = db.Column(db.Integer, primary_key=True)
    receipt_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    verification_code = db.Column(db.String(12), unique=True, nullable=True, index=True)

    subtotal = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    tax_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    discount_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    total_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)

    status = db.Column(db.String(20), nullable=False, default="completed", index=True)
    # statuses: draft, awaiting_payment, completed, voided, refunded, partially_refunded

    terminal_id = db.Column(db.Integer, db.ForeignKey("devices.id"), nullable=True)
    terminal = db.relationship("Device")

    customer_payment_method = db.Column(db.String(20), nullable=True)
    # method chosen by the customer on the customer display: cash, chapa, offline

    cashier_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    cashier = db.relationship("User", back_populates="sales", foreign_keys=[cashier_id])

    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=True, index=True)
    customer = db.relationship("Customer", back_populates="sales")

    items = db.relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")
    payments = db.relationship("Payment", back_populates="sale", cascade="all, delete-orphan")
    refunds = db.relationship("Refund", back_populates="sale", cascade="all, delete-orphan")

    def to_dict(self, exclude=None):
        data = super().to_dict(exclude)
        for f in ("subtotal", "tax_amount", "discount_amount", "total_amount"):
            data[f] = float(getattr(self, f))
        data["cashier_name"] = self.cashier.full_name if self.cashier else None
        data["customer_name"] = self.customer.name if self.customer else None
        data["items"] = [item.to_dict() for item in self.items]
        data["payments"] = [p.to_dict() for p in self.payments]
        return data

    def __repr__(self):
        return f"<Sale {self.receipt_number} total={self.total_amount}>"
