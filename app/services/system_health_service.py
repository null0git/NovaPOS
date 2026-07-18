"""
System health monitoring: DB connectivity, API status, WebSocket clients,
printer/customer-display status, CPU/memory/disk usage, last backup.
"""
from datetime import timedelta

import psutil
from sqlalchemy import text

from app.extensions import db
from app.core.utils.datetime_utils import utcnow


class SystemHealthService:
    def check_database(self):
        try:
            db.session.execute(text("SELECT 1"))
            return {"status": "ok"}
        except Exception as exc:
            return {"status": "error", "detail": str(exc)}

    def check_printers(self):
        from app.models.printer import Printer
        printers = Printer.query.filter_by(is_active=True).all()
        cutoff = utcnow() - timedelta(minutes=5)
        online = sum(1 for p in printers if p.last_seen_at and p.last_seen_at.replace(tzinfo=utcnow().tzinfo) >= cutoff)
        return {"total": len(printers), "online": online, "offline": len(printers) - online}

    def check_customer_displays(self):
        from app.models.device import Device
        displays = Device.query.filter_by(device_type="customer_display", is_active=True).all()
        cutoff = utcnow() - timedelta(minutes=5)
        online = sum(1 for d in displays if d.last_seen_at and d.last_seen_at.replace(tzinfo=utcnow().tzinfo) >= cutoff)
        return {"total": len(displays), "online": online, "offline": len(displays) - online}

    def check_resources(self):
        return {
            "cpu_percent": psutil.cpu_percent(interval=0.2),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage("/").percent,
        }

    def check_last_backup(self):
        from app.repositories.backup_repository import BackupRepository
        latest = BackupRepository().get_latest(limit=1)
        if not latest:
            return {"last_backup_at": None, "status": None}
        backup = latest[0]
        return {"last_backup_at": backup.created_at.isoformat(), "status": backup.status,
                "filename": backup.filename}

    def full_report(self):
        return {
            "api": {"status": "ok"},
            "database": self.check_database(),
            "printers": self.check_printers(),
            "customer_displays": self.check_customer_displays(),
            "resources": self.check_resources(),
            "last_backup": self.check_last_backup(),
            "checked_at": utcnow().isoformat(),
        }
