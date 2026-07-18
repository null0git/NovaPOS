"""
Business logic for connecting a Customer Display to a POS terminal.

Connection priority implemented here (client tries these in order):
  1. Automatic local network discovery -> GET /hardware/discover (existing)
  2. Select from discovered POS terminals -> same endpoint, client picks one
  3. Pairing code -> generate_code() / redeem_code() below
  4. QR code pairing -> generate_code() also returns a QR encoding the code
  5. Manual server address -> handled entirely client-side (no backend need)

Once paired, the display stores the terminal's device identifier and
reconnects automatically (client-side responsibility); the backend just
needs `redeem_code` to be idempotent-ish and heartbeat to keep it "seen".
"""
import base64
import random
import string
from datetime import timedelta

from app.core.middleware.error_handler import ConflictError, NotFoundError
from app.core.utils.datetime_utils import utcnow
from app.core.utils.qr_code import generate_qr_bytes
from app.extensions import db
from app.repositories.pairing_repository import PairingRepository
from app.repositories.device_repository import DeviceRepository

CODE_TTL_MINUTES = 10


class PairingService:
    def __init__(self):
        self.repo = PairingRepository()
        self.device_repo = DeviceRepository()

    def _generate_code(self):
        return "".join(random.choices(string.digits, k=6))

    def generate_pairing_code(self, terminal_id, server_address=None):
        terminal = self.device_repo.get_by_id(terminal_id)
        if not terminal:
            raise NotFoundError("POS terminal device not found. Register it first.")

        code = self._generate_code()
        while self.repo.get_by_code(code):
            code = self._generate_code()

        pairing = self.repo.create(
            code=code, terminal_id=terminal_id,
            expires_at=utcnow() + timedelta(minutes=CODE_TTL_MINUTES),
        )

        qr_payload = f"novapos-pair:{code}"
        if server_address:
            qr_payload = f"novapos-pair:{code}:{server_address}"
        qr_bytes = generate_qr_bytes(qr_payload)

        return {
            "code": pairing.code,
            "expires_at": pairing.expires_at.isoformat(),
            "terminal_id": terminal_id,
            "terminal_name": terminal.name,
            "qr_code_base64": base64.b64encode(qr_bytes).decode(),
        }

    def redeem_pairing_code(self, code, display_identifier, display_name="Customer Display"):
        pairing = self.repo.get_by_code(code)
        if not pairing:
            raise NotFoundError("Invalid pairing code.")
        if pairing.redeemed:
            raise ConflictError("This pairing code has already been used.")
        if pairing.expires_at.replace(tzinfo=utcnow().tzinfo) < utcnow():
            raise ConflictError("This pairing code has expired. Please generate a new one.")

        device = self.device_repo.get_by_identifier(display_identifier)
        if not device:
            device = self.device_repo.create(
                name=display_name, device_type="customer_display",
                identifier=display_identifier, last_seen_at=utcnow(),
            )
        else:
            device.last_seen_at = utcnow()

        pairing.redeemed = True
        pairing.redeemed_by_device_id = device.id
        pairing.redeemed_at = utcnow()
        db.session.commit()

        return {
            "device_id": device.id,
            "terminal_id": pairing.terminal_id,
            "terminal_name": pairing.terminal.name if pairing.terminal else None,
            "websocket_room": "customer_displays",
        }

    def discover_terminals(self, active_within_minutes=5):
        """POS terminals that have sent a heartbeat/login recently — candidates for auto-discovery."""
        from app.models.device import Device
        cutoff = utcnow() - timedelta(minutes=active_within_minutes)
        return Device.query.filter(
            Device.device_type == "pos_terminal",
            Device.is_active.is_(True),
            Device.last_seen_at.isnot(None),
            Device.last_seen_at >= cutoff,
        ).all()
