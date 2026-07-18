"""Aggregated home-screen dashboard endpoint."""
from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

from app.core.security.permissions import permission_required
from app.core.utils.response import success_response
from app.services.dashboard_service import DashboardService

blp = Blueprint("dashboard", __name__, url_prefix="/api/v1/dashboard", description="Dashboard summary")


@blp.route("/summary")
class DashboardSummaryResource(MethodView):
    @jwt_required()
    @permission_required("dashboard.view")
    def get(self):
        return success_response(DashboardService().summary())
