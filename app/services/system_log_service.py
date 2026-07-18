"""Business logic for categorized operational logging (distinct from AuditLog)."""
from app.repositories.system_log_repository import SystemLogRepository


class SystemLogService:
    def __init__(self):
        self.repo = SystemLogRepository()

    def log(self, category, message, severity="info", module=None, user_id=None,
            terminal_id=None, meta=None):
        return self.repo.create(
            category=category, severity=severity, module=module, message=message,
            user_id=user_id, terminal_id=terminal_id, meta=meta,
        )

    def list_logs(self, category=None, severity=None):
        query = self.repo.get_all()
        if category:
            query = query.filter_by(category=category)
        if severity:
            query = query.filter_by(severity=severity)
        return query.order_by(self.repo.model.created_at.desc())
