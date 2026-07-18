"""Business logic for writing audit trail entries (used by nearly every other service)."""
from app.repositories.audit_repository import AuditRepository


class AuditService:
    def __init__(self):
        self.repo = AuditRepository()

    def log(self, user_id, action, entity_type=None, entity_id=None, details=None, ip_address=None):
        entry = self.repo.create(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            ip_address=ip_address,
        )
        self._broadcast_activity(entry)
        return entry

    def _broadcast_activity(self, entry):
        try:
            from app.websocket.events import emit_activity
            emit_activity(entry)
        except Exception:
            # WebSocket layer may not be initialized (e.g. during tests/CLI use).
            pass

    def get_for_entity(self, entity_type, entity_id):
        return self.repo.get_by_entity(entity_type, entity_id)

    def get_for_user(self, user_id):
        return self.repo.get_by_user(user_id)

    def get_all(self):
        return self.repo.get_all()
