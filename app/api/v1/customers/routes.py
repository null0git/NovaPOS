"""Customer profile endpoints."""
from flask import request, Response
from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

from app.core.middleware.auth_middleware import current_user_id
from app.core.security.permissions import permission_required
from app.core.utils.pagination import paginate_query
from app.core.utils.response import success_response
from app.schemas.customer_schema import CustomerCreateSchema, CustomerUpdateSchema
from app.services.customer_service import CustomerService

blp = Blueprint("customers", __name__, url_prefix="/api/v1/customers", description="Customer profiles")


@blp.route("/export.csv")
class CustomersExportCSVResource(MethodView):
    @jwt_required()
    @permission_required("customers.manage", "reports.view")
    def get(self):
        from app.services.import_export_service import ImportExportService
        data = ImportExportService().export_customers_csv()
        return Response(data, mimetype="text/csv",
                         headers={"Content-Disposition": 'attachment; filename="customers.csv"'})


@blp.route("")
class CustomersListResource(MethodView):
    @jwt_required()
    def get(self):
        active_only = request.args.get("active_only", "false").lower() == "true"
        items, meta = paginate_query(CustomerService().list_customers(active_only))
        return success_response([c.to_dict() for c in items], meta=meta)

    @jwt_required()
    @permission_required("customers.manage")
    @blp.arguments(CustomerCreateSchema)
    def post(self, data):
        customer = CustomerService().create_customer(current_user_id(), **data)
        return success_response(customer.to_dict(), "Customer created", 201)


@blp.route("/<int:customer_id>")
class CustomerDetailResource(MethodView):
    @jwt_required()
    def get(self, customer_id):
        customer = CustomerService().get_customer(customer_id)
        return success_response(customer.to_dict())

    @jwt_required()
    @permission_required("customers.manage")
    @blp.arguments(CustomerUpdateSchema)
    def patch(self, data, customer_id):
        customer = CustomerService().update_customer(current_user_id(), customer_id, **data)
        return success_response(customer.to_dict(), "Customer updated")

    @jwt_required()
    @permission_required("customers.manage")
    def delete(self, customer_id):
        CustomerService().deactivate_customer(current_user_id(), customer_id)
        return success_response(None, "Customer deactivated")


@blp.route("/<int:customer_id>/purchase-history")
class CustomerPurchaseHistoryResource(MethodView):
    @jwt_required()
    def get(self, customer_id):
        sales = CustomerService().purchase_history(customer_id)
        return success_response([s.to_dict() for s in sales])
