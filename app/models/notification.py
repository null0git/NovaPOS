from app.extensions import db
from app.models._base import TimestampMixin, SerializerMixin


class Notification(db.Model, TimestampMixin, SerializerMixin):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)  # low_stock, backup_completed, system, etc.
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    is_archived = db.Column(db.Boolean, default=False, nullable=False)
    severity = db.Column(db.String(20), default="info")  # info, warning, critical

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)  # null = broadcast
    user = db.relationship("User")

    meta = db.Column(db.JSON)

    def __repr__(self):
        return f"<Notification {self.type} {self.title}>"
