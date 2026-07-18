from app.extensions import db
from app.models._base import TimestampMixin, SerializerMixin


class Payment(db.Model, TimestampMixin, SerializerMixin):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey("sales.id"), nullable=False, index=True)

    method = db.Column(db.String(30), nullable=False, index=True)  # cash, card, chapa, offline, mobile_money, wallet
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    amount_tendered = db.Column(db.Numeric(12, 2), nullable=True)  # for cash
    change_due = db.Column(db.Numeric(12, 2), nullable=True)
    reference = db.Column(db.String(100))  # transaction id from card/mobile processor
    status = db.Column(db.String(20), nullable=False, default="completed")
    # statuses: pending, completed, failed, cancelled

    external_reference = db.Column(db.String(150))  # e.g. Chapa tx_ref
    checkout_url = db.Column(db.String(500))  # e.g. Chapa hosted checkout link
    gateway_response = db.Column(db.JSON)

    sale = db.relationship("Sale", back_populates="payments")

    def to_dict(self, exclude=None):
        data = super().to_dict(exclude)
        for f in ("amount", "amount_tendered", "change_due"):
            val = getattr(self, f)
            data[f] = float(val) if val is not None else None
        return data

    def __repr__(self):
        return f"<Payment {self.method} {self.amount}>"
