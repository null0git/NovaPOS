"""Business logic for alternate selling units (e.g. Sugar sold as kg/500g/250g)."""
from app.core.middleware.error_handler import ConflictError, NotFoundError
from app.extensions import db
from app.repositories.unit_repository import UnitRepository
from app.repositories.product_repository import ProductRepository
from app.services.audit_service import AuditService


class UnitService:
    def __init__(self):
        self.repo = UnitRepository()
        self.product_repo = ProductRepository()
        self.audit_service = AuditService()

    def list_for_product(self, product_id):
        return self.repo.get_for_product(product_id)

    def get_unit(self, unit_id):
        unit = self.repo.get_by_id(unit_id)
        if not unit:
            raise NotFoundError("Unit not found.")
        return unit

    def create_unit(self, actor_id, product_id, unit_name, conversion_ratio, price, barcode=None):
        product = self.product_repo.get_by_id(product_id)
        if not product:
            raise NotFoundError("Product not found.")
        if barcode and self.repo.barcode_exists(barcode):
            raise ConflictError("A unit with this barcode already exists.")

        unit = self.repo.create(
            product_id=product_id, unit_name=unit_name, conversion_ratio=conversion_ratio,
            price=price, barcode=barcode,
        )
        self.audit_service.log(actor_id, "unit.create", "product_unit", unit.id)
        return unit

    def update_unit(self, actor_id, unit_id, **fields):
        unit = self.get_unit(unit_id)
        barcode = fields.get("barcode")
        if barcode and self.repo.barcode_exists(barcode, exclude_id=unit_id):
            raise ConflictError("A unit with this barcode already exists.")
        for key, value in fields.items():
            if value is not None:
                setattr(unit, key, value)
        db.session.commit()
        self.audit_service.log(actor_id, "unit.update", "product_unit", unit.id, details=fields)
        return unit

    def delete_unit(self, actor_id, unit_id):
        unit = self.get_unit(unit_id)
        unit.is_active = False
        db.session.commit()
        self.audit_service.log(actor_id, "unit.deactivate", "product_unit", unit.id)
