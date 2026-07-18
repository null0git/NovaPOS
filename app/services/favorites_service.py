"""
Business logic for cashier quick-access: pinned favorites, plus computed
"recently sold" and "frequently sold" lists per cashier for fast POS-screen
shortcuts.
"""
from sqlalchemy import func

from app.core.middleware.error_handler import ConflictError, NotFoundError
from app.core.utils.datetime_utils import date_range_from_period
from app.extensions import db
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.product import Product
from app.repositories.favorite_repository import FavoriteRepository
from app.repositories.product_repository import ProductRepository


class FavoritesService:
    def __init__(self):
        self.repo = FavoriteRepository()
        self.product_repo = ProductRepository()

    def list_favorites(self, user_id):
        return self.repo.get_for_user(user_id)

    def pin(self, user_id, product_id):
        if not self.product_repo.get_by_id(product_id):
            raise NotFoundError("Product not found.")
        if self.repo.get(user_id, product_id):
            raise ConflictError("This product is already pinned.")
        return self.repo.create(user_id=user_id, product_id=product_id)

    def unpin(self, user_id, product_id):
        favorite = self.repo.get(user_id, product_id)
        if not favorite:
            raise NotFoundError("This product isn't pinned.")
        self.repo.delete(favorite)

    def recently_sold(self, user_id, limit=10):
        rows = (
            db.session.query(Product, func.max(Sale.created_at).label("last_sold"))
            .join(SaleItem, SaleItem.product_id == Product.id)
            .join(Sale, SaleItem.sale_id == Sale.id)
            .filter(Sale.cashier_id == user_id, Sale.status != "voided")
            .group_by(Product.id)
            .order_by(func.max(Sale.created_at).desc())
            .limit(limit)
            .all()
        )
        return [p for p, _ in rows]

    def frequently_sold(self, user_id, limit=10, period="month"):
        start, end = date_range_from_period(period)
        rows = (
            db.session.query(Product, func.sum(SaleItem.quantity).label("qty"))
            .join(SaleItem, SaleItem.product_id == Product.id)
            .join(Sale, SaleItem.sale_id == Sale.id)
            .filter(Sale.cashier_id == user_id, Sale.status != "voided",
                    Sale.created_at >= start, Sale.created_at <= end)
            .group_by(Product.id)
            .order_by(func.sum(SaleItem.quantity).desc())
            .limit(limit)
            .all()
        )
        return [p for p, _ in rows]
