"""System health monitoring and categorized system logs."""
from flask import request
from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

from app.core.security.permissions import permission_required
from app.core.utils.pagination import paginate_query
from app.core.utils.response import success_response
from app.services.system_health_service import SystemHealthService
from app.services.system_log_service import SystemLogService

blp = Blueprint("system", __name__, url_prefix="/api/v1/system",
                description="System health monitoring & operational logs")


@blp.route("/health")
class SystemHealthResource(MethodView):
    @jwt_required()
    @permission_required("settings.manage", "dashboard.view")
    def get(self):
        return success_response(SystemHealthService().full_report())


@blp.route("/logs")
class SystemLogsResource(MethodView):
    @jwt_required()
    @permission_required("settings.manage")
    def get(self):
        category = request.args.get("category")
        severity = request.args.get("severity")
        items, meta = paginate_query(SystemLogService().list_logs(category, severity))
        return success_response([log.to_dict() for log in items], meta=meta)
