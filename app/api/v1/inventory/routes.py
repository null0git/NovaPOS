"""Inventory endpoints: current stock, restock, adjustments, history, low-stock alerts."""
from flask import Response
from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

from app.core.middleware.auth_middleware import current_user_id
from app.core.security.permissions import permission_required
from app.core.utils.pagination import paginate_query
from app.core.utils.response import success_response
from app.schemas.inventory_schema import (
    InventoryAdjustSchema, InventoryRestockSchema, InventoryThresholdSchema,
)
from app.services.inventory_service import InventoryService

blp = Blueprint("inventory", __name__, url_prefix="/api/v1/inventory", description="Inventory management")


@blp.route("/export.csv")
class InventoryExportCSVResource(MethodView):
    @jwt_required()
    @permission_required("inventory.manage", "inventory.view", "reports.view")
    def get(self):
        from app.services.import_export_service import ImportExportService
        data = ImportExportService().export_inventory_csv()
        return Response(data, mimetype="text/csv",
                         headers={"Content-Disposition": 'attachment; filename="inventory.csv"'})


@blp.route("")
class InventoryListResource(MethodView):
    @jwt_required()
    @permission_required("inventory.view", "inventory.manage")
    def get(self):
        items, meta = paginate_query(InventoryService().list_all())
        return success_response([i.to_dict() for i in items], meta=meta)


@blp.route("/low-stock")
class LowStockResource(MethodView):
    @jwt_required()
    @permission_required("inventory.view", "inventory.manage")
    def get(self):
        items = InventoryService().list_low_stock().all()
        return success_response([i.to_dict() for i in items])


@blp.route("/product/<int:product_id>")
class InventoryForProductResource(MethodView):
    @jwt_required()
    @permission_required("inventory.view", "inventory.manage")
    def get(self, product_id):
        inventory = InventoryService().get_for_product(product_id)
        return success_response(inventory.to_dict())


@blp.route("/product/<int:product_id>/restock")
class InventoryRestockResource(MethodView):
    @jwt_required()
    @permission_required("inventory.manage")
    @blp.arguments(InventoryRestockSchema)
    def post(self, data, product_id):
        inventory = InventoryService().restock(current_user_id(), product_id, data["quantity"], data["reason"])
        return success_response(inventory.to_dict(), "Stock restocked")


@blp.route("/product/<int:product_id>/adjust")
class InventoryAdjustResource(MethodView):
    @jwt_required()
    @permission_required("inventory.manage")
    @blp.arguments(InventoryAdjustSchema)
    def post(self, data, product_id):
        inventory = InventoryService().adjust(
            current_user_id(), product_id, data["quantity_change"], data["reason"]
        )
        return success_response(inventory.to_dict(), "Stock adjusted")


@blp.route("/product/<int:product_id>/thresholds")
class InventoryThresholdsResource(MethodView):
    @jwt_required()
    @permission_required("inventory.manage")
    @blp.arguments(InventoryThresholdSchema)
    def patch(self, data, product_id):
        inventory = InventoryService().update_thresholds(current_user_id(), product_id, **data)
        return success_response(inventory.to_dict(), "Thresholds updated")


@blp.route("/product/<int:product_id>/history")
class InventoryHistoryResource(MethodView):
    @jwt_required()
    @permission_required("inventory.view", "inventory.manage")
    def get(self, product_id):
        items, meta = paginate_query(InventoryService().get_history(product_id))
        return success_response([h.to_dict() for h in items], meta=meta)
