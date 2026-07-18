"""Backup & restore endpoints (SQLite-file backup, and complete ZIP backup/restore)."""
from flask import request, Response, send_file
from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

from app.core.security.permissions import permission_required
from app.core.utils.response import success_response, error_response
from app.services.backup_service import BackupService

blp = Blueprint("backup", __name__, url_prefix="/api/v1/backup", description="Backup & restore")


@blp.route("")
class BackupListResource(MethodView):
    @jwt_required()
    @permission_required("settings.manage")
    def get(self):
        backups = BackupService().list_backups()
        return success_response([b.to_dict() for b in backups])

    @jwt_required()
    @permission_required("settings.manage")
    def post(self):
        backup = BackupService().create_backup(triggered_by="manual")
        return success_response(backup.to_dict(), "Database backup created", 201)


@blp.route("/full")
class FullBackupResource(MethodView):
    @jwt_required()
    @permission_required("settings.manage")
    def post(self):
        """Create a complete ZIP backup: database + uploads + logs + settings/printers/devices."""
        backup = BackupService().create_full_backup_zip(triggered_by="manual")
        return success_response(backup.to_dict(), "Full backup archive created", 201)


@blp.route("/<int:backup_id>/download")
class BackupDownloadResource(MethodView):
    @jwt_required()
    @permission_required("settings.manage")
    def get(self, backup_id):
        import os
        from flask import current_app
        backup = BackupService().repo.get_by_id(backup_id)
        if not backup:
            return error_response("Backup not found.", 404)
        path = os.path.join(current_app.config["BACKUP_FOLDER"], backup.filename)
        if not os.path.exists(path):
            return error_response("Backup file missing from disk.", 404)
        return send_file(path, as_attachment=True, download_name=backup.filename)


@blp.route("/<int:backup_id>/restore")
class BackupRestoreResource(MethodView):
    @jwt_required()
    @permission_required("settings.manage")
    def post(self, backup_id):
        backup = BackupService().restore_backup(backup_id)
        return success_response(backup.to_dict(), "Backup restored")


@blp.route("/restore-full")
class FullBackupRestoreResource(MethodView):
    @jwt_required()
    @permission_required("settings.manage")
    def post(self):
        """Upload a complete ZIP backup; it's verified, then extracted and restored."""
        if "file" not in request.files:
            return error_response("No file part in the request.", 422)
        file_bytes = request.files["file"].read()
        result = BackupService().restore_full_backup_zip(file_bytes)
        return success_response(result, "Full backup restored successfully")


@blp.route("/verify")
class BackupVerifyResource(MethodView):
    @jwt_required()
    @permission_required("settings.manage")
    def post(self):
        """Verify a ZIP backup's integrity without restoring it."""
        if "file" not in request.files:
            return error_response("No file part in the request.", 422)
        file_bytes = request.files["file"].read()
        manifest = BackupService().verify_zip_backup(file_bytes)
        return success_response(manifest, "Backup archive verified")
