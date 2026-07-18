"""
Business logic for gift cards and store credit. Both share the same
mechanics (a balance you can recharge and redeem); `card_type` just labels
how the balance originated, since store credit is normally issued
automatically after a refund rather than purchased outright.
"""
import random
import string
from decimal import Decimal

from app.core.middleware.error_handler import ConflictError, NotFoundError
from app.extensions import db
from app.repositories.gift_card_repository import GiftCardRepository
from app.services.audit_service import AuditService


class GiftCardService:
    def __init__(self):
        self.repo = GiftCardRepository()
        self.audit_service = AuditService()

    def _generate_code(self):
        return "GC-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=10))

    def issue(self, actor_id, initial_value, customer_id=None, expires_at=None, card_type="gift_card"):
        code = self._generate_code()
        while self.repo.code_exists(code):
            code = self._generate_code()

        card = self.repo.create(
            code=code, card_type=card_type, balance=initial_value, initial_value=initial_value,
            customer_id=customer_id, expires_at=expires_at, issued_by_id=actor_id,
        )
        self.repo.add_transaction(
            gift_card_id=card.id, transaction_type="issue", amount=Decimal(str(initial_value)),
            balance_after=card.balance, performed_by_id=actor_id,
        )
        db.session.commit()
        self.audit_service.log(actor_id, f"gift_card.issue", "gift_card", card.id,
                                details={"initial_value": float(initial_value), "card_type": card_type})
        return card

    def issue_store_credit_for_refund(self, actor_id, customer_id, amount, refund_id):
        """Called automatically when a refund is issued as store credit instead of cash back."""
        card = self.issue(actor_id, amount, customer_id=customer_id, card_type="store_credit")
        self.audit_service.log(actor_id, "gift_card.store_credit_from_refund", "gift_card", card.id,
                                details={"refund_id": refund_id, "amount": float(amount)})
        return card

    def get_by_code(self, code):
        card = self.repo.get_by_code(code)
        if not card:
            raise NotFoundError("Gift card not found.")
        return card

    def get_balance(self, code):
        card = self.get_by_code(code)
        return {"code": card.code, "balance": float(card.balance), "is_active": card.is_active,
                "expires_at": card.expires_at.isoformat() if card.expires_at else None}

    def recharge(self, actor_id, code, amount):
        card = self.get_by_code(code)
        if not card.is_active:
            raise ConflictError("This gift card has been deactivated.")

        amount = Decimal(str(amount))
        card.balance += amount
        db.session.commit()

        self.repo.add_transaction(
            gift_card_id=card.id, transaction_type="recharge", amount=amount,
            balance_after=card.balance, performed_by_id=actor_id,
        )
        db.session.commit()
        self.audit_service.log(actor_id, "gift_card.recharge", "gift_card", card.id,
                                details={"amount": float(amount)})
        return card

    def redeem(self, actor_id, code, amount, sale_id=None):
        """Deduct `amount` from the card's balance (used as a payment method during checkout)."""
        card = self.get_by_code(code)
        if not card.is_active:
            raise ConflictError("This gift card has been deactivated.")

        amount = Decimal(str(amount))
        if card.balance < amount:
            raise ConflictError(f"Insufficient gift card balance. Available: {card.balance}, requested: {amount}.")

        card.balance -= amount
        db.session.commit()

        self.repo.add_transaction(
            gift_card_id=card.id, transaction_type="redeem", amount=-amount,
            balance_after=card.balance, sale_id=sale_id, performed_by_id=actor_id,
        )
        db.session.commit()
        self.audit_service.log(actor_id, "gift_card.redeem", "gift_card", card.id,
                                details={"amount": float(amount), "sale_id": sale_id})
        return card

    def deactivate(self, actor_id, code):
        card = self.get_by_code(code)
        card.is_active = False
        db.session.commit()
        self.audit_service.log(actor_id, "gift_card.deactivate", "gift_card", card.id)
        return card

    def transaction_history(self, code):
        card = self.get_by_code(code)
        return self.repo.get_transactions(card.id)

    def list_for_customer(self, customer_id):
        return self.repo.get_for_customer(customer_id)
