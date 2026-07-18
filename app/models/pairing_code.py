from app.extensions import db
from app.models._base import TimestampMixin, SerializerMixin


class PairingCode(db.Model, TimestampMixin, SerializerMixin):
    """
    Short-lived code (also embeddable in a QR code) that a customer display
    redeems to pair itself with a specific POS terminal/register.
    """
    __tablename__ = "pairing_codes"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(12), unique=True, nullable=False, index=True)
    terminal_id = db.Column(db.Integer, db.ForeignKey("devices.id"), nullable=False)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    redeemed = db.Column(db.Boolean, default=False, nullable=False)
    redeemed_by_device_id = db.Column(db.Integer, db.ForeignKey("devices.id"), nullable=True)
    redeemed_at = db.Column(db.DateTime(timezone=True), nullable=True)

    terminal = db.relationship("Device", foreign_keys=[terminal_id])
    redeemed_by = db.relationship("Device", foreign_keys=[redeemed_by_device_id])

    def __repr__(self):
        return f"<PairingCode {self.code} terminal={self.terminal_id}>"
