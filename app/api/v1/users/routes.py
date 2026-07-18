"""User management endpoints (admin/manager only)."""
from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

from app.core.middleware.auth_middleware import current_user_id
from app.core.security.permissions import permission_required
from app.core.utils.pagination import paginate_query
from app.core.utils.response import success_response
from app.schemas.user_schema import UserCreateSchema, UserUpdateSchema, UserResponseSchema
from app.services.user_service import UserService

blp = Blueprint("users", __name__, url_prefix="/api/v1/users", description="User management")


@blp.route("")
class UsersListResource(MethodView):
    @jwt_required()
    @permission_required("users.view", "users.manage")
    def get(self):
        items, meta = paginate_query(UserService().list_users())
        return success_response([u.to_dict() for u in items], meta=meta)

    @jwt_required()
    @permission_required("users.manage")
    @blp.arguments(UserCreateSchema)
    def post(self, data):
        user = UserService().create_user(current_user_id(), **data)
        return success_response(user.to_dict(), "User created", 201)


@blp.route("/<int:user_id>")
class UserDetailResource(MethodView):
    @jwt_required()
    @permission_required("users.view", "users.manage")
    def get(self, user_id):
        user = UserService().get_user(user_id)
        return success_response(user.to_dict())

    @jwt_required()
    @permission_required("users.manage")
    @blp.arguments(UserUpdateSchema)
    def patch(self, data, user_id):
        user = UserService().update_user(current_user_id(), user_id, **data)
        return success_response(user.to_dict(), "User updated")

    @jwt_required()
    @permission_required("users.manage")
    def delete(self, user_id):
        UserService().deactivate_user(current_user_id(), user_id)
        return success_response(None, "User deactivated")


@blp.route("/<int:user_id>/reactivate")
class UserReactivateResource(MethodView):
    @jwt_required()
    @permission_required("users.manage")
    def post(self, user_id):
        user = UserService().reactivate_user(current_user_id(), user_id)
        return success_response(user.to_dict(), "User reactivated")


@blp.route("/<int:user_id>/reset-password")
class UserResetPasswordResource(MethodView):
    @jwt_required()
    @permission_required("users.manage")
    def post(self, user_id):
        from flask import request
        new_password = (request.get_json(silent=True) or {}).get("new_password")
        if not new_password or len(new_password) < 6:
            from app.core.utils.response import error_response
            return error_response("new_password must be at least 6 characters.", 422)
        UserService().reset_password(current_user_id(), user_id, new_password)
        return success_response(None, "Password reset successfully")
