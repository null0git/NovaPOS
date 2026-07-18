from app.models.product_history import ProductHistory
from app.repositories.base_repository import BaseRepository


class ProductHistoryRepository(BaseRepository):
    model = ProductHistory

    def get_for_product(self, product_id):
        return ProductHistory.query.filter_by(product_id=product_id).order_by(
            ProductHistory.created_at.desc()
        )
