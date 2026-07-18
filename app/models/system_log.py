from app.extensions import db
from app.models._base import TimestampMixin, SerializerMixin

LOG_CATEGORIES = [
    "authentication", "api", "sales", "inventory", "payments",
    "hardware", "customer_display", "backup", "system",
]


class SystemLog(db.Model, TimestampMixin, SerializerMixin):
    """
    Categorized operational log entries, distinct from AuditLog:
    AuditLog records *who changed what* for compliance; SystemLog records
    *what happened* operationally (for troubleshooting/monitoring), including
    system-generated events with no specific user.
    """
    __tablename__ = "system_logs"

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(30), nullable=False)  # see LOG_CATEGORIES
    severity = db.Column(db.String(20), nullable=False, default="info")  # info, warning, error, critical
    module = db.Column(db.String(100))
    message = db.Column(db.Text, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    terminal_id = db.Column(db.Integer, db.ForeignKey("devices.id"), nullable=True)

    user = db.relationship("User")
    terminal = db.relationship("Device")

    meta = db.Column(db.JSON)

    def to_dict(self, exclude=None):
        data = super().to_dict(exclude)
        data["user_name"] = self.user.full_name if self.user else None
        data["terminal_name"] = self.terminal.name if self.terminal else None
        return data

    def __repr__(self):
        return f"<SystemLog [{self.category}/{self.severity}] {self.message[:40]}>"
