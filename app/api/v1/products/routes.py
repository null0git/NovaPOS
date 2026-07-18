"""Product catalog endpoints, including barcode lookup/generation and image upload."""
from flask import request
from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

from app.core.middleware.auth_middleware import current_user_id
from app.core.security.permissions import permission_required
from app.core.utils.pagination import paginate_query
from app.core.utils.filters import apply_search, apply_sort
from app.core.utils.response import success_response, error_response
from app.models.product import Product
from app.schemas.product_schema import ProductCreateSchema, ProductUpdateSchema
from app.services.product_service import ProductService
from app.services.barcode_service import BarcodeService

blp = Blueprint("products", __name__, url_prefix="/api/v1/products", description="Product catalog")


@blp.route("")
class ProductsListResource(MethodView):
    @jwt_required()
    def get(self):
        active_only = request.args.get("active_only", "false").lower() == "true"
        category_id = request.args.get("category_id", type=int)
        query = ProductService().list_products(active_only, category_id)
        query = apply_search(query, Product, ["name", "sku", "barcode"])
        query = apply_sort(query, Product, default_field="id")
        items, meta = paginate_query(query)
        return success_response([p.to_dict() for p in items], meta=meta)

    @jwt_required()
    @permission_required("products.manage")
    @blp.arguments(ProductCreateSchema)
    def post(self, data):
        product = ProductService().create_product(current_user_id(), data)
        return success_response(product.to_dict(), "Product created", 201)


@blp.route("/<int:product_id>")
class ProductDetailResource(MethodView):
    @jwt_required()
    def get(self, product_id):
        product = ProductService().get_product(product_id)
        return success_response(product.to_dict())

    @jwt_required()
    @permission_required("products.manage")
    @blp.arguments(ProductUpdateSchema)
    def patch(self, data, product_id):
        product = ProductService().update_product(current_user_id(), product_id, data)
        return success_response(product.to_dict(), "Product updated")

    @jwt_required()
    @permission_required("products.manage")
    def delete(self, product_id):
        ProductService().delete_product(current_user_id(), product_id)
        return success_response(None, "Product deactivated")


@blp.route("/<int:product_id>/restore")
class ProductRestoreResource(MethodView):
    @jwt_required()
    @permission_required("products.manage")
    def post(self, product_id):
        product = ProductService().restore_product(current_user_id(), product_id)
        return success_response(product.to_dict(), "Product restored")


@blp.route("/<int:product_id>/history")
class ProductHistoryResource(MethodView):
    @jwt_required()
    @permission_required("products.manage", "products.view")
    def get(self, product_id):
        history = ProductService().get_history(product_id)
        return success_response([h.to_dict() for h in history])


@blp.route("/barcode/<string:barcode>")
class ProductByBarcodeResource(MethodView):
    @jwt_required()
    def get(self, barcode):
        product = ProductService().get_by_barcode(barcode)
        return success_response(product.to_dict())


@blp.route("/<int:product_id>/barcode")
class ProductGenerateBarcodeResource(MethodView):
    @jwt_required()
    @permission_required("products.manage")
    def post(self, product_id):
        product = ProductService().get_product(product_id)
        code = (request.get_json(silent=True) or {}).get("code")
        product = BarcodeService().assign_barcode(product, code)
        return success_response(product.to_dict(), "Barcode assigned")


@blp.route("/<int:product_id>/image")
class ProductImageResource(MethodView):
    @jwt_required()
    @permission_required("products.manage")
    def post(self, product_id):
        if "file" not in request.files:
            return error_response("No file part in the request.", 422)
        file_storage = request.files["file"]
        if file_storage.filename == "":
            return error_response("No file selected.", 422)
        product = ProductService().upload_image(current_user_id(), product_id, file_storage)
        return success_response(product.to_dict(), "Image uploaded")
