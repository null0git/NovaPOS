"""Notification endpoints."""
from flask import request
from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

from app.core.middleware.auth_middleware import current_user_id
from app.core.security.permissions import permission_required
from app.core.utils.pagination import paginate_query
from app.core.utils.response import success_response
from app.schemas.notification_schema import NotificationCreateSchema
from app.services.notification_service import NotificationService

blp = Blueprint("notifications", __name__, url_prefix="/api/v1/notifications", description="Notifications")


@blp.route("")
class NotificationsListResource(MethodView):
    @jwt_required()
    def get(self):
        unread_only = request.args.get("unread_only", "false").lower() == "true"
        include_archived = request.args.get("include_archived", "false").lower() == "true"
        notif_type = request.args.get("type")
        severity = request.args.get("severity")

        query = NotificationService().get_for_user(current_user_id(), unread_only, include_archived)
        if notif_type:
            query = query.filter_by(type=notif_type)
        if severity:
            query = query.filter_by(severity=severity)

        items, meta = paginate_query(query)
        return success_response([n.to_dict() for n in items], meta=meta)

    @jwt_required()
    @permission_required("notifications.manage", "settings.manage")
    @blp.arguments(NotificationCreateSchema)
    def post(self, data):
        notification = NotificationService().create(
            type_=data["type"], title=data["title"], message=data.get("message"),
            severity=data.get("severity", "info"), user_id=data.get("user_id"),
        )
        return success_response(notification.to_dict(), "Notification created", 201)


@blp.route("/<int:notification_id>/archive")
class NotificationArchiveResource(MethodView):
    @jwt_required()
    def post(self, notification_id):
        notification = NotificationService().archive(notification_id)
        if not notification:
            from app.core.utils.response import error_response
            return error_response("Notification not found.", 404)
        return success_response(notification.to_dict(), "Notification archived")


@blp.route("/<int:notification_id>/read")
class NotificationMarkReadResource(MethodView):
    @jwt_required()
    def post(self, notification_id):
        notification = NotificationService().mark_read(notification_id)
        if not notification:
            from app.core.utils.response import error_response
            return error_response("Notification not found.", 404)
        return success_response(notification.to_dict(), "Marked as read")
