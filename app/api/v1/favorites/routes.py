"""Cashier favorites / quick-access endpoints."""
from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

from app.core.middleware.auth_middleware import current_user_id
from app.core.security.permissions import permission_required
from app.core.utils.response import success_response
from app.services.favorites_service import FavoritesService

blp = Blueprint("favorites", __name__, url_prefix="/api/v1/favorites", description="Cashier favorite products")


@blp.route("")
class FavoritesListResource(MethodView):
    @jwt_required()
    def get(self):
        favorites = FavoritesService().list_favorites(current_user_id())
        return success_response([f.to_dict() for f in favorites])


@blp.route("/<int:product_id>")
class FavoriteToggleResource(MethodView):
    @jwt_required()
    @permission_required("sales.create", "sales.manage")
    def post(self, product_id):
        favorite = FavoritesService().pin(current_user_id(), product_id)
        return success_response(favorite.to_dict(), "Pinned to favorites", 201)

    @jwt_required()
    @permission_required("sales.create", "sales.manage")
    def delete(self, product_id):
        FavoritesService().unpin(current_user_id(), product_id)
        return success_response(None, "Removed from favorites")


@blp.route("/recently-sold")
class RecentlySoldResource(MethodView):
    @jwt_required()
    def get(self):
        products = FavoritesService().recently_sold(current_user_id())
        return success_response([p.to_dict() for p in products])


@blp.route("/frequently-sold")
class FrequentlySoldResource(MethodView):
    @jwt_required()
    def get(self):
        products = FavoritesService().frequently_sold(current_user_id())
        return success_response([p.to_dict() for p in products])
