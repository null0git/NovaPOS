from app.extensions import db
from app.models._base import TimestampMixin, SerializerMixin


class PrintJob(db.Model, TimestampMixin, SerializerMixin):
    """Log of every print job dispatched, for the printer history view and retry tracking."""
    __tablename__ = "print_jobs"

    id = db.Column(db.Integer, primary_key=True)
    printer_id = db.Column(db.Integer, db.ForeignKey("printers.id"), nullable=False)
    job_type = db.Column(db.String(20), nullable=False, default="receipt")  # receipt, test, label
    sale_id = db.Column(db.Integer, db.ForeignKey("sales.id"), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="sent")  # sent, queued_offline, failed
    content_preview = db.Column(db.Text)  # first N chars, for troubleshooting

    printer = db.relationship("Printer")
    sale = db.relationship("Sale")

    def to_dict(self, exclude=None):
        data = super().to_dict(exclude)
        data["printer_name"] = self.printer.name if self.printer else None
        return data

    def __repr__(self):
        return f"<PrintJob printer={self.printer_id} status={self.status}>"
