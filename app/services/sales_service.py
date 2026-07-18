"""
Business logic for the sales/checkout flow. This is the heart of the POS:

  check stock -> reduce inventory -> create sale + items -> record payments
  -> save audit log -> notify dashboard (WebSocket)
"""
from decimal import Decimal

from app.core.middleware.error_handler import ConflictError, NotFoundError
from app.core.utils.datetime_utils import humanize_timedelta
from app.extensions import db
from app.repositories.sales_repository import SalesRepository
from app.repositories.product_repository import ProductRepository
from app.services.audit_service import AuditService
from app.services.inventory_service import InventoryService
from app.services.payment_service import PaymentService
from app.services.pricing_helper import resolve_sale_line
from app.services.receipt_service import ReceiptService


class SalesService:
    def __init__(self):
        self.repo = SalesRepository()
        self.product_repo = ProductRepository()
        self.inventory_service = InventoryService()
        self.payment_service = PaymentService()
        self.receipt_service = ReceiptService()
        self.audit_service = AuditService()

    def list_sales(self):
        return self.repo.get_all()

    def get_sale(self, sale_id):
        sale = self.repo.get_by_id(sale_id)
        if not sale:
            raise NotFoundError("Sale not found.")
        return sale

    def get_by_receipt(self, receipt_number):
        sale = self.repo.get_by_receipt_number(receipt_number)
        if not sale:
            raise NotFoundError("Sale not found for this receipt number.")
        return sale

    def create_sale(self, cashier_id, items_data, payments_data, customer_id=None, discount_amount=0,
                     discount_reason=None):
        # 1. Resolve every line (product/variant/unit, price, tax, per-line discount) and
        #    check stock availability before touching anything.
        resolved_lines = [resolve_sale_line(item_data) for item_data in items_data]

        # 2. Compute totals.
        subtotal = Decimal("0")
        tax_total = Decimal("0")
        for line in resolved_lines:
            subtotal += (line.unit_price * line.quantity) - line.discount_amount
            tax_total += line.line_total - ((line.unit_price * line.quantity) - line.discount_amount)

        overall_discount = Decimal(str(discount_amount))
        total_amount = subtotal + tax_total - overall_discount
        if total_amount < 0:
            raise ConflictError("Discount cannot exceed the sale subtotal.")

        # 3. Create the sale header.
        sale = self.repo.create(
            receipt_number=self.receipt_service.generate_receipt_number(),
            verification_code=self.receipt_service.generate_verification_code(),
            subtotal=subtotal,
            tax_amount=tax_total,
            discount_amount=overall_discount,
            total_amount=total_amount,
            status="completed",
            cashier_id=cashier_id,
            customer_id=customer_id,
        )

        # 4. Create sale items, deduct stock (variant/unit-aware), and log any discounts.
        for line, item_data in zip(resolved_lines, items_data):
            sale_item = self.repo.add_item(
                sale_id=sale.id,
                product_id=line.product.id,
                variant_id=line.variant.id if line.variant else None,
                unit_id=line.unit.id if line.unit else None,
                quantity=line.quantity,
                unit_price=line.unit_price,
                tax_rate=line.tax_rate,
                discount_amount=line.discount_amount,
                line_total=line.line_total,
            )
            db.session.flush()

            if line.variant:
                from app.services.variant_service import VariantService
                VariantService().adjust_stock(cashier_id, line.variant.id, -line.base_stock_deduction,
                                               reason=f"Sale #{sale.id}")
            else:
                self.inventory_service.deduct_for_sale(
                    cashier_id, line.product.id, line.base_stock_deduction, sale.id
                )

            if line.discount_amount > 0:
                self._log_discount(sale.id, sale_item.id, item_data, line, cashier_id)

        db.session.commit()

        if overall_discount > 0:
            from app.repositories.discount_repository import DiscountRepository
            DiscountRepository().create(
                sale_id=sale.id, sale_item_id=None, discount_type="fixed", scope="cart",
                original_amount=subtotal + tax_total, discount_amount=overall_discount,
                reason=discount_reason, cashier_id=cashier_id,
            )

        # 5. Record payments (validates that payment covers the total).
        self.payment_service.process_payments(sale, payments_data)

        # 6. Audit + realtime notification to dashboards/customer displays.
        self.audit_service.log(cashier_id, "sale.create", "sale", sale.id,
                                details={"total_amount": float(total_amount)})
        self._broadcast_sale(sale)
        self._print_receipt(sale)

        return sale

    def _log_discount(self, sale_id, sale_item_id, item_data, line, actor_id):
        from app.repositories.discount_repository import DiscountRepository
        DiscountRepository().create(
            sale_id=sale_id, sale_item_id=sale_item_id,
            discount_type=item_data.get("discount_type", "fixed"), scope="product",
            original_amount=line.unit_price * line.quantity, discount_amount=line.discount_amount,
            reason=item_data.get("discount_reason"), cashier_id=actor_id,
        )

    def _print_receipt(self, sale):
        try:
            from app.services.printer_service import PrinterService
            PrinterService().print_receipt(sale)
        except Exception:
            # Printing failures should never roll back a completed sale;
            # PrinterService already raises a notification for offline printers.
            pass

    def void_sale(self, actor_id, sale_id, reason="Voided by staff"):
        sale = self.get_sale(sale_id)
        if sale.status != "completed":
            raise ConflictError(f"Cannot void a sale with status '{sale.status}'.")

        for item in sale.items:
            self.inventory_service.restore_for_refund(actor_id, item.product_id, item.quantity, sale.id)

        sale.status = "voided"
        db.session.commit()
        self.audit_service.log(actor_id, "sale.void", "sale", sale.id, details={"reason": reason})
        return sale

    def search_for_refund(self, receipt_number=None, receipt_barcode=None, product_barcode=None):
        """
        Find sale(s) eligible for refund via receipt number, a scanned receipt
        barcode (which encodes the receipt number), or a scanned product barcode
        (returns recent sales containing that product, for when the receipt is lost).
        """
        if receipt_number or receipt_barcode:
            code = receipt_number or receipt_barcode
            sale = self.repo.get_by_receipt_number(code)
            if not sale:
                raise NotFoundError("No sale found for that receipt number/barcode.")
            return [self._refund_lookup_dict(sale)]

        if product_barcode:
            from app.services.barcode_service import BarcodeService
            product = BarcodeService().lookup_by_barcode(product_barcode)
            from app.models.sale_item import SaleItem
            from app.models.sale import Sale
            items = (
                SaleItem.query.join(Sale)
                .filter(SaleItem.product_id == product.id, Sale.status.in_(["completed", "partially_refunded"]))
                .order_by(Sale.created_at.desc())
                .limit(20)
                .all()
            )
            seen_sale_ids = []
            results = []
            for item in items:
                if item.sale_id in seen_sale_ids:
                    continue
                seen_sale_ids.append(item.sale_id)
                results.append(self._refund_lookup_dict(item.sale))
            return results

        raise ConflictError("Provide a receipt number, receipt barcode, or product barcode to search.")

    def _refund_lookup_dict(self, sale):
        data = sale.to_dict()
        data["purchase_age"] = humanize_timedelta(sale.created_at)
        data["refund_eligible"] = sale.status in ("completed", "partially_refunded")
        data["items"] = [
            {**item.to_dict(), "refundable_quantity": item.quantity - item.refunded_quantity}
            for item in sale.items
        ]
        return data

    def create_refund(self, actor_id, sale_id, sale_item_id, quantity, reason, require_approval=False,
                       as_store_credit=False):
        sale = self.get_sale(sale_id)
        item = self.repo.get_sale_item(sale_item_id)
        if not item or item.sale_id != sale.id:
            raise NotFoundError("Sale item not found on this sale.")

        remaining = item.quantity - item.refunded_quantity
        if quantity > remaining:
            raise ConflictError(f"Cannot refund {quantity} units; only {remaining} remain refundable.")

        unit_refund_value = (item.line_total / item.quantity) if item.quantity else Decimal("0")
        refund_amount = Decimal(str(unit_refund_value)) * quantity

        if require_approval:
            refund = self.repo.add_refund(
                sale_id=sale.id, sale_item_id=item.id, quantity=quantity,
                amount=refund_amount, reason=reason, processed_by_id=actor_id, status="pending",
            )
            self.audit_service.log(actor_id, "sale.refund_requested", "sale", sale.id,
                                    details={"sale_item_id": item.id, "quantity": quantity})
            return refund

        item.refunded_quantity += quantity
        db.session.commit()

        self.inventory_service.restore_for_refund(actor_id, item.product_id, quantity, sale.id)

        refund = self.repo.add_refund(
            sale_id=sale.id, sale_item_id=item.id, quantity=quantity,
            amount=refund_amount, reason=reason, processed_by_id=actor_id, status="completed",
        )

        fully_refunded = all(i.refunded_quantity >= i.quantity for i in sale.items)
        sale.status = "refunded" if fully_refunded else "partially_refunded"
        db.session.commit()

        self.audit_service.log(actor_id, "sale.refund", "sale", sale.id,
                                details={"sale_item_id": item.id, "quantity": quantity})

        if as_store_credit:
            self._issue_store_credit(actor_id, sale, refund_amount, refund.id)

        self._print_refund_receipt(refund)
        return refund

    def _issue_store_credit(self, actor_id, sale, amount, refund_id):
        if not sale.customer_id:
            raise ConflictError("Store credit requires the sale to have a linked customer.")
        from app.services.gift_card_service import GiftCardService
        GiftCardService().issue_store_credit_for_refund(actor_id, sale.customer_id, amount, refund_id)

    def approve_refund(self, actor_id, refund_id, as_store_credit=False):
        from app.models.refund import Refund
        refund = Refund.query.get(refund_id)
        if not refund:
            raise NotFoundError("Refund request not found.")
        if refund.status != "pending":
            raise ConflictError(f"This refund is already '{refund.status}'.")

        item = refund.sale_item
        item.refunded_quantity += refund.quantity
        refund.status = "completed"
        db.session.commit()

        self.inventory_service.restore_for_refund(actor_id, item.product_id, refund.quantity, refund.sale_id)

        sale = refund.sale
        fully_refunded = all(i.refunded_quantity >= i.quantity for i in sale.items)
        sale.status = "refunded" if fully_refunded else "partially_refunded"
        db.session.commit()

        self.audit_service.log(actor_id, "sale.refund_approved", "refund", refund.id)

        if as_store_credit:
            self._issue_store_credit(actor_id, sale, refund.amount, refund.id)

        self._print_refund_receipt(refund)
        return refund

    def reject_refund(self, actor_id, refund_id, reason=None):
        from app.models.refund import Refund
        refund = Refund.query.get(refund_id)
        if not refund:
            raise NotFoundError("Refund request not found.")
        if refund.status != "pending":
            raise ConflictError(f"This refund is already '{refund.status}'.")

        refund.status = "rejected"
        if reason:
            refund.reason = f"{refund.reason or ''} [Rejected: {reason}]".strip()
        db.session.commit()

        self.audit_service.log(actor_id, "sale.refund_rejected", "refund", refund.id, details={"reason": reason})
        return refund

    def refund_history(self):
        from app.models.refund import Refund
        return Refund.query.order_by(Refund.created_at.desc())

    def verify_receipt(self, verification_code):
        """Public-safe receipt lookup: only the minimal info needed to confirm authenticity —
        no cashier/customer PII beyond what's already printed on the physical receipt."""
        from app.models.sale import Sale
        sale = Sale.query.filter_by(verification_code=verification_code).first()
        if not sale:
            raise NotFoundError("No receipt found for this verification code.")

        from app.services.settings_service import SettingsService
        settings = SettingsService().get_all()

        return {
            "valid": True,
            "receipt_number": sale.receipt_number,
            "status": sale.status,
            "store_name": settings.get("business_name"),
            "purchase_date": sale.created_at.isoformat() if sale.created_at else None,
            "total_amount": float(sale.total_amount),
            "payment_methods": [p.method for p in sale.payments],
            "items": [
                {
                    "product_name": item.product.name if item.product else None,
                    "variant_name": item.variant.name if item.variant else None,
                    "quantity": item.quantity,
                }
                for item in sale.items
            ],
        }

    def get_timeline(self, sale_id):
        """Chronological event timeline for a sale — creation, discounts, payments,
        printing, refunds, void — all sourced from the audit log for this entity."""
        from app.services.audit_service import AuditService
        entries = AuditService().get_for_entity("sale", sale_id).all()
        return [e.to_dict() for e in entries]

    def _print_refund_receipt(self, refund):
        try:
            from app.services.printer_service import PrinterService
            PrinterService().print_receipt(refund.sale)
        except Exception:
            pass

    def _broadcast_sale(self, sale):
        try:
            from app.websocket.events import emit_new_sale
            emit_new_sale(sale)
        except Exception:
            pass
