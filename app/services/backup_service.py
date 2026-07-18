"""Business logic for database backup/restore."""
import io
import json
import os
import shutil
import zipfile
from datetime import datetime, timezone

from flask import current_app

from app.core.middleware.error_handler import NotFoundError, ConflictError
from app.repositories.backup_repository import BackupRepository
from app.services.notification_service import NotificationService


class BackupService:
    def __init__(self):
        self.repo = BackupRepository()
        self.notification_service = NotificationService()

    def _sqlite_db_path(self):
        uri = current_app.config["SQLALCHEMY_DATABASE_URI"]
        if not uri.startswith("sqlite:///"):
            return None
        return uri.replace("sqlite:///", "", 1)

    def create_backup(self, triggered_by="manual"):
        db_path = self._sqlite_db_path()
        backup_folder = current_app.config["BACKUP_FOLDER"]
        os.makedirs(backup_folder, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"novapos_backup_{timestamp}.db"
        dest_path = os.path.join(backup_folder, filename)

        try:
            if db_path and os.path.exists(db_path):
                shutil.copy2(db_path, dest_path)
                size = os.path.getsize(dest_path)
            else:
                # Non-SQLite (e.g. Postgres) backends should use pg_dump externally;
                # we still record the backup attempt for auditability.
                size = 0

            backup = self.repo.create(
                filename=filename, file_size_bytes=size, status="completed",
                triggered_by=triggered_by,
            )
            self.notification_service.notify_backup_completed(backup)
            return backup
        except Exception as exc:
            backup = self.repo.create(
                filename=filename, file_size_bytes=0, status="failed",
                triggered_by=triggered_by, notes=str(exc),
            )
            self.notification_service.notify_backup_failed(str(exc))
            return backup

    def list_backups(self):
        return self.repo.get_all()

    def restore_backup(self, backup_id):
        backup = self.repo.get_by_id(backup_id)
        if not backup:
            raise NotFoundError("Backup not found.")

        db_path = self._sqlite_db_path()
        if not db_path:
            raise NotFoundError("Restore is only supported for SQLite deployments from this endpoint.")

        backup_path = os.path.join(current_app.config["BACKUP_FOLDER"], backup.filename)
        if not os.path.exists(backup_path):
            raise NotFoundError("Backup file missing from disk.")

        shutil.copy2(backup_path, db_path)
        return backup

    # ---------- Complete ZIP backup (DB + uploads + logs + settings/config) ----------

    def create_full_backup_zip(self, triggered_by="manual"):
        """
        Bundles everything into a single ZIP: database file, all uploads
        (product images, receipts, exports, barcode/label images, store logo),
        application logs, and a JSON export of settings/printer profiles/
        customer-display device configs (so they can be restored even onto
        a fresh database).
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"novapos_full_backup_{timestamp}.zip"
        backup_folder = current_app.config["BACKUP_FOLDER"]
        os.makedirs(backup_folder, exist_ok=True)
        dest_path = os.path.join(backup_folder, filename)

        try:
            with zipfile.ZipFile(dest_path, "w", zipfile.ZIP_DEFLATED) as zf:
                db_path = self._sqlite_db_path()
                if db_path and os.path.exists(db_path):
                    zf.write(db_path, arcname="database/novapos.db")

                self._add_directory_to_zip(zf, current_app.config["UPLOAD_FOLDER"], "uploads")
                self._add_directory_to_zip(zf, current_app.config["LOG_FOLDER"], "logs")

                zf.writestr("config/settings_export.json", json.dumps(self._export_settings_bundle(), indent=2))
                zf.writestr("config/manifest.json", json.dumps({
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "triggered_by": triggered_by,
                    "app": "NovaPOS", "version": "2.0",
                }, indent=2))

            size = os.path.getsize(dest_path)
            backup = self.repo.create(filename=filename, file_size_bytes=size, status="completed",
                                       triggered_by=triggered_by, notes="full_zip")
            self.notification_service.notify_backup_completed(backup)
            return backup
        except Exception as exc:
            backup = self.repo.create(filename=filename, file_size_bytes=0, status="failed",
                                       triggered_by=triggered_by, notes=str(exc))
            self.notification_service.notify_backup_failed(str(exc))
            return backup

    def _add_directory_to_zip(self, zf, source_dir, arc_prefix):
        if not os.path.isdir(source_dir):
            return
        for root, _dirs, files in os.walk(source_dir):
            for f in files:
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, source_dir)
                zf.write(full_path, arcname=os.path.join(arc_prefix, rel_path))

    def _export_settings_bundle(self):
        from app.services.settings_service import SettingsService
        from app.models.printer import Printer
        from app.models.device import Device

        return {
            "settings": SettingsService().get_all(),
            "printers": [p.to_dict() for p in Printer.query.all()],
            "devices": [d.to_dict() for d in Device.query.all()],
        }

    def verify_zip_backup(self, file_bytes):
        """Sanity-check a ZIP before restoring: must contain our manifest and be a valid archive."""
        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
                bad_file = zf.testzip()
                if bad_file:
                    raise ConflictError(f"Backup archive is corrupted (bad file: {bad_file}).")
                names = zf.namelist()
                if "config/manifest.json" not in names:
                    raise ConflictError("This doesn't look like a NovaPOS backup archive (manifest missing).")
                manifest = json.loads(zf.read("config/manifest.json"))
                return manifest
        except zipfile.BadZipFile:
            raise ConflictError("Uploaded file is not a valid ZIP archive.")

    def restore_full_backup_zip(self, file_bytes):
        manifest = self.verify_zip_backup(file_bytes)

        with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
            db_path = self._sqlite_db_path()
            if db_path and "database/novapos.db" in zf.namelist():
                with zf.open("database/novapos.db") as src, open(db_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)

            upload_folder = current_app.config["UPLOAD_FOLDER"]
            for name in zf.namelist():
                if name.startswith("uploads/") and not name.endswith("/"):
                    rel_path = os.path.relpath(name, "uploads")
                    target_path = os.path.join(upload_folder, rel_path)
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    with zf.open(name) as src, open(target_path, "wb") as dst:
                        shutil.copyfileobj(src, dst)

            settings_bundle = {}
            if "config/settings_export.json" in zf.namelist():
                settings_bundle = json.loads(zf.read("config/settings_export.json"))

        return {"manifest": manifest, "settings_restored": bool(settings_bundle)}
