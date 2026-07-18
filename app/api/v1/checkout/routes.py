"""
Customer-display checkout flow endpoints: start a session, push live cart
updates, let the customer pick a payment method, and confirm/finalize.
"""
from flask import request
from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

from app.core.middleware.auth_middleware import current_user_id
from app.core.security.permissions import permission_required
from app.core.utils.response import success_response
from app.schemas.checkout_schema import (
    CheckoutStartSchema, CheckoutSetItemsSchema, CustomerPaymentMethodSchema,
    ConfirmCashSchema, ConfirmOfflineSchema,
)
from app.services.checkout_session_service import CheckoutSessionService

blp = Blueprint("checkout", __name__, url_prefix="/api/v1/checkout",
                description="Customer-display checkout sessions (live cart + payment selection)")


@blp.route("/drafts")
class CheckoutDraftsListResource(MethodView):
    @jwt_required()
    @permission_required("sales.create", "sales.manage")
    def get(self):
        """Recoverable unfinished carts (survives browser crash/power outage/network drop)."""
        from flask import request
        mine_only = request.args.get("mine_only", "true").lower() == "true"
        cashier_id = current_user_id() if mine_only else None
        drafts = CheckoutSessionService().list_drafts(cashier_id)
        return success_response([d.to_dict() for d in drafts])


@blp.route("/start")
class CheckoutStartResource(MethodView):
    @jwt_required()
    @permission_required("sales.create", "sales.manage")
    @blp.arguments(CheckoutStartSchema)
    def post(self, data):
        sale = CheckoutSessionService().start_session(current_user_id(), **data)
        return success_response(sale.to_dict(), "Checkout session started", 201)


@blp.route("/<int:sale_id>/items")
class CheckoutItemsResource(MethodView):
    @jwt_required()
    @permission_required("sales.create", "sales.manage")
    @blp.arguments(CheckoutSetItemsSchema)
    def put(self, data, sale_id):
        sale = CheckoutSessionService().set_items(
            current_user_id(), sale_id, data["items"],
            data.get("cart_discount_amount", 0), data.get("cart_discount_reason"),
        )
        return success_response(sale.to_dict(), "Cart updated")


@blp.route("/<int:sale_id>/customer-payment-method")
class CheckoutCustomerPaymentMethodResource(MethodView):
    @blp.doc(security=[])
    def post(self, sale_id):
        """Called by the (unauthenticated) customer display when the shopper picks a method."""
        from app.schemas.checkout_schema import CustomerPaymentMethodSchema as Schema_
        data = Schema_().load(request.get_json(silent=True) or {})
        result = CheckoutSessionService().select_payment_method(
            sale_id, data["method"],
            customer_email=data.get("customer_email"), customer_name=data.get("customer_name"),
            callback_url=request.url_root.rstrip("/") + "/api/v1/payments/chapa/webhook",
            return_url=request.url_root,
        )
        return success_response(result, "Payment method recorded")


@blp.route("/<int:sale_id>/confirm-cash")
class CheckoutConfirmCashResource(MethodView):
    @jwt_required()
    @permission_required("sales.create", "sales.manage")
    @blp.arguments(ConfirmCashSchema)
    def post(self, data, sale_id):
        sale = CheckoutSessionService().confirm_cash(
            current_user_id(), sale_id, data.get("amount_tendered")
        )
        return success_response(sale.to_dict(), "Cash payment confirmed; sale completed")


@blp.route("/<int:sale_id>/reject-cash")
class CheckoutRejectCashResource(MethodView):
    @jwt_required()
    @permission_required("sales.create", "sales.manage")
    def post(self, sale_id):
        reason = (request.get_json(silent=True) or {}).get("reason", "Cash rejected by cashier")
        sale = CheckoutSessionService().reject_cash(current_user_id(), sale_id, reason)
        return success_response(sale.to_dict(), "Cash payment rejected")


@blp.route("/<int:sale_id>/confirm-offline")
class CheckoutConfirmOfflineResource(MethodView):
    @jwt_required()
    @permission_required("sales.create", "sales.manage")
    @blp.arguments(ConfirmOfflineSchema)
    def post(self, data, sale_id):
        sale = CheckoutSessionService().confirm_offline(
            current_user_id(), sale_id, data.get("reference")
        )
        return success_response(sale.to_dict(), "Offline payment confirmed; sale completed")


@blp.route("/<int:sale_id>/cancel")
class CheckoutCancelResource(MethodView):
    @jwt_required()
    @permission_required("sales.create", "sales.manage")
    def post(self, sale_id):
        reason = (request.get_json(silent=True) or {}).get("reason", "Cancelled")
        sale = CheckoutSessionService().cancel_session(current_user_id(), sale_id, reason)
        return success_response(sale.to_dict(), "Checkout session cancelled")
