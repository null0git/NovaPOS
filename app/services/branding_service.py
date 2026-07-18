"""
Business logic for store branding (name, logo, address, contact info) and
tax configuration. Both are thin, structured wrappers around SettingsService
so the frontend has clean dedicated endpoints instead of raw key/value pairs.
"""
import os

from flask import current_app
from PIL import Image

from app.core.utils.file_utils import save_upload, delete_file, allowed_file
from app.services.settings_service import SettingsService

BRANDING_KEYS = ["business_name", "logo_filename", "address", "phone", "email", "website", "tax_number"]
TAX_KEYS = ["tax_enabled", "tax_name", "default_tax_rate", "prices_include_tax"]
LOGO_MAX_DIMENSION = 512  # px — logos are auto-resized down to this on upload


class BrandingService:
    def __init__(self):
        self.settings_service = SettingsService()

    def get_branding(self):
        all_settings = self.settings_service.get_all()
        return {k: all_settings.get(k) for k in BRANDING_KEYS}

    def update_branding(self, actor_id, **fields):
        for key, value in fields.items():
            if key in BRANDING_KEYS and value is not None:
                self.settings_service.set(actor_id, key, value)
        return self.get_branding()

    def upload_logo(self, actor_id, file_storage):
        if not allowed_file(file_storage.filename):
            from app.core.middleware.error_handler import ConflictError
            raise ConflictError("Unsupported image file type. Use PNG, JPEG, JPG, or WebP.")

        folder = os.path.join(current_app.config["UPLOAD_FOLDER"], "branding")
        old_filename = self.settings_service.get("logo_filename")
        filename, full_path = save_upload(file_storage, folder)

        self._resize_logo(full_path)

        self.settings_service.set(actor_id, "logo_filename", filename)

        if old_filename:
            delete_file(os.path.join(folder, old_filename))
        return {"logo_filename": filename}

    def _resize_logo(self, path):
        """Downscale (preserving aspect ratio) so oversized uploads don't bloat receipts/backups."""
        try:
            with Image.open(path) as img:
                img.thumbnail((LOGO_MAX_DIMENSION, LOGO_MAX_DIMENSION))
                img.save(path)
        except Exception:
            pass  # if Pillow can't process it, keep the original upload as-is

    def delete_logo(self, actor_id):
        folder = os.path.join(current_app.config["UPLOAD_FOLDER"], "branding")
        filename = self.settings_service.get("logo_filename")
        if filename:
            delete_file(os.path.join(folder, filename))
        self.settings_service.set(actor_id, "logo_filename", None)
        return {"logo_filename": None}

    def get_tax_config(self):
        all_settings = self.settings_service.get_all()
        return {k: all_settings.get(k) for k in TAX_KEYS}

    def update_tax_config(self, actor_id, **fields):
        for key, value in fields.items():
            if key in TAX_KEYS and value is not None:
                self.settings_service.set(actor_id, key, value)
        return self.get_tax_config()
