from app.models.product_variant import ProductVariant
from app.repositories.base_repository import BaseRepository


class VariantRepository(BaseRepository):
    model = ProductVariant

    def get_by_sku(self, sku):
        return ProductVariant.query.filter_by(sku=sku).first()

    def get_by_barcode(self, barcode):
        return ProductVariant.query.filter_by(barcode=barcode).first()

    def sku_exists(self, sku, exclude_id=None):
        query = ProductVariant.query.filter_by(sku=sku)
        if exclude_id:
            query = query.filter(ProductVariant.id != exclude_id)
        return query.first() is not None

    def barcode_exists(self, barcode, exclude_id=None):
        query = ProductVariant.query.filter_by(barcode=barcode)
        if exclude_id:
            query = query.filter(ProductVariant.id != exclude_id)
        return query.first() is not None

    def get_for_product(self, product_id):
        return ProductVariant.query.filter_by(product_id=product_id)

    def get_low_stock(self):
        return ProductVariant.query.filter(
            ProductVariant.stock_quantity <= ProductVariant.low_stock_threshold
        )
