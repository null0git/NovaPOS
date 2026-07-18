"""Reporting endpoints: sales, profit, top products, inventory."""
from flask import request
from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

from app.core.security.permissions import permission_required
from app.core.utils.response import success_response, error_response
from app.services.report_service import ReportService

blp = Blueprint("reports", __name__, url_prefix="/api/v1/reports", description="Business reports")


def _period_args():
    period = request.args.get("period", "today")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    return period, start_date, end_date


@blp.route("/sales")
class SalesReportResource(MethodView):
    @jwt_required()
    @permission_required("reports.view")
    def get(self):
        period, start, end = _period_args()
        return success_response(ReportService().sales_report(period, start, end))


@blp.route("/profit")
class ProfitReportResource(MethodView):
    @jwt_required()
    @permission_required("reports.view")
    def get(self):
        period, start, end = _period_args()
        return success_response(ReportService().profit_report(period, start, end))


@blp.route("/top-products")
class TopProductsReportResource(MethodView):
    @jwt_required()
    @permission_required("reports.view")
    def get(self):
        period, start, end = _period_args()
        limit = request.args.get("limit", 10, type=int)
        return success_response(ReportService().top_products(period, start, end, limit))


@blp.route("/inventory")
class InventoryReportResource(MethodView):
    @jwt_required()
    @permission_required("reports.view")
    def get(self):
        return success_response(ReportService().inventory_report())


@blp.route("/daily-closing")
class DailyClosingReportResource(MethodView):
    @jwt_required()
    @permission_required("reports.view")
    def get(self):
        from datetime import datetime
        date_str = request.args.get("date")
        date = datetime.fromisoformat(date_str) if date_str else None
        return success_response(ReportService().daily_closing_report(date))


@blp.route("/daily-closing/pdf")
class DailyClosingReportPDFResource(MethodView):
    @jwt_required()
    @permission_required("reports.view")
    def get(self):
        from datetime import datetime
        from flask import Response
        from app.services.closing_report_pdf_service import ClosingReportPDFService
        date_str = request.args.get("date")
        date = datetime.fromisoformat(date_str) if date_str else None
        report = ReportService().daily_closing_report(date)
        pdf_bytes = ClosingReportPDFService().generate_pdf(report)
        return Response(pdf_bytes, mimetype="application/pdf", headers={
            "Content-Disposition": f'attachment; filename="closing_report_{report["date"]}.pdf"'
        })


@blp.route("/product-analytics")
class ProductAnalyticsResource(MethodView):
    @jwt_required()
    @permission_required("reports.view")
    def get(self):
        period = request.args.get("period", "month")
        limit = request.args.get("limit", 10, type=int)
        return success_response(ReportService().product_analytics(period, limit))


@blp.route("/calendar")
class BusinessCalendarResource(MethodView):
    @jwt_required()
    @permission_required("reports.view")
    def get(self):
        year = request.args.get("year", type=int)
        month = request.args.get("month", type=int)
        if not year or not month:
            return error_response("Provide ?year=YYYY&month=MM.", 422)
        return success_response(ReportService().business_calendar(year, month))
