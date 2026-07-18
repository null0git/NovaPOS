"""
Central registry of every API v1 blueprint.

app/__init__.py imports ALL_BLUEPRINTS and registers them on the shared
flask-smorest Api instance, which also auto-generates the OpenAPI spec
that powers Swagger UI.
"""
from app.api.v1.auth import blp as auth_blp
from app.api.v1.users import blp as users_blp
from app.api.v1.roles import blp as roles_blp
from app.api.v1.products import blp as products_blp
from app.api.v1.categories import blp as categories_blp
from app.api.v1.inventory import blp as inventory_blp
from app.api.v1.sales import blp as sales_blp
from app.api.v1.payments import blp as payments_blp
from app.api.v1.refunds import blp as refunds_blp
from app.api.v1.customers import blp as customers_blp
from app.api.v1.reports import blp as reports_blp
from app.api.v1.dashboard import blp as dashboard_blp
from app.api.v1.notifications import blp as notifications_blp
from app.api.v1.hardware import blp as hardware_blp
from app.api.v1.backup import blp as backup_blp
from app.api.v1.settings import blp as settings_blp
from app.api.v1.audit import blp as audit_blp

# V2 additions
from app.api.v1.sessions import blp as sessions_blp
from app.api.v1.printers import blp as printers_blp
from app.api.v1.pairing import blp as pairing_blp
from app.api.v1.checkout import blp as checkout_blp
from app.api.v1.variants import blp as variants_blp
from app.api.v1.units import blp as units_blp
from app.api.v1.barcodes import blp as barcodes_blp
from app.api.v1.import_export import blp as import_export_blp
from app.api.v1.branding import blp as branding_blp
from app.api.v1.system import blp as system_blp

# V3 additions
from app.api.v1.gift_cards import blp as gift_cards_blp
from app.api.v1.favorites import blp as favorites_blp
from app.api.v1.search import blp as search_blp
from app.api.v1.templates import blp as templates_blp

ALL_BLUEPRINTS = [
    auth_blp, users_blp, roles_blp, products_blp, categories_blp,
    inventory_blp, sales_blp, payments_blp, refunds_blp, customers_blp,
    reports_blp, dashboard_blp, notifications_blp, hardware_blp,
    backup_blp, settings_blp, audit_blp,
    sessions_blp, printers_blp, pairing_blp, checkout_blp, variants_blp,
    units_blp, barcodes_blp, import_export_blp, branding_blp, system_blp,
    gift_cards_blp, favorites_blp, search_blp, templates_blp,
]
