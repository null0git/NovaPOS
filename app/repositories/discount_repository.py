from app.models.discount_log import DiscountLog
from app.repositories.base_repository import BaseRepository


class DiscountRepository(BaseRepository):
    model = DiscountLog

    def get_for_sale(self, sale_id):
        return DiscountLog.query.filter_by(sale_id=sale_id)
