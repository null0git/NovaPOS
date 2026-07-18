"""Refund processing endpoints: search, request/approve/reject workflow, and history."""
from flask import request
from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

from app.core.middleware.auth_middleware import current_user_id
from app.core.security.permissions import permission_required
from app.core.utils.pagination import paginate_query
from app.core.utils.response import success_response
from app.schemas.sales_schema import RefundCreateSchema
from app.services.sales_service import SalesService

blp = Blueprint("refunds", __name__, url_prefix="/api/v1/refunds", description="Refunds")


@blp.route("/search")
class RefundSearchResource(MethodView):
    @jwt_required()
    @permission_required("refunds.create", "refunds.manage")
    def get(self):
        """Find a sale eligible for refund via receipt number/barcode or a scanned product barcode."""
        results = SalesService().search_for_refund(
            receipt_number=request.args.get("receipt_number"),
            receipt_barcode=request.args.get("receipt_barcode"),
            product_barcode=request.args.get("product_barcode"),
        )
        return success_response(results)


@blp.route("/history")
class RefundHistoryResource(MethodView):
    @jwt_required()
    @permission_required("refunds.manage")
    def get(self):
        items, meta = paginate_query(SalesService().refund_history())
        return success_response([r.to_dict() for r in items], meta=meta)


@blp.route("/sale/<int:sale_id>")
class RefundCreateResource(MethodView):
    @jwt_required()
    @permission_required("refunds.create", "refunds.manage")
    @blp.arguments(RefundCreateSchema)
    def post(self, data, sale_id):
        """Direct refund (immediately completed). Use /request for an approval-gated refund."""
        refund = SalesService().create_refund(
            current_user_id(), sale_id, data["sale_item_id"], data["quantity"], data["reason"],
            as_store_credit=data.get("as_store_credit", False),
        )
        return success_response(refund.to_dict(), "Refund processed", 201)


@blp.route("/sale/<int:sale_id>/request")
class RefundRequestResource(MethodView):
    @jwt_required()
    @permission_required("refunds.create", "refunds.manage")
    @blp.arguments(RefundCreateSchema)
    def post(self, data, sale_id):
        """Create a refund request awaiting manager approval (stock/status untouched until approved)."""
        refund = SalesService().create_refund(
            current_user_id(), sale_id, data["sale_item_id"], data["quantity"], data["reason"],
            require_approval=True,
        )
        return success_response(refund.to_dict(), "Refund request submitted for approval", 201)


@blp.route("/<int:refund_id>/approve")
class RefundApproveResource(MethodView):
    @jwt_required()
    @permission_required("refunds.manage")
    def post(self, refund_id):
        as_store_credit = (request.get_json(silent=True) or {}).get("as_store_credit", False)
        refund = SalesService().approve_refund(current_user_id(), refund_id, as_store_credit=as_store_credit)
        return success_response(refund.to_dict(), "Refund approved and processed")


@blp.route("/<int:refund_id>/reject")
class RefundRejectResource(MethodView):
    @jwt_required()
    @permission_required("refunds.manage")
    def post(self, refund_id):
        reason = (request.get_json(silent=True) or {}).get("reason")
        refund = SalesService().reject_refund(current_user_id(), refund_id, reason)
        return success_response(refund.to_dict(), "Refund rejected")


@blp.route("/sale/<int:sale_id>/list")
class RefundsForSaleResource(MethodView):
    @jwt_required()
    @permission_required("refunds.create", "refunds.manage", "sales.view")
    def get(self, sale_id):
        sale = SalesService().get_sale(sale_id)
        return success_response([r.to_dict() for r in sale.refunds])
