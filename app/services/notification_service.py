"""Business logic for creating and dispatching notifications (in-app + WebSocket push)."""
from app.repositories.notification_repository import NotificationRepository


class NotificationService:
    def __init__(self):
        self.repo = NotificationRepository()

    def _broadcast(self, notification):
        """Push the notification over WebSocket to connected dashboards, if available."""
        try:
            from app.websocket.events import emit_notification
            emit_notification(notification)
        except Exception:
            # WebSocket layer may not be initialized (e.g. during tests/CLI use).
            pass

    def create(self, type_, title, message=None, severity="info", user_id=None, meta=None):
        notification = self.repo.create(
            type=type_, title=title, message=message, severity=severity,
            user_id=user_id, meta=meta,
        )
        self._broadcast(notification)
        return notification

    def notify_low_stock(self, inventory):
        product_name = inventory.product.name if inventory.product else f"Product #{inventory.product_id}"
        return self.create(
            type_="low_stock",
            title=f"Low stock: {product_name}",
            message=f"{product_name} has {inventory.quantity} units left "
                    f"(threshold: {inventory.low_stock_threshold}).",
            severity="warning",
            meta={"product_id": inventory.product_id, "quantity": inventory.quantity},
        )

    def notify_backup_completed(self, backup):
        return self.create(
            type_="backup_completed",
            title="Backup completed",
            message=f"Backup '{backup.filename}' completed successfully.",
            severity="info",
            meta={"backup_id": backup.id},
        )

    def notify_backup_failed(self, error_message):
        return self.create(
            type_="backup_failed",
            title="Backup failed",
            message=error_message,
            severity="critical",
        )

    def get_for_user(self, user_id, unread_only=False, include_archived=False):
        return self.repo.get_for_user(user_id, unread_only, include_archived)

    def mark_read(self, notification_id):
        notification = self.repo.get_by_id(notification_id)
        if notification:
            self.repo.mark_read(notification)
        return notification

    def archive(self, notification_id):
        notification = self.repo.get_by_id(notification_id)
        if notification:
            self.repo.archive(notification)
        return notification
