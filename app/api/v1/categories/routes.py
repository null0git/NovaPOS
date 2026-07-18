"""Product category endpoints."""
from flask import request
from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

from app.core.middleware.auth_middleware import current_user_id
from app.core.security.permissions import permission_required
from app.core.utils.response import success_response
from app.schemas.category_schema import CategoryCreateSchema, CategoryUpdateSchema
from app.services.category_service import CategoryService

blp = Blueprint("categories", __name__, url_prefix="/api/v1/categories", description="Product categories")


@blp.route("")
class CategoriesListResource(MethodView):
    @jwt_required()
    def get(self):
        active_only = request.args.get("active_only", "false").lower() == "true"
        categories = CategoryService().list_categories(active_only)
        return success_response([c.to_dict() for c in categories])

    @jwt_required()
    @permission_required("categories.manage")
    @blp.arguments(CategoryCreateSchema)
    def post(self, data):
        category = CategoryService().create_category(current_user_id(), **data)
        return success_response(category.to_dict(), "Category created", 201)


@blp.route("/<int:category_id>")
class CategoryDetailResource(MethodView):
    @jwt_required()
    def get(self, category_id):
        category = CategoryService().get_category(category_id)
        return success_response(category.to_dict())

    @jwt_required()
    @permission_required("categories.manage")
    @blp.arguments(CategoryUpdateSchema)
    def patch(self, data, category_id):
        category = CategoryService().update_category(current_user_id(), category_id, **data)
        return success_response(category.to_dict(), "Category updated")

    @jwt_required()
    @permission_required("categories.manage")
    def delete(self, category_id):
        CategoryService().delete_category(current_user_id(), category_id)
        return success_response(None, "Category deleted")
