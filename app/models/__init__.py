"""
Import every model here so:
1. Flask-Migrate/Alembic can discover all tables for autogenerate.
2. `from app.models import User, Product, ...` works app-wide.
"""
from app.models.role import Role
from app.models.permission import Permission
from app.models.user import User
from app.models.category import Category
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.product_unit import ProductUnit
from app.models.inventory import Inventory
from app.models.inventory_history import InventoryHistory
from app.models.customer import Customer
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.payment import Payment
from app.models.refund import Refund
from app.models.discount_log import DiscountLog
from app.models.audit_log import AuditLog
from app.models.notification import Notification
from app.models.backup import Backup
from app.models.settings import Setting
from app.models.device import Device
from app.models.printer import Printer
from app.models.pairing_code import PairingCode
from app.models.system_log import SystemLog
from app.models.session import UserSession
from app.models.generated_barcode import GeneratedBarcode

# V3 additions
from app.models.print_job import PrintJob
from app.models.gift_card import GiftCard, GiftCardTransaction
from app.models.product_history import ProductHistory
from app.models.favorite_product import FavoriteProduct
from app.models.templates import ReceiptTemplate, LabelTemplate

__all__ = [
    "Role", "Permission", "User", "Category", "Product", "ProductVariant",
    "ProductUnit", "Inventory", "InventoryHistory", "Customer", "Sale",
    "SaleItem", "Payment", "Refund", "DiscountLog", "AuditLog", "Notification",
    "Backup", "Setting", "Device", "Printer", "PairingCode", "SystemLog",
    "UserSession", "GeneratedBarcode",
    "PrintJob", "GiftCard", "GiftCardTransaction", "ProductHistory",
    "FavoriteProduct", "ReceiptTemplate", "LabelTemplate",
]
