"""Business logic for product management: creation, updates, images, stock linkage."""
import os

from flask import current_app

from app.core.middleware.error_handler import ConflictError, NotFoundError
from app.core.utils.file_utils import save_upload, delete_file, allowed_file
from app.extensions import db
from app.repositories.product_repository import ProductRepository
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.product_history_repository import ProductHistoryRepository
from app.services.audit_service import AuditService
from app.services.barcode_service import BarcodeService

# Fields whose changes are worth a dedicated, field-level ProductHistory entry
# (price/cost changes matter for margin analysis; barcode changes matter for
# traceability). Everything else still lands in the general AuditLog.
TRACKED_FIELDS = {"price": "price", "cost_price": "cost_price", "barcode": "barcode"}


class ProductService:
    def __init__(self):
        self.repo = ProductRepository()
        self.inventory_repo = InventoryRepository()
        self.category_repo = CategoryRepository()
        self.history_repo = ProductHistoryRepository()
        self.audit_service = AuditService()
        self.barcode_service = BarcodeService()

    def list_products(self, active_only=False, category_id=None):
        query = self.repo.get_active() if active_only else self.repo.get_all()
        if category_id:
            query = query.filter_by(category_id=category_id)
        return query

    def get_product(self, product_id):
        product = self.repo.get_by_id(product_id)
        if not product:
            raise NotFoundError("Product not found.")
        return product

    def get_by_barcode(self, barcode):
        product = self.repo.get_by_barcode(barcode)
        if not product:
            raise NotFoundError("No product found for this barcode.")
        return product

    def create_product(self, actor_id, data):
        if self.repo.sku_exists(data["sku"]):
            raise ConflictError("A product with this SKU already exists.")
        barcode = data.get("barcode")
        if barcode and self.repo.barcode_exists(barcode):
            raise ConflictError("A product with this barcode already exists.")
        if data.get("category_id"):
            category = self.category_repo.get_by_id(data["category_id"])
            if not category:
                raise NotFoundError("Category not found.")

        product = self.repo.create(
            sku=data["sku"],
            barcode=barcode,
            name=data["name"],
            description=data.get("description"),
            price=data["price"],
            cost_price=data.get("cost_price", 0),
            tax_rate=data.get("tax_rate", 0),
            category_id=data.get("category_id"),
            unit=data.get("unit", "pcs"),
            is_tax_exempt=data.get("is_tax_exempt", False),
        )

        # Every product gets an inventory row at creation time.
        self.inventory_repo.create(
            product_id=product.id,
            quantity=data.get("initial_stock", 0),
            low_stock_threshold=data.get("low_stock_threshold", 5),
        )

        if data.get("generate_barcode") and not barcode:
            self.barcode_service.assign_barcode(product)

        self.audit_service.log(actor_id, "product.create", "product", product.id)
        return product

    def update_product(self, actor_id, product_id, data):
        product = self.get_product(product_id)

        if "sku" in data and data["sku"] and self.repo.sku_exists(data["sku"], exclude_id=product_id):
            raise ConflictError("A product with this SKU already exists.")
        if "barcode" in data and data["barcode"] and self.repo.barcode_exists(data["barcode"], exclude_id=product_id):
            raise ConflictError("A product with this barcode already exists.")
        if data.get("category_id") and not self.category_repo.get_by_id(data["category_id"]):
            raise NotFoundError("Category not found.")

        for key, value in data.items():
            if value is None:
                continue
            old_value = getattr(product, key, None)
            if key in TRACKED_FIELDS and str(old_value) != str(value):
                self.history_repo.create(
                    product_id=product.id, change_type=TRACKED_FIELDS[key], field_name=key,
                    old_value=str(old_value) if old_value is not None else None,
                    new_value=str(value), changed_by_id=actor_id,
                )
            setattr(product, key, value)
        db.session.commit()
        self.audit_service.log(actor_id, "product.update", "product", product.id, details=data)
        return product

    def delete_product(self, actor_id, product_id):
        """Archive (soft-delete) a product."""
        product = self.get_product(product_id)
        product.is_active = False
        db.session.commit()
        self.history_repo.create(product_id=product.id, change_type="archive", changed_by_id=actor_id)
        self.audit_service.log(actor_id, "product.deactivate", "product", product.id)
        return product

    def restore_product(self, actor_id, product_id):
        """Restore a previously archived product."""
        product = self.get_product(product_id)
        product.is_active = True
        db.session.commit()
        self.history_repo.create(product_id=product.id, change_type="restore", changed_by_id=actor_id)
        self.audit_service.log(actor_id, "product.restore", "product", product.id)
        return product

    def upload_image(self, actor_id, product_id, file_storage):
        product = self.get_product(product_id)
        if not allowed_file(file_storage.filename):
            raise ConflictError("Unsupported image file type.")

        folder = os.path.join(current_app.config["UPLOAD_FOLDER"], "products")
        old_filename = product.image_filename
        filename, _ = save_upload(file_storage, folder)

        product.image_filename = filename
        db.session.commit()

        if old_filename:
            delete_file(os.path.join(folder, old_filename))

        self.history_repo.create(product_id=product.id, change_type="image", field_name="image_filename",
                                  old_value=old_filename, new_value=filename, changed_by_id=actor_id)
        self.audit_service.log(actor_id, "product.image_upload", "product", product.id)
        return product

    def get_history(self, product_id):
        return self.history_repo.get_for_product(product_id)
