"""
Business logic for key-value business settings (store name, default tax rate, etc.).

Settings are read on almost every request path (receipts, dashboard, branding,
tax calculation) but written rarely, so they're cached in-process with a
simple version counter invalidated on every write — cheap and correct for a
single-process/single-worker deployment (see README performance notes for
scaling to multiple workers with a shared cache like Redis).
"""
from app.repositories.settings_repository import SettingsRepository
from app.services.audit_service import AuditService

DEFAULT_SETTINGS = {
    "business_name": "NovaPOS Store",
    "default_tax_rate": 0,
    "currency": "USD",
    "receipt_footer": "Thank you for shopping with us!",
    "receipt_paper_width_mm": 80,
    "refund_policy_text": None,
    "low_stock_threshold_default": 5,
    # Branding
    "logo_filename": None,
    "address": None,
    "phone": None,
    "email": None,
    "website": None,
    "tax_number": None,
    # Tax configuration
    "tax_enabled": True,
    "tax_name": "VAT",
    "prices_include_tax": False,
    "allow_duplicate_manufacturer_barcodes": False,
}

_cache = {"data": None}


class SettingsService:
    def __init__(self):
        self.repo = SettingsRepository()
        self.audit_service = AuditService()

    def get_all(self):
        if _cache["data"] is None:
            stored = self.repo.get_all_as_dict()
            _cache["data"] = {**DEFAULT_SETTINGS, **stored}
        return _cache["data"]

    def get(self, key):
        return self.get_all().get(key)

    def set(self, actor_id, key, value, description=None):
        setting = self.repo.set_value(key, value, description)
        _cache["data"] = None  # invalidate — next get_all() reloads from DB
        self.audit_service.log(actor_id, "settings.update", "setting", setting.id,
                                details={"key": key, "value": value})
        return setting

    @staticmethod
    def clear_cache():
        """Exposed for tests — ensures a clean cache between test runs."""
        _cache["data"] = None
