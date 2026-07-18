"""Store branding (name, logo, contact info) and tax configuration endpoints."""
from flask import request
from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

from app.core.middleware.auth_middleware import current_user_id
from app.core.security.permissions import permission_required
from app.core.utils.response import success_response, error_response
from app.schemas.branding_schema import BrandingUpdateSchema, TaxConfigUpdateSchema
from app.services.branding_service import BrandingService

blp = Blueprint("branding", __name__, url_prefix="/api/v1/branding", description="Store branding & tax config")


@blp.route("")
class BrandingResource(MethodView):
    @blp.doc(security=[])
    def get(self):
        # Unauthenticated: the login page and customer display both need branding info.
        return success_response(BrandingService().get_branding())

    @jwt_required()
    @permission_required("settings.manage")
    @blp.arguments(BrandingUpdateSchema)
    def patch(self, data):
        branding = BrandingService().update_branding(current_user_id(), **data)
        return success_response(branding, "Branding updated")


@blp.route("/logo")
class BrandingLogoResource(MethodView):
    @jwt_required()
    @permission_required("settings.manage")
    def post(self):
        if "file" not in request.files:
            return error_response("No file part in the request.", 422)
        file_storage = request.files["file"]
        if file_storage.filename == "":
            return error_response("No file selected.", 422)
        result = BrandingService().upload_logo(current_user_id(), file_storage)
        return success_response(result, "Logo uploaded")

    @jwt_required()
    @permission_required("settings.manage")
    def delete(self):
        result = BrandingService().delete_logo(current_user_id())
        return success_response(result, "Logo removed")


@blp.route("/tax")
class TaxConfigResource(MethodView):
    @jwt_required()
    def get(self):
        return success_response(BrandingService().get_tax_config())

    @jwt_required()
    @permission_required("settings.manage")
    @blp.arguments(TaxConfigUpdateSchema)
    def patch(self, data):
        config = BrandingService().update_tax_config(current_user_id(), **data)
        return success_response(config, "Tax configuration updated")
