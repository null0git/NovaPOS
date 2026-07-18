from app.models.product import Product
from app.repositories.base_repository import BaseRepository


class ProductRepository(BaseRepository):
    model = Product

    def get_by_sku(self, sku):
        return Product.query.filter_by(sku=sku).first()

    def get_by_barcode(self, barcode):
        return Product.query.filter_by(barcode=barcode).first()

    def sku_exists(self, sku, exclude_id=None):
        query = Product.query.filter_by(sku=sku)
        if exclude_id:
            query = query.filter(Product.id != exclude_id)
        return query.first() is not None

    def barcode_exists(self, barcode, exclude_id=None):
        query = Product.query.filter_by(barcode=barcode)
        if exclude_id:
            query = query.filter(Product.id != exclude_id)
        return query.first() is not None

    def get_active(self):
        return Product.query.filter_by(is_active=True)

    def get_by_category(self, category_id):
        return Product.query.filter_by(category_id=category_id)
