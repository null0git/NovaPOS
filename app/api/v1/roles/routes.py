"""Role & permission management endpoints."""
from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

from app.core.middleware.auth_middleware import current_user_id
from app.core.security.permissions import permission_required
from app.core.utils.response import success_response
from app.schemas.role_schema import RoleCreateSchema, RoleUpdateSchema
from app.services.role_service import RoleService

blp = Blueprint("roles", __name__, url_prefix="/api/v1/roles", description="Role & permission management")


@blp.route("")
class RolesListResource(MethodView):
    @jwt_required()
    def get(self):
        roles = RoleService().list_roles()
        return success_response([r.to_dict() for r in roles])

    @jwt_required()
    @permission_required("users.manage")
    @blp.arguments(RoleCreateSchema)
    def post(self, data):
        role = RoleService().create_role(
            current_user_id(), data["name"], data.get("description"), data.get("permissions")
        )
        return success_response(role.to_dict(), "Role created", 201)


@blp.route("/<int:role_id>")
class RoleDetailResource(MethodView):
    @jwt_required()
    def get(self, role_id):
        role = RoleService().get_role(role_id)
        return success_response(role.to_dict())

    @jwt_required()
    @permission_required("users.manage")
    @blp.arguments(RoleUpdateSchema)
    def patch(self, data, role_id):
        role = RoleService().update_role(
            current_user_id(), role_id, data.get("description"), data.get("permissions")
        )
        return success_response(role.to_dict(), "Role updated")

    @jwt_required()
    @permission_required("users.manage")
    def delete(self, role_id):
        RoleService().delete_role(current_user_id(), role_id)
        return success_response(None, "Role deleted")
