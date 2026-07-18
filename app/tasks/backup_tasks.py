"""Nightly database backup job."""
import logging

logger = logging.getLogger("novapos")


def nightly_backup_job(app):
    with app.app_context():
        from app.services.backup_service import BackupService
        try:
            backup = BackupService().create_backup(triggered_by="scheduled")
            logger.info(f"Nightly backup completed: {backup.filename}")
        except Exception:
            logger.exception("Nightly backup failed")
