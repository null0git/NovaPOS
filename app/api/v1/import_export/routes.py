"""Bulk product import (CSV/Excel) and export (CSV/Excel/JSON) endpoints."""
from flask import request, Response
from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

from app.core.middleware.auth_middleware import current_user_id
from app.core.security.permissions import permission_required
from app.core.utils.response import success_response, error_response
from app.services.import_export_service import ImportExportService

blp = Blueprint("import_export", __name__, url_prefix="/api/v1/products/bulk",
                description="Bulk product import/export")


@blp.route("/export.csv")
class ExportProductsCSVResource(MethodView):
    @jwt_required()
    @permission_required("products.manage", "reports.view")
    def get(self):
        data = ImportExportService().export_products_csv()
        return Response(data, mimetype="text/csv",
                         headers={"Content-Disposition": 'attachment; filename="products.csv"'})


@blp.route("/export.xlsx")
class ExportProductsXLSXResource(MethodView):
    @jwt_required()
    @permission_required("products.manage", "reports.view")
    def get(self):
        data = ImportExportService().export_products_xlsx()
        return Response(
            data, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": 'attachment; filename="products.xlsx"'},
        )


@blp.route("/export.json")
class ExportProductsJSONResource(MethodView):
    @jwt_required()
    @permission_required("products.manage", "reports.view")
    def get(self):
        data = ImportExportService().export_products_json()
        return Response(data, mimetype="application/json",
                         headers={"Content-Disposition": 'attachment; filename="products.json"'})


@blp.route("/import")
class ImportProductsResource(MethodView):
    @jwt_required()
    @permission_required("products.manage")
    def post(self):
        if "file" not in request.files:
            return error_response("No file part in the request.", 422)
        file_storage = request.files["file"]
        filename = file_storage.filename or ""
        file_bytes = file_storage.read()

        service = ImportExportService()
        if filename.endswith(".csv"):
            result = service.import_products_csv(current_user_id(), file_bytes)
        elif filename.endswith(".xlsx"):
            result = service.import_products_xlsx(current_user_id(), file_bytes)
        else:
            return error_response("Unsupported file type. Use .csv or .xlsx.", 422)

        return success_response(result, f"Import complete: {result['created']} created, "
                                         f"{result['updated']} updated, {len(result['errors'])} errors")
