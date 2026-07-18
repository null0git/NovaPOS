from app.models.generated_barcode import GeneratedBarcode
from app.repositories.base_repository import BaseRepository


class GeneratedBarcodeRepository(BaseRepository):
    model = GeneratedBarcode

    def get_by_code(self, code):
        return GeneratedBarcode.query.filter_by(code=code).first()

    def get_for_product(self, product_id):
        return GeneratedBarcode.query.filter_by(product_id=product_id).order_by(
            GeneratedBarcode.created_at.desc()
        )
