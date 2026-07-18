"""Alternate selling-unit endpoints (e.g. Sugar sold as kg/500g/250g)."""
from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

from app.core.middleware.auth_middleware import current_user_id
from app.core.security.permissions import permission_required
from app.core.utils.response import success_response
from app.schemas.unit_schema import UnitCreateSchema, UnitUpdateSchema
from app.services.unit_service import UnitService

blp = Blueprint("units", __name__, url_prefix="/api/v1/products/<int:product_id>/units",
                description="Product alternate selling units")


@blp.route("")
class UnitsListResource(MethodView):
    @jwt_required()
    def get(self, product_id):
        units = UnitService().list_for_product(product_id)
        return success_response([u.to_dict() for u in units])

    @jwt_required()
    @permission_required("products.manage")
    @blp.arguments(UnitCreateSchema)
    def post(self, data, product_id):
        unit = UnitService().create_unit(current_user_id(), product_id, **data)
        return success_response(unit.to_dict(), "Unit created", 201)


@blp.route("/<int:unit_id>")
class UnitDetailResource(MethodView):
    @jwt_required()
    def get(self, product_id, unit_id):
        unit = UnitService().get_unit(unit_id)
        return success_response(unit.to_dict())

    @jwt_required()
    @permission_required("products.manage")
    @blp.arguments(UnitUpdateSchema)
    def patch(self, data, product_id, unit_id):
        unit = UnitService().update_unit(current_user_id(), unit_id, **data)
        return success_response(unit.to_dict(), "Unit updated")

    @jwt_required()
    @permission_required("products.manage")
    def delete(self, product_id, unit_id):
        UnitService().delete_unit(current_user_id(), unit_id)
        return success_response(None, "Unit deactivated")
