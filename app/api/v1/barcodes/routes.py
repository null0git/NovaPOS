"""
Advanced barcode management: register scanned manufacturer barcodes, or
bulk-generate internal barcodes for a batch (e.g. 100 units of 5L Cooking
Oil) and print them as a PDF sheet of Code128 labels.
"""
from flask import request, Response
from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

from app.core.middleware.auth_middleware import current_user_id
from app.core.security.permissions import permission_required
from app.core.utils.response import success_response
from app.schemas.barcode_schema import (
    BulkBarcodeGenerateSchema, ManufacturerBarcodeScanSchema, LabelPrintSchema,
)
from app.services.barcode_service import BarcodeService
from app.services.product_service import ProductService
from app.services.label_service import LabelService
from app.services.settings_service import SettingsService

blp = Blueprint("barcodes", __name__, url_prefix="/api/v1/products/<int:product_id>/barcodes",
                description="Advanced barcode management (manufacturer scans + bulk internal generation)")


@blp.route("/scan")
class ManufacturerBarcodeScanResource(MethodView):
    @jwt_required()
    @permission_required("products.manage")
    @blp.arguments(ManufacturerBarcodeScanSchema)
    def post(self, data, product_id):
        product = ProductService().get_product(product_id)
        product = BarcodeService().register_manufacturer_barcode(product, data["code"])
        return success_response(product.to_dict(), "Manufacturer barcode registered")


@blp.route("/bulk-generate")
class BulkGenerateResource(MethodView):
    @jwt_required()
    @permission_required("products.manage", "inventory.manage")
    @blp.arguments(BulkBarcodeGenerateSchema)
    def post(self, data, product_id):
        entries = BarcodeService().bulk_generate(
            current_user_id(), product_id, data["quantity"], data.get("batch_label")
        )
        return success_response([e.to_dict() for e in entries], f"{len(entries)} barcodes generated", 201)


@blp.route("")
class GeneratedBarcodesListResource(MethodView):
    @jwt_required()
    @permission_required("products.manage", "inventory.manage")
    def get(self, product_id):
        entries = BarcodeService().list_generated_for_product(product_id)
        return success_response([e.to_dict() for e in entries])


@blp.route("/print-labels")
class PrintLabelsResource(MethodView):
    @jwt_required()
    @permission_required("products.manage", "inventory.manage")
    @blp.arguments(LabelPrintSchema)
    def post(self, data, product_id):
        product = ProductService().get_product(product_id)
        from app.models.generated_barcode import GeneratedBarcode
        entries = GeneratedBarcode.query.filter(
            GeneratedBarcode.id.in_(data["barcode_ids"]), GeneratedBarcode.product_id == product_id
        ).all()

        settings = SettingsService().get_all()
        pdf_bytes = LabelService().generate_label_sheet_pdf(
            entries, product, label_size=data["label_size"],
            store_name=settings.get("business_name"),
            show_price=data["show_price"], show_sku=data["show_sku"],
        )
        BarcodeService().mark_printed(data["barcode_ids"])

        return Response(
            pdf_bytes, mimetype="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="labels_{product.sku}.pdf"'},
        )
