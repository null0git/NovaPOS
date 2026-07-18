from app.extensions import db
from app.models._base import TimestampMixin, SerializerMixin


class Printer(db.Model, TimestampMixin, SerializerMixin):
    """A saved receipt printer profile (USB, Bluetooth, or Network)."""
    __tablename__ = "printers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    connection_type = db.Column(db.String(20), nullable=False)  # usb, bluetooth, network

    identifier = db.Column(db.String(150), unique=True, nullable=False)
    # USB: vendor/serial string. Bluetooth: MAC address. Network: host:port.

    ip_address = db.Column(db.String(45))
    bluetooth_address = db.Column(db.String(45))
    manufacturer = db.Column(db.String(100))
    model = db.Column(db.String(100))
    profile_type = db.Column(db.String(20), default="receipt", nullable=False)  # receipt, label, kitchen

    status = db.Column(db.String(20), default="unknown")  # online, offline, unknown
    paper_status = db.Column(db.String(20))  # ok, low, empty, unknown
    is_default = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_seen_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # Printer profile settings (per-printer print formatting preferences).
    receipt_width_mm = db.Column(db.Integer, default=80)  # 58 or 80 typical thermal widths
    paper_size = db.Column(db.String(20), default="80mm")
    character_encoding = db.Column(db.String(20), default="utf-8")
    print_density = db.Column(db.String(10), default="normal")  # light, normal, dark
    auto_cut = db.Column(db.Boolean, default=True, nullable=False)
    cash_drawer_pulse = db.Column(db.Boolean, default=False, nullable=False)  # reserved for future use
    print_logo = db.Column(db.Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<Printer {self.name} ({self.connection_type})>"
