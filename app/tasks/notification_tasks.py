"""Housekeeping job that prunes old, already-read notifications."""
import logging
from datetime import timedelta

logger = logging.getLogger("novapos")


def stale_notification_cleanup_job(app):
    with app.app_context():
        from app.extensions import db
        from app.models.notification import Notification
        from app.core.utils.datetime_utils import utcnow

        cutoff = utcnow() - timedelta(days=30)
        deleted = Notification.query.filter(
            Notification.is_read.is_(True), Notification.created_at < cutoff
        ).delete(synchronize_session=False)
        db.session.commit()
        logger.info(f"Notification cleanup removed {deleted} old read notifications.")
