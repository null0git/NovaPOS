"""Business-wide settings endpoints (store name, tax rate, currency, etc.)."""
from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

from app.core.middleware.auth_middleware import current_user_id
from app.core.security.permissions import permission_required
from app.core.utils.response import success_response
from app.schemas.settings_schema import SettingUpdateSchema
from app.services.settings_service import SettingsService

blp = Blueprint("settings", __name__, url_prefix="/api/v1/settings", description="Business settings")


@blp.route("")
class SettingsResource(MethodView):
    @jwt_required()
    def get(self):
        return success_response(SettingsService().get_all())

    @jwt_required()
    @permission_required("settings.manage")
    @blp.arguments(SettingUpdateSchema)
    def put(self, data):
        setting = SettingsService().set(current_user_id(), data["key"], data["value"], data.get("description"))
        return success_response({"key": setting.key, "value": setting.value}, "Setting updated")


@blp.route("/<string:key>")
class SettingDetailResource(MethodView):
    @jwt_required()
    def get(self, key):
        return success_response({"key": key, "value": SettingsService().get(key)})
