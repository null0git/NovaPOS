from app.models.notification import Notification
from app.repositories.base_repository import BaseRepository


class NotificationRepository(BaseRepository):
    model = Notification

    def get_for_user(self, user_id, unread_only=False, include_archived=False):
        query = Notification.query.filter(
            (Notification.user_id == user_id) | (Notification.user_id.is_(None))
        )
        if not include_archived:
            query = query.filter_by(is_archived=False)
        if unread_only:
            query = query.filter_by(is_read=False)
        return query.order_by(Notification.created_at.desc())

    def mark_read(self, notification):
        notification.is_read = True
        from app.extensions import db
        db.session.commit()
        return notification

    def archive(self, notification):
        notification.is_archived = True
        from app.extensions import db
        db.session.commit()
        return notification
