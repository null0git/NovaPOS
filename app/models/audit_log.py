from app.extensions import db
from app.models._base import TimestampMixin, SerializerMixin


class AuditLog(db.Model, TimestampMixin, SerializerMixin):
    """Immutable record of sensitive actions (who did what, to what, when)."""
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    action = db.Column(db.String(100), nullable=False)  # e.g. "sale.void", "product.delete"
    entity_type = db.Column(db.String(50), index=True)
    entity_id = db.Column(db.Integer)
    details = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))

    user = db.relationship("User")

    def to_dict(self, exclude=None):
        data = super().to_dict(exclude)
        data["user_name"] = self.user.full_name if self.user else "System"
        return data

    def __repr__(self):
        return f"<AuditLog {self.action} by user={self.user_id}>"
