"""Business logic for receipt numbering, verification codes, and text formatting."""
import random
import string
from datetime import datetime, timezone

from app.core.utils.receipt import format_receipt_text
from app.repositories.sales_repository import SalesRepository


class ReceiptService:
    def __init__(self):
        self.sales_repo = SalesRepository()

    def generate_receipt_number(self):
        """e.g. NP-20260706-8F3K1Q — date-prefixed, so receipts sort naturally and are unique."""
        while True:
            suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
            candidate = f"NP-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{suffix}"
            if not self.sales_repo.receipt_number_exists(candidate):
                return candidate

    def generate_verification_code(self):
        """A short customer-facing code (distinct from the receipt number) used for
        the public receipt-verification lookup — printed as text + encoded in the QR."""
        from app.models.sale import Sale
        while True:
            code = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if not Sale.query.filter_by(verification_code=code).first():
                return code

    def get_receipt_text(self, sale, business_name="NovaPOS Store", **kwargs):
        return format_receipt_text(sale, business_name=business_name, **kwargs)
