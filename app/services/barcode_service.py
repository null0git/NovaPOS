"""Business logic for generating and looking up product barcodes."""
import os
import uuid

from flask import current_app

from app.core.middleware.error_handler import NotFoundError, ConflictError
from app.core.utils.barcode import generate_barcode_image
from app.core.utils.datetime_utils import utcnow
from app.extensions import db
from app.repositories.product_repository import ProductRepository
from app.repositories.generated_barcode_repository import GeneratedBarcodeRepository
from app.services.settings_service import SettingsService


class BarcodeService:
    def __init__(self):
        self.product_repo = ProductRepository()
        self.generated_repo = GeneratedBarcodeRepository()
        self.settings_service = SettingsService()

    def generate_code(self):
        """Generate a unique numeric-style barcode value."""
        return str(uuid.uuid4().int)[:12]

    def _allow_duplicate_manufacturer_barcodes(self):
        return bool(self.settings_service.get("allow_duplicate_manufacturer_barcodes") or False)

    def register_manufacturer_barcode(self, product, code):
        """
        Register a manufacturer barcode scanned on the product (as opposed to an
        internally generated one). Ignores no-op re-scans of the same code on the
        same product; enforces uniqueness across products unless configured to allow it.
        """
        if product.barcode == code:
            return product  # duplicate scan of the same product/code: no-op

        if not self._allow_duplicate_manufacturer_barcodes():
            existing = self.product_repo.get_by_barcode(code)
            if existing and existing.id != product.id:
                raise ConflictError(
                    f"Barcode already registered to '{existing.name}'. Enable "
                    f"'allow_duplicate_manufacturer_barcodes' in settings to allow this."
                )

        product.barcode = code
        db.session.commit()
        return product

    def assign_barcode(self, product, code=None):
        code = code or self.generate_code()
        if self.product_repo.barcode_exists(code, exclude_id=product.id) and not self._allow_duplicate_manufacturer_barcodes():
            raise ConflictError("This barcode is already assigned to another product.")

        folder = os.path.join(current_app.config["UPLOAD_FOLDER"], "products", "barcodes")
        filename = generate_barcode_image(code, folder)

        product.barcode = code
        product.barcode_image_filename = filename
        db.session.commit()
        return product

    def lookup_by_barcode(self, code):
        product = self.product_repo.get_by_barcode(code)
        if not product:
            # Also check individually-generated internal barcodes (batch labels).
            generated = self.generated_repo.get_by_code(code)
            if generated:
                return generated.product
            raise NotFoundError("No product found for this barcode.")
        return product

    def bulk_generate(self, actor_id, product_id, quantity, batch_label=None):
        """Generate `quantity` unique internal barcodes for a product (e.g. 100 for a new stock batch)."""
        product = self.product_repo.get_by_id(product_id)
        if not product:
            raise NotFoundError("Product not found.")
        if quantity < 1 or quantity > 5000:
            raise ConflictError("Quantity must be between 1 and 5000 per batch.")

        label = batch_label or f"Batch {utcnow().strftime('%Y-%m-%d %H:%M')}"
        generated = []
        for _ in range(quantity):
            code = self.generate_code()
            while self.generated_repo.get_by_code(code) or self.product_repo.get_by_barcode(code):
                code = self.generate_code()
            entry = self.generated_repo.create(product_id=product.id, code=code, batch_label=label)
            generated.append(entry)

        return generated

    def list_generated_for_product(self, product_id):
        return self.generated_repo.get_for_product(product_id)

    def mark_printed(self, barcode_ids):
        from app.models.generated_barcode import GeneratedBarcode
        GeneratedBarcode.query.filter(GeneratedBarcode.id.in_(barcode_ids)).update(
            {"printed": True, "printed_at": utcnow()}, synchronize_session=False
        )
        db.session.commit()
