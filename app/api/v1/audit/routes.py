"""Audit log read endpoints (immutable trail of sensitive actions)."""
from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

from app.core.security.permissions import permission_required
from app.core.utils.pagination import paginate_query
from app.core.utils.response import success_response
from app.services.audit_service import AuditService

blp = Blueprint("audit", __name__, url_prefix="/api/v1/audit", description="Audit trail")


@blp.route("")
class AuditListResource(MethodView):
    @jwt_required()
    @permission_required("settings.manage")
    def get(self):
        items, meta = paginate_query(AuditService().get_all())
        return success_response([a.to_dict() for a in items], meta=meta)


@blp.route("/entity/<string:entity_type>/<int:entity_id>")
class AuditForEntityResource(MethodView):
    @jwt_required()
    @permission_required("settings.manage")
    def get(self, entity_type, entity_id):
        items, meta = paginate_query(AuditService().get_for_entity(entity_type, entity_id))
        return success_response([a.to_dict() for a in items], meta=meta)


@blp.route("/user/<int:user_id>")
class AuditForUserResource(MethodView):
    @jwt_required()
    @permission_required("settings.manage")
    def get(self, user_id):
        items, meta = paginate_query(AuditService().get_for_user(user_id))
        return success_response([a.to_dict() for a in items], meta=meta)
