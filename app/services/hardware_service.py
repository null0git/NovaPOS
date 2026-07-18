"""
Business logic for hardware devices: barcode scanners, receipt printers,
cash drawers, and customer displays. Devices are registered so different
frontends can address the same physical hardware consistently.
"""
from app.core.middleware.error_handler import ConflictError, NotFoundError
from app.core.utils.datetime_utils import utcnow
from app.extensions import db
from app.repositories.device_repository import DeviceRepository
from app.services.audit_service import AuditService


class HardwareService:
    def __init__(self):
        self.repo = DeviceRepository()
        self.audit_service = AuditService()

    def list_devices(self, device_type=None):
        return self.repo.get_by_type(device_type) if device_type else self.repo.get_all()

    def get_device(self, device_id):
        device = self.repo.get_by_id(device_id)
        if not device:
            raise NotFoundError("Device not found.")
        return device

    def register_device(self, actor_id, name, device_type, identifier, ip_address=None, config=None):
        if self.repo.identifier_exists(identifier):
            raise ConflictError("A device with this identifier is already registered.")
        device = self.repo.create(
            name=name, device_type=device_type, identifier=identifier,
            ip_address=ip_address, config=config or {}, last_seen_at=utcnow(),
        )
        self.audit_service.log(actor_id, "device.register", "device", device.id)
        return device

    def update_device(self, actor_id, device_id, **fields):
        device = self.get_device(device_id)
        for key, value in fields.items():
            if value is not None:
                setattr(device, key, value)
        db.session.commit()
        self.audit_service.log(actor_id, "device.update", "device", device.id, details=fields)
        return device

    def heartbeat(self, identifier):
        device = self.repo.get_by_identifier(identifier)
        if not device:
            raise NotFoundError("Device not registered.")
        device.last_seen_at = utcnow()
        db.session.commit()
        return device

    def deregister_device(self, actor_id, device_id):
        device = self.get_device(device_id)
        self.repo.delete(device)
        self.audit_service.log(actor_id, "device.deregister", "device", device_id)

    def push_to_customer_display(self, sale):
        """Broadcast the current sale/cart to all connected customer-display devices."""
        try:
            from app.websocket.events import emit_customer_display_update
            emit_customer_display_update(sale)
        except Exception:
            pass

    def open_cash_drawer(self, device_id):
        device = self.get_device(device_id)
        if device.device_type != "cash_drawer":
            raise ConflictError("This device is not a cash drawer.")
        try:
            from app.websocket.events import emit_cash_drawer_open
            emit_cash_drawer_open(device)
        except Exception:
            pass
        return {"device_id": device.id, "command": "open"}
