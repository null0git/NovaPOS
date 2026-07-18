"""Authentication endpoints: login, refresh, register, change password, me."""
from flask.views import MethodView
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from flask_smorest import Blueprint

from app.core.middleware.auth_middleware import current_user
from app.core.middleware.rate_limit import rate_limit
from app.core.security.permissions import permission_required
from app.core.utils.response import success_response
from app.schemas.auth_schema import (
    LoginSchema, TokenResponseSchema, RefreshResponseSchema,
    ChangePasswordSchema, RegisterUserSchema,
)
from app.schemas.user_schema import UserResponseSchema
from app.services.auth_service import AuthService

blp = Blueprint("auth", __name__, url_prefix="/api/v1/auth", description="Authentication operations")


@blp.route("/login")
class LoginResource(MethodView):
    @blp.doc(security=[])
    @blp.arguments(LoginSchema)
    @rate_limit("60 per minute")
    def post(self, data):
        from flask import request
        result = AuthService().login(
            data["username"], data["password"],
            ip_address=request.remote_addr,
            user_agent=request.headers.get("User-Agent"),
            terminal_id=request.headers.get("X-Terminal-Id", type=int),
        )
        return success_response(result, "Login successful")


@blp.route("/refresh")
class RefreshResource(MethodView):
    @jwt_required(refresh=True)
    def post(self):
        identity = get_jwt_identity()
        result = AuthService().refresh(identity)
        return success_response(result, "Token refreshed")


@blp.route("/register")
class RegisterResource(MethodView):
    @jwt_required()
    @permission_required("users.manage")
    @blp.arguments(RegisterUserSchema)
    def post(self, data):
        """Create a user account. Requires users.manage — use /api/v1/users for the fuller user-management API."""
        user = AuthService().register(
            username=data["username"], full_name=data["full_name"], password=data["password"],
            role_name=data["role_name"], email=data.get("email"), phone=data.get("phone"),
        )
        return success_response(user.to_dict(), "User registered", 201)


@blp.route("/change-password")
class ChangePasswordResource(MethodView):
    @jwt_required()
    @blp.arguments(ChangePasswordSchema)
    def post(self, data):
        AuthService().change_password(current_user(), data["current_password"], data["new_password"])
        return success_response(None, "Password changed successfully")


@blp.route("/me")
class MeResource(MethodView):
    @jwt_required()
    def get(self):
        user = current_user()
        return success_response(user.to_dict(), "Current user")
