"""Product variant endpoints (e.g. Coca-Cola 330ml/500ml/1L)."""
from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

from app.core.middleware.auth_middleware import current_user_id
from app.core.security.permissions import permission_required
from app.core.utils.response import success_response
from app.schemas.variant_schema import VariantCreateSchema, VariantUpdateSchema, VariantStockAdjustSchema
from app.services.variant_service import VariantService

blp = Blueprint("variants", __name__, url_prefix="/api/v1/products/<int:product_id>/variants",
                description="Product variants")


@blp.route("")
class VariantsListResource(MethodView):
    @jwt_required()
    def get(self, product_id):
        variants = VariantService().list_for_product(product_id)
        return success_response([v.to_dict() for v in variants])

    @jwt_required()
    @permission_required("products.manage")
    @blp.arguments(VariantCreateSchema)
    def post(self, data, product_id):
        variant = VariantService().create_variant(current_user_id(), product_id, **data)
        return success_response(variant.to_dict(), "Variant created", 201)


@blp.route("/<int:variant_id>")
class VariantDetailResource(MethodView):
    @jwt_required()
    def get(self, product_id, variant_id):
        variant = VariantService().get_variant(variant_id)
        return success_response(variant.to_dict())

    @jwt_required()
    @permission_required("products.manage")
    @blp.arguments(VariantUpdateSchema)
    def patch(self, data, product_id, variant_id):
        variant = VariantService().update_variant(current_user_id(), variant_id, **data)
        return success_response(variant.to_dict(), "Variant updated")

    @jwt_required()
    @permission_required("products.manage")
    def delete(self, product_id, variant_id):
        VariantService().delete_variant(current_user_id(), variant_id)
        return success_response(None, "Variant deactivated")


@blp.route("/<int:variant_id>/stock")
class VariantStockResource(MethodView):
    @jwt_required()
    @permission_required("inventory.manage")
    @blp.arguments(VariantStockAdjustSchema)
    def post(self, data, product_id, variant_id):
        variant = VariantService().adjust_stock(
            current_user_id(), variant_id, data["quantity_change"], data["reason"]
        )
        return success_response(variant.to_dict(), "Stock adjusted")
