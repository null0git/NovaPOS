from app.models.backup import Backup
from app.repositories.base_repository import BaseRepository


class BackupRepository(BaseRepository):
    model = Backup

    def get_latest(self, limit=10):
        return Backup.query.order_by(Backup.created_at.desc()).limit(limit).all()
