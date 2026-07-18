from app.extensions import db
from app.models._base import TimestampMixin, SerializerMixin


class UserSession(db.Model, TimestampMixin, SerializerMixin):
    """
    One row per issued access token, so admins can see active sessions,
    review login history, and force-revoke a specific session or device.
    """
    __tablename__ = "user_sessions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    jti = db.Column(db.String(36), unique=True, nullable=False, index=True)

    device_info = db.Column(db.String(255))
    terminal_id = db.Column(db.Integer, db.ForeignKey("devices.id"), nullable=True)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))

    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    revoked = db.Column(db.Boolean, default=False, nullable=False)
    revoked_at = db.Column(db.DateTime(timezone=True), nullable=True)
    last_seen_at = db.Column(db.DateTime(timezone=True), nullable=True)

    user = db.relationship("User")
    terminal = db.relationship("Device")

    def to_dict(self, exclude=None):
        data = super().to_dict(exclude)
        data["user_name"] = self.user.full_name if self.user else None
        data["terminal_name"] = self.terminal.name if self.terminal else None
        return data

    def __repr__(self):
        return f"<UserSession user={self.user_id} jti={self.jti[:8]}>"
