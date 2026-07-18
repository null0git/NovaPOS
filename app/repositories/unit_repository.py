from app.models.product_unit import ProductUnit
from app.repositories.base_repository import BaseRepository


class UnitRepository(BaseRepository):
    model = ProductUnit

    def get_by_barcode(self, barcode):
        return ProductUnit.query.filter_by(barcode=barcode).first()

    def barcode_exists(self, barcode, exclude_id=None):
        query = ProductUnit.query.filter_by(barcode=barcode)
        if exclude_id:
            query = query.filter(ProductUnit.id != exclude_id)
        return query.first() is not None

    def get_for_product(self, product_id):
        return ProductUnit.query.filter_by(product_id=product_id)
