"""Session management endpoints: view active sessions, login history, force logout."""
from flask.views import MethodView
from flask_jwt_extended import jwt_required, get_jwt

from flask_smorest import Blueprint

from app.core.middleware.auth_middleware import current_user_id
from app.core.security.permissions import permission_required
from app.core.utils.response import success_response
from app.services.session_service import SessionService

blp = Blueprint("sessions", __name__, url_prefix="/api/v1/sessions", description="Session management")


@blp.route("")
class ActiveSessionsResource(MethodView):
    @jwt_required()
    @permission_required("settings.manage")
    def get(self):
        sessions = SessionService().list_all_active()
        return success_response([s.to_dict() for s in sessions])


@blp.route("/me")
class MySessionsResource(MethodView):
    @jwt_required()
    def get(self):
        sessions = SessionService().list_active_for_user(current_user_id())
        return success_response([s.to_dict() for s in sessions])


@blp.route("/user/<int:user_id>/history")
class UserLoginHistoryResource(MethodView):
    @jwt_required()
    @permission_required("settings.manage")
    def get(self, user_id):
        sessions = SessionService().login_history(user_id)
        return success_response([s.to_dict() for s in sessions])


@blp.route("/<int:session_id>/revoke")
class RevokeSessionResource(MethodView):
    @jwt_required()
    @permission_required("settings.manage")
    def post(self, session_id):
        session = SessionService().revoke(session_id)
        return success_response(session.to_dict(), "Session revoked (device will be logged out)")


@blp.route("/user/<int:user_id>/force-logout")
class ForceLogoutResource(MethodView):
    @jwt_required()
    @permission_required("settings.manage", "users.manage")
    def post(self, user_id):
        sessions = SessionService().revoke_all_for_user(user_id)
        return success_response(
            {"revoked_count": len(sessions)}, "All sessions revoked; user will be logged out everywhere"
        )
