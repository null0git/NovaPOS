from app.models.favorite_product import FavoriteProduct
from app.repositories.base_repository import BaseRepository


class FavoriteRepository(BaseRepository):
    model = FavoriteProduct

    def get_for_user(self, user_id):
        return FavoriteProduct.query.filter_by(user_id=user_id)

    def get(self, user_id, product_id):
        return FavoriteProduct.query.filter_by(user_id=user_id, product_id=product_id).first()
