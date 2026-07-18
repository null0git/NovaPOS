"""
Business logic for printer management and print-job dispatch.

The backend itself doesn't talk to USB/Bluetooth/network printer hardware
directly (that requires local OS-level drivers). Instead:

- A local agent (the cashier app / a small desktop helper) performs the
  actual USB/Bluetooth/mDNS discovery and reports results here via
  `discover()`, which upserts them as saved printer profiles.
- When a sale completes (or a test print is requested), this service emits
  a `print:job` WebSocket event containing the formatted receipt to the
  POS terminal room; the local agent listening on that terminal executes
  the actual print using its driver and reports back success/failure via
  `heartbeat()` / status updates.
"""
from datetime import timedelta

from app.core.middleware.error_handler import ConflictError, NotFoundError
from app.core.utils.datetime_utils import utcnow
from app.extensions import db
from app.repositories.printer_repository import PrinterRepository
from app.repositories.print_job_repository import PrintJobRepository
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService

OFFLINE_THRESHOLD = timedelta(minutes=5)


class PrinterService:
    def __init__(self):
        self.repo = PrinterRepository()
        self.print_job_repo = PrintJobRepository()
        self.audit_service = AuditService()
        self.notification_service = NotificationService()

    def list_printers(self):
        return self.repo.get_all()

    def get_printer(self, printer_id):
        printer = self.repo.get_by_id(printer_id)
        if not printer:
            raise NotFoundError("Printer not found.")
        return printer

    def _is_online(self, printer):
        if not printer.last_seen_at:
            return False
        return utcnow() - printer.last_seen_at.replace(tzinfo=utcnow().tzinfo) < OFFLINE_THRESHOLD

    def register(self, actor_id, name, connection_type, identifier, ip_address=None,
                 bluetooth_address=None, manufacturer=None, model=None, profile_type="receipt"):
        if self.repo.identifier_exists(identifier):
            raise ConflictError("A printer with this identifier is already saved.")
        printer = self.repo.create(
            name=name, connection_type=connection_type, identifier=identifier,
            ip_address=ip_address, bluetooth_address=bluetooth_address,
            manufacturer=manufacturer, model=model, status="unknown", profile_type=profile_type,
        )
        self.audit_service.log(actor_id, "printer.register", "printer", printer.id)
        return printer

    def discover(self, discovered_list):
        """Upsert a batch of printers reported by the local discovery agent."""
        results = []
        for entry in discovered_list:
            printer = self.repo.get_by_identifier(entry["identifier"])
            if printer:
                printer.status = "online"
                printer.last_seen_at = utcnow()
                for field in ("name", "ip_address", "bluetooth_address", "manufacturer", "model"):
                    if entry.get(field):
                        setattr(printer, field, entry[field])
                db.session.commit()
            else:
                printer = self.repo.create(
                    name=entry["name"], connection_type=entry["connection_type"],
                    identifier=entry["identifier"], ip_address=entry.get("ip_address"),
                    bluetooth_address=entry.get("bluetooth_address"),
                    manufacturer=entry.get("manufacturer"), model=entry.get("model"),
                    status="online", last_seen_at=utcnow(),
                )
            results.append(printer)
        # Also return previously saved printers not in this scan (they may be offline now).
        all_saved = self.repo.get_active().all()
        discovered_ids = {p.id for p in results}
        for printer in all_saved:
            if printer.id not in discovered_ids:
                results.append(printer)
        return results

    def rename(self, actor_id, printer_id, name):
        printer = self.get_printer(printer_id)
        printer.name = name
        db.session.commit()
        self.audit_service.log(actor_id, "printer.rename", "printer", printer.id)
        return printer

    def update(self, actor_id, printer_id, **fields):
        printer = self.get_printer(printer_id)
        for key, value in fields.items():
            if value is not None:
                setattr(printer, key, value)
        db.session.commit()
        self.audit_service.log(actor_id, "printer.update", "printer", printer.id, details=fields)
        return printer

    def delete(self, actor_id, printer_id):
        printer = self.get_printer(printer_id)
        self.repo.delete(printer)
        self.audit_service.log(actor_id, "printer.delete", "printer", printer_id)

    def set_default(self, actor_id, printer_id):
        printer = self.get_printer(printer_id)
        self.repo.clear_default()
        printer.is_default = True
        db.session.commit()
        self.audit_service.log(actor_id, "printer.set_default", "printer", printer.id)
        return printer

    def get_default(self):
        return self.repo.get_default()

    def heartbeat(self, identifier, paper_status=None):
        printer = self.repo.get_by_identifier(identifier)
        if not printer:
            raise NotFoundError("Printer not registered.")
        printer.status = "online"
        printer.last_seen_at = utcnow()
        if paper_status:
            printer.paper_status = paper_status
        db.session.commit()
        return printer

    def _emit_print_job(self, printer, content, job_type="receipt"):
        try:
            from app.websocket.events import emit_print_job
            emit_print_job(printer, content, job_type)
        except Exception:
            pass

    def print_receipt(self, sale, printer_id=None):
        printer = self.get_printer(printer_id) if printer_id else self.get_default()
        if not printer:
            raise NotFoundError("No default printer configured. Please save and select a printer.")

        from app.services.receipt_service import ReceiptService
        content = ReceiptService().get_receipt_text(sale)

        online = self._is_online(printer)
        self._emit_print_job(printer, content, "receipt")
        status = "sent" if online else "queued_offline"
        self.print_job_repo.create(
            printer_id=printer.id, job_type="receipt", sale_id=sale.id, status=status,
            content_preview=content[:300],
        )

        if not online:
            self.notification_service.create(
                type_="printer_offline",
                title=f"Printer '{printer.name}' may be offline",
                message="The receipt was queued, but the printer hasn't responded recently. "
                        "You can retry printing or choose a different saved printer.",
                severity="warning",
                meta={"printer_id": printer.id, "sale_id": sale.id},
            )
            return {"printer": printer.to_dict(), "status": "queued_offline", "retry_available": True}

        return {"printer": printer.to_dict(), "status": "sent", "retry_available": False}

    def test_print(self, printer_id):
        printer = self.get_printer(printer_id)
        content = f"*** TEST PRINT ***\nPrinter: {printer.name}\nConnection: {printer.connection_type}\n" \
                  f"Time: {utcnow().isoformat()}\n*** END TEST ***"
        self._emit_print_job(printer, content, "test")
        self.print_job_repo.create(printer_id=printer.id, job_type="test", status="sent",
                                    content_preview=content[:300])
        return {"printer": printer.to_dict(), "status": "sent"}

    def get_history(self, printer_id):
        return self.print_job_repo.get_for_printer(printer_id)
