"""Global search endpoint — products, variants, categories, customers, users, sales/receipts."""
from flask import request
from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

from app.core.utils.response import success_response, error_response
from app.services.search_service import SearchService

blp = Blueprint("search", __name__, url_prefix="/api/v1/search", description="Global search")


@blp.route("")
class GlobalSearchResource(MethodView):
    @jwt_required()
    def get(self):
        query = request.args.get("q", "").strip()
        if not query or len(query) < 2:
            return error_response("Provide a search query of at least 2 characters (?q=...).", 422)
        return success_response(SearchService().global_search(query))
