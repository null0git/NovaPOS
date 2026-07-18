from app.extensions import db
from app.models._base import TimestampMixin, SerializerMixin


class Backup(db.Model, TimestampMixin, SerializerMixin):
    __tablename__ = "backups"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    file_size_bytes = db.Column(db.Integer)
    status = db.Column(db.String(20), nullable=False, default="completed")  # running, completed, failed
    triggered_by = db.Column(db.String(20), default="scheduled")  # scheduled, manual
    notes = db.Column(db.String(255))

    def __repr__(self):
        return f"<Backup {self.filename}>"
