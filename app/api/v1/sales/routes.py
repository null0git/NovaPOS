"""Sales/checkout endpoints."""
from flask import request, Response
from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

from app.core.middleware.auth_middleware import current_user_id
from app.core.security.permissions import permission_required
from app.core.utils.pagination import paginate_query
from app.core.utils.filters import apply_search
from app.core.utils.response import success_response
from app.models.sale import Sale
from app.schemas.sales_schema import SaleCreateSchema
from app.services.sales_service import SalesService
from app.services.receipt_service import ReceiptService

blp = Blueprint("sales", __name__, url_prefix="/api/v1/sales", description="Sales / checkout")


@blp.route("")
class SalesListResource(MethodView):
    @jwt_required()
    @permission_required("sales.view", "sales.manage")
    def get(self):
        items, meta = paginate_query(SalesService().list_sales())
        return success_response([s.to_dict() for s in items], meta=meta)

    @jwt_required()
    @permission_required("sales.create", "sales.manage")
    @blp.arguments(SaleCreateSchema)
    def post(self, data):
        sale = SalesService().create_sale(
            cashier_id=current_user_id(),
            items_data=data["items"],
            payments_data=data["payments"],
            customer_id=data.get("customer_id"),
            discount_amount=data.get("discount_amount", 0),
            discount_reason=data.get("discount_reason"),
        )
        return success_response(sale.to_dict(), "Sale completed", 201)


@blp.route("/search")
class SalesSearchResource(MethodView):
    @jwt_required()
    @permission_required("sales.view", "sales.manage")
    def get(self):
        """Receipt history search: by receipt number, customer, cashier, date range, payment method."""
        query = Sale.query
        receipt_number = request.args.get("receipt_number")
        customer_id = request.args.get("customer_id", type=int)
        cashier_id = request.args.get("cashier_id", type=int)
        payment_method = request.args.get("payment_method")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        if receipt_number:
            query = query.filter(Sale.receipt_number.ilike(f"%{receipt_number}%"))
        if customer_id:
            query = query.filter(Sale.customer_id == customer_id)
        if cashier_id:
            query = query.filter(Sale.cashier_id == cashier_id)
        if start_date:
            query = query.filter(Sale.created_at >= start_date)
        if end_date:
            query = query.filter(Sale.created_at <= end_date)
        if payment_method:
            from app.models.payment import Payment
            query = query.join(Payment).filter(Payment.method == payment_method)

        query = query.order_by(Sale.created_at.desc())
        items, meta = paginate_query(query)
        return success_response([s.to_dict() for s in items], meta=meta)


@blp.route("/<int:sale_id>")
class SaleDetailResource(MethodView):
    @jwt_required()
    @permission_required("sales.view", "sales.manage")
    def get(self, sale_id):
        sale = SalesService().get_sale(sale_id)
        return success_response(sale.to_dict())


@blp.route("/receipt/<string:receipt_number>")
class SaleByReceiptResource(MethodView):
    @jwt_required()
    @permission_required("sales.view", "sales.manage")
    def get(self, receipt_number):
        sale = SalesService().get_by_receipt(receipt_number)
        return success_response(sale.to_dict())


@blp.route("/<int:sale_id>/receipt-text")
class SaleReceiptTextResource(MethodView):
    @jwt_required()
    @permission_required("sales.view", "sales.manage")
    def get(self, sale_id):
        from app.services.settings_service import SettingsService
        sale = SalesService().get_sale(sale_id)
        settings = SettingsService().get_all()
        width = request.args.get("paper_width_mm", settings.get("receipt_paper_width_mm", 80), type=int)
        text = ReceiptService().get_receipt_text(
            sale, business_name=settings.get("business_name"), paper_width_mm=width,
            refund_policy=settings.get("refund_policy_text"), footer_text=settings.get("receipt_footer"),
        )
        return Response(text, mimetype="text/plain")


@blp.route("/<int:sale_id>/receipt-pdf")
class SaleReceiptPDFResource(MethodView):
    @jwt_required()
    @permission_required("sales.view", "sales.manage")
    def get(self, sale_id):
        from app.services.pdf_service import ReceiptPDFService
        from app.services.settings_service import SettingsService
        sale = SalesService().get_sale(sale_id)
        settings = SettingsService().get_all()
        pdf_bytes = ReceiptPDFService().generate_pdf(
            sale, business_name=settings.get("business_name"), footer_text=settings.get("receipt_footer"),
            refund_policy=settings.get("refund_policy_text"),
        )
        return Response(
            pdf_bytes, mimetype="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="receipt_{sale.receipt_number}.pdf"'},
        )


@blp.route("/<int:sale_id>/timeline")
class SaleTimelineResource(MethodView):
    @jwt_required()
    @permission_required("sales.view", "sales.manage")
    def get(self, sale_id):
        timeline = SalesService().get_timeline(sale_id)
        return success_response(timeline)


@blp.route("/<int:sale_id>/void")
class SaleVoidResource(MethodView):
    @jwt_required()
    @permission_required("sales.manage")
    def post(self, sale_id):
        reason = (request.get_json(silent=True) or {}).get("reason", "Voided by staff")
        sale = SalesService().void_sale(current_user_id(), sale_id, reason)
        return success_response(sale.to_dict(), "Sale voided")


@blp.route("/verify/<string:code>")
class SaleVerifyResource(MethodView):
    @blp.doc(security=[])
    def get(self, code):
        """Public receipt verification — no auth. Customers/staff can confirm a
        receipt is genuine by its verification code (printed as text + QR)."""
        sale = SalesService().verify_receipt(code)
        return success_response(sale)


@blp.route("/<int:sale_id>/print")
class SalePrintResource(MethodView):
    @jwt_required()
    @permission_required("sales.create", "sales.manage")
    def post(self, sale_id):
        from app.services.printer_service import PrinterService
        printer_id = (request.get_json(silent=True) or {}).get("printer_id")
        sale = SalesService().get_sale(sale_id)
        result = PrinterService().print_receipt(sale, printer_id)
        return success_response(result, "Print job sent")
