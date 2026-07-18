"""Business logic for recording and validating payments against a sale."""
from decimal import Decimal

from app.core.middleware.error_handler import ConflictError
from app.extensions import db
from app.repositories.sales_repository import SalesRepository


class PaymentService:
    def __init__(self):
        self.sales_repo = SalesRepository()

    def process_payments(self, sale, payments_data):
        """Create Payment rows for `sale`; raises if total paid doesn't cover the sale total."""
        total_paid = Decimal("0")
        payment_records = []

        for payment in payments_data:
            amount = Decimal(str(payment["amount"]))
            amount_tendered = payment.get("amount_tendered")
            change_due = None
            reference = payment.get("reference")

            if payment["method"] == "cash" and amount_tendered is not None:
                amount_tendered = Decimal(str(amount_tendered))
                if amount_tendered < amount:
                    raise ConflictError("Amount tendered is less than the payment amount.")
                change_due = amount_tendered - amount

            if payment["method"] == "gift_card":
                gift_card_code = payment.get("gift_card_code")
                if not gift_card_code:
                    raise ConflictError("gift_card_code is required for gift_card payments.")
                from app.services.gift_card_service import GiftCardService
                GiftCardService().redeem(sale.cashier_id, gift_card_code, amount, sale_id=sale.id)
                reference = gift_card_code

            record = self.sales_repo.add_payment(
                sale_id=sale.id,
                method=payment["method"],
                amount=amount,
                amount_tendered=amount_tendered,
                change_due=change_due,
                reference=reference,
            )
            payment_records.append(record)
            total_paid += amount

        if total_paid < Decimal(str(sale.total_amount)):
            raise ConflictError(
                f"Total payments ({total_paid}) do not cover the sale total ({sale.total_amount})."
            )

        db.session.commit()
        return payment_records
