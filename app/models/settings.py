from app.extensions import db
from app.models._base import TimestampMixin, SerializerMixin


class Setting(db.Model, TimestampMixin, SerializerMixin):
    """Simple key-value store for business-wide settings (tax rate, store name, etc.)."""
    __tablename__ = "settings"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.JSON, nullable=True)
    description = db.Column(db.String(255))

    def __repr__(self):
        return f"<Setting {self.key}={self.value}>"
