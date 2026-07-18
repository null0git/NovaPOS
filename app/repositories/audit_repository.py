from app.models.audit_log import AuditLog
from app.repositories.base_repository import BaseRepository


class AuditRepository(BaseRepository):
    model = AuditLog

    def get_by_entity(self, entity_type, entity_id):
        return AuditLog.query.filter_by(entity_type=entity_type, entity_id=entity_id).order_by(
            AuditLog.created_at.desc()
        )

    def get_by_user(self, user_id):
        return AuditLog.query.filter_by(user_id=user_id).order_by(AuditLog.created_at.desc())
