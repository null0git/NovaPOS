from app.extensions import db
from app.models._base import TimestampMixin, SerializerMixin


class Device(db.Model, TimestampMixin, SerializerMixin):
    """Registered hardware/client endpoints: RPi customer displays, printers, scanners, terminals."""
    __tablename__ = "devices"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    device_type = db.Column(db.String(30), nullable=False)
    # types: customer_display, receipt_printer, barcode_scanner, cash_drawer, pos_terminal

    identifier = db.Column(db.String(100), unique=True, nullable=False)  # MAC, serial, or token
    ip_address = db.Column(db.String(45))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_seen_at = db.Column(db.DateTime(timezone=True), nullable=True)
    config = db.Column(db.JSON)

    def __repr__(self):
        return f"<Device {self.name} ({self.device_type})>"
