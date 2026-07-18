"""
Business logic for the customer-display checkout flow:

  cashier starts session -> items pushed live to customer display ->
  customer picks a payment method on the display -> cashier confirms
  (cash/offline) or Chapa webhook confirms -> sale finalized (stock
  deducted, payment recorded, receipt printed, audit logged).

Unlike SalesService.create_sale (a single atomic call for direct/offline
checkout), this flow holds a "draft" Sale open across multiple requests.
Stock is validated and deducted only at finalization time.
"""
import base64
from decimal import Decimal

from app.core.middleware.error_handler import ConflictError, NotFoundError, AuthError
from app.core.utils.qr_code import generate_qr_bytes
from app.extensions import db
from app.repositories.sales_repository import SalesRepository
from app.services.audit_service import AuditService
from app.services.chapa_service import ChapaService
from app.services.inventory_service import InventoryService
from app.services.pricing_helper import resolve_sale_line
from app.services.receipt_service import ReceiptService

DRAFT_STATUSES = ("draft",)


class CheckoutSessionService:
    def __init__(self):
        self.repo = SalesRepository()
        self.inventory_service = InventoryService()
        self.receipt_service = ReceiptService()
        self.audit_service = AuditService()
        self.chapa_service = ChapaService()

    def get_draft_sale(self, sale_id):
        sale = self.repo.get_by_id(sale_id)
        if not sale:
            raise NotFoundError("Checkout session not found.")
        if sale.status not in DRAFT_STATUSES:
            raise ConflictError(f"This checkout session is already '{sale.status}'.")
        return sale

    def list_drafts(self, cashier_id=None):
        """List saved/unfinished carts — survives browser crash, power outage, or network
        drop since drafts are persisted in the database the moment they're created/updated."""
        from app.models.sale import Sale
        query = Sale.query.filter_by(status="draft")
        if cashier_id:
            query = query.filter_by(cashier_id=cashier_id)
        return query.order_by(Sale.updated_at.desc())

    def start_session(self, cashier_id, terminal_id=None, customer_id=None):
        sale = self.repo.create(
            receipt_number=self.receipt_service.generate_receipt_number(),
            verification_code=self.receipt_service.generate_verification_code(),
            subtotal=0, tax_amount=0, discount_amount=0, total_amount=0,
            status="draft", cashier_id=cashier_id, customer_id=customer_id, terminal_id=terminal_id,
        )
        self._broadcast_checkout(sale)
        return sale

    def set_items(self, actor_id, sale_id, items_data, cart_discount_amount=0, cart_discount_reason=None):
        sale = self.get_draft_sale(sale_id)

        for item in list(sale.items):
            db.session.delete(item)
        db.session.flush()

        subtotal = Decimal("0")
        tax_total = Decimal("0")
        for item_data in items_data:
            line = resolve_sale_line(item_data)
            subtotal += (line.unit_price * line.quantity) - line.discount_amount
            tax_total += line.line_total - ((line.unit_price * line.quantity) - line.discount_amount)

            sale_item = self.repo.add_item(
                sale_id=sale.id, product_id=line.product.id,
                variant_id=line.variant.id if line.variant else None,
                unit_id=line.unit.id if line.unit else None,
                quantity=line.quantity, unit_price=line.unit_price, tax_rate=line.tax_rate,
                discount_amount=line.discount_amount, line_total=line.line_total,
            )
            db.session.flush()

            if line.discount_amount > 0:
                self._log_discount(sale.id, sale_item.id, item_data, line, actor_id)

        cart_discount_amount = Decimal(str(cart_discount_amount or 0))
        total_amount = subtotal + tax_total - cart_discount_amount
        if total_amount < 0:
            raise ConflictError("Cart discount cannot exceed the cart subtotal.")

        sale.subtotal = subtotal
        sale.tax_amount = tax_total
        sale.discount_amount = cart_discount_amount
        sale.total_amount = total_amount
        db.session.commit()

        if cart_discount_amount > 0:
            from app.repositories.discount_repository import DiscountRepository
            DiscountRepository().create(
                sale_id=sale.id, sale_item_id=None, discount_type="fixed", scope="cart",
                original_amount=subtotal + tax_total, discount_amount=cart_discount_amount,
                reason=cart_discount_reason, cashier_id=actor_id,
            )

        self._broadcast_checkout(sale)
        return sale

    def _log_discount(self, sale_id, sale_item_id, item_data, line, actor_id):
        from app.repositories.discount_repository import DiscountRepository
        DiscountRepository().create(
            sale_id=sale_id, sale_item_id=sale_item_id,
            discount_type=item_data.get("discount_type", "fixed"), scope="product",
            original_amount=line.unit_price * line.quantity, discount_amount=line.discount_amount,
            reason=item_data.get("discount_reason"), cashier_id=actor_id,
        )

    def select_payment_method(self, sale_id, method, customer_email=None, customer_name=None,
                               callback_url=None, return_url=None):
        sale = self.get_draft_sale(sale_id)
        if method not in ("cash", "chapa", "offline"):
            raise ConflictError(f"Unsupported payment method '{method}'.")

        sale.customer_payment_method = method
        db.session.commit()

        result = {"sale": sale.to_dict(), "method": method}

        if method == "chapa":
            tx_ref, checkout_url = self.chapa_service.initialize_session(
                sale, callback_url=callback_url, return_url=return_url,
                customer_email=customer_email, customer_name=customer_name,
            )
            self.repo.add_payment(
                sale_id=sale.id, method="chapa", amount=sale.total_amount,
                status="pending", external_reference=tx_ref, checkout_url=checkout_url,
            )
            db.session.commit()
            qr_bytes = generate_qr_bytes(checkout_url)
            result["checkout_url"] = checkout_url
            result["qr_code_base64"] = base64.b64encode(qr_bytes).decode()
            result["instructions"] = "Scan the QR code or open the payment link to complete payment."
        elif method == "cash":
            result["instructions"] = "Please hand the cash to the cashier."
        else:
            result["instructions"] = "Please follow the cashier's instructions to complete payment."

        self._broadcast_payment_selected(sale, method, result)
        return result

    def confirm_cash(self, actor_id, sale_id, amount_tendered=None):
        sale = self.get_draft_sale(sale_id)
        return self._finalize(actor_id, sale, method="cash", amount=sale.total_amount,
                               amount_tendered=amount_tendered)

    def reject_cash(self, actor_id, sale_id, reason="Cash rejected by cashier"):
        sale = self.get_draft_sale(sale_id)
        sale.customer_payment_method = None
        db.session.commit()
        self.audit_service.log(actor_id, "sale.reject_cash", "sale", sale.id, details={"reason": reason})
        self._broadcast_checkout(sale)
        return sale

    def confirm_offline(self, actor_id, sale_id, reference=None):
        sale = self.get_draft_sale(sale_id)
        return self._finalize(actor_id, sale, method="offline", amount=sale.total_amount, reference=reference)

    def cancel_session(self, actor_id, sale_id, reason="Cancelled"):
        sale = self.get_draft_sale(sale_id)
        sale.status = "voided"
        db.session.commit()
        self.audit_service.log(actor_id, "sale.cancel_draft", "sale", sale.id, details={"reason": reason})
        self._broadcast_checkout(sale, event="cancelled")
        return sale

    def handle_chapa_webhook(self, raw_body, signature_header, payload):
        if not self.chapa_service.verify_webhook_signature(raw_body, signature_header):
            raise AuthError("Invalid webhook signature.")

        tx_ref = payload.get("tx_ref") or (payload.get("data") or {}).get("tx_ref")
        if not tx_ref:
            raise ConflictError("Webhook payload missing tx_ref.")

        verification = self.chapa_service.verify_transaction(tx_ref)
        from app.models.payment import Payment
        payment = Payment.query.filter_by(external_reference=tx_ref).first()
        if not payment:
            raise NotFoundError("No payment session found for this transaction reference.")

        sale = payment.sale
        if sale.status == "completed":
            return sale  # already finalized; webhook may be retried by Chapa

        if verification.get("status") != "success":
            payment.status = "failed"
            payment.gateway_response = verification
            db.session.commit()
            return sale

        payment.status = "completed"
        payment.gateway_response = verification
        db.session.commit()

        return self._finalize(None, sale, method="chapa", amount=payment.amount, skip_payment_creation=True)

    def _finalize(self, actor_id, sale, method, amount, amount_tendered=None, reference=None,
                  skip_payment_creation=False):
        actor_id = actor_id or sale.cashier_id

        for item in sale.items:
            product = item.product
            if item.variant_id:
                available = item.variant.stock_quantity if item.variant else 0
            else:
                available = product.inventory.quantity if product.inventory else 0
            if available < item.quantity:
                raise ConflictError(f"Insufficient stock for '{product.name}' to complete this sale.")

        for item in sale.items:
            if item.variant_id:
                from app.services.variant_service import VariantService
                VariantService().adjust_stock(actor_id, item.variant_id, -item.quantity,
                                               reason=f"Sale #{sale.id}")
            else:
                self.inventory_service.deduct_for_sale(actor_id, item.product_id, item.quantity, sale.id)

        if not skip_payment_creation:
            amount = Decimal(str(amount))
            change_due = None
            if method == "cash" and amount_tendered is not None:
                amount_tendered = Decimal(str(amount_tendered))
                if amount_tendered < amount:
                    raise ConflictError("Amount tendered is less than the sale total.")
                change_due = amount_tendered - amount
            self.repo.add_payment(
                sale_id=sale.id, method=method, amount=amount, amount_tendered=amount_tendered,
                change_due=change_due, reference=reference, status="completed",
            )

        sale.status = "completed"
        db.session.commit()

        self.audit_service.log(actor_id, "sale.complete", "sale", sale.id, details={"method": method})
        self._broadcast_payment_confirmed(sale)
        self._print_receipt(sale)
        return sale

    def _broadcast_checkout(self, sale, event="update"):
        try:
            from app.websocket.events import emit_checkout_update
            emit_checkout_update(sale)
        except Exception:
            pass

    def _broadcast_payment_selected(self, sale, method, result):
        try:
            from app.websocket.events import emit_customer_payment_selected
            emit_customer_payment_selected({"sale_id": sale.id, "method": method,
                                             "checkout_url": result.get("checkout_url")})
        except Exception:
            pass

    def _broadcast_payment_confirmed(self, sale):
        try:
            from app.websocket.events import emit_payment_confirmed
            emit_payment_confirmed(sale)
        except Exception:
            pass

    def _print_receipt(self, sale):
        try:
            from app.services.printer_service import PrinterService
            PrinterService().print_receipt(sale)
        except Exception:
            pass
