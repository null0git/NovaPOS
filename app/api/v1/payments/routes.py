"""Payment records (payments are created as part of checkout; this exposes read access)."""
from flask import request
from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

from app.core.security.permissions import permission_required
from app.core.utils.response import success_response, error_response
from app.services.sales_service import SalesService
from app.services.checkout_session_service import CheckoutSessionService

blp = Blueprint("payments", __name__, url_prefix="/api/v1/payments", description="Payment records")


@blp.route("/sale/<int:sale_id>")
class PaymentsForSaleResource(MethodView):
    @jwt_required()
    @permission_required("sales.view", "sales.manage")
    def get(self, sale_id):
        sale = SalesService().get_sale(sale_id)
        return success_response([p.to_dict() for p in sale.payments])


@blp.route("/chapa/webhook")
class ChapaWebhookResource(MethodView):
    @blp.doc(security=[])
    def post(self):
        """Chapa calls this after a customer completes (or fails) a hosted checkout payment."""
        raw_body = request.get_data()
        signature = request.headers.get("Chapa-Signature") or request.headers.get("x-chapa-signature")
        payload = request.get_json(silent=True) or {}
        try:
            sale = CheckoutSessionService().handle_chapa_webhook(raw_body, signature, payload)
            return success_response({"sale_id": sale.id, "status": sale.status}, "Webhook processed")
        except Exception as exc:
            # Chapa expects a 200 to stop retrying malformed/duplicate webhooks once we've
            # logged the issue; genuine transient errors still surface via SystemLog.
            from app.services.system_log_service import SystemLogService
            SystemLogService().log("payments", f"Chapa webhook error: {exc}", severity="error")
            return error_response(str(exc), 400)
