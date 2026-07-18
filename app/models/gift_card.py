from app.extensions import db
from app.models._base import TimestampMixin, SerializerMixin


class GiftCard(db.Model, TimestampMixin, SerializerMixin):
    """
    A gift card or store-credit account. `card_type` distinguishes a
    purchased gift card from store credit issued after a refund — both
    share the same balance/redemption mechanics.
    """
    __tablename__ = "gift_cards"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(30), unique=True, nullable=False, index=True)
    card_type = db.Column(db.String(20), nullable=False, default="gift_card")  # gift_card, store_credit
    balance = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    initial_value = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=True)

    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=True)
    customer = db.relationship("Customer")

    issued_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    issued_by = db.relationship("User")

    transactions = db.relationship("GiftCardTransaction", back_populates="gift_card",
                                    cascade="all, delete-orphan", order_by="GiftCardTransaction.created_at.desc()")

    def to_dict(self, exclude=None):
        data = super().to_dict(exclude)
        data["balance"] = float(self.balance)
        data["initial_value"] = float(self.initial_value)
        data["customer_name"] = self.customer.name if self.customer else None
        return data

    def __repr__(self):
        return f"<GiftCard {self.code} balance={self.balance}>"


class GiftCardTransaction(db.Model, TimestampMixin, SerializerMixin):
    """Ledger entry for a gift card: issue, recharge, redeem (payment), or refund-credit."""
    __tablename__ = "gift_card_transactions"

    id = db.Column(db.Integer, primary_key=True)
    gift_card_id = db.Column(db.Integer, db.ForeignKey("gift_cards.id"), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # issue, recharge, redeem, refund_credit
    amount = db.Column(db.Numeric(12, 2), nullable=False)  # positive for credit, negative for redemption
    balance_after = db.Column(db.Numeric(12, 2), nullable=False)
    sale_id = db.Column(db.Integer, db.ForeignKey("sales.id"), nullable=True)
    performed_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    notes = db.Column(db.String(255))

    gift_card = db.relationship("GiftCard", back_populates="transactions")
    sale = db.relationship("Sale")
    performed_by = db.relationship("User")

    def to_dict(self, exclude=None):
        data = super().to_dict(exclude)
        data["amount"] = float(self.amount)
        data["balance_after"] = float(self.balance_after)
        return data

    def __repr__(self):
        return f"<GiftCardTransaction {self.transaction_type} {self.amount}>"
