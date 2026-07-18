from app.models.system_log import SystemLog
from app.repositories.base_repository import BaseRepository


class SystemLogRepository(BaseRepository):
    model = SystemLog

    def get_by_category(self, category):
        return SystemLog.query.filter_by(category=category)

    def get_by_severity(self, severity):
        return SystemLog.query.filter_by(severity=severity)
