"""Receipt & barcode label template storage (backend for the visual designer)."""
from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

from app.core.middleware.auth_middleware import current_user_id
from app.core.security.permissions import permission_required
from app.core.utils.response import success_response
from app.schemas.template_schema import (
    ReceiptTemplateCreateSchema, ReceiptTemplateUpdateSchema,
    LabelTemplateCreateSchema, LabelTemplateUpdateSchema,
)
from app.services.template_service import TemplateService

blp = Blueprint("templates", __name__, url_prefix="/api/v1/templates",
                description="Receipt & label designer templates")


@blp.route("/receipts")
class ReceiptTemplatesListResource(MethodView):
    @jwt_required()
    def get(self):
        templates = TemplateService().list_receipt_templates()
        return success_response([t.to_dict() for t in templates])

    @jwt_required()
    @permission_required("settings.manage")
    @blp.arguments(ReceiptTemplateCreateSchema)
    def post(self, data):
        template = TemplateService().create_receipt_template(current_user_id(), **data)
        return success_response(template.to_dict(), "Receipt template created", 201)


@blp.route("/receipts/<int:template_id>")
class ReceiptTemplateDetailResource(MethodView):
    @jwt_required()
    def get(self, template_id):
        template = TemplateService().get_receipt_template(template_id)
        return success_response(template.to_dict())

    @jwt_required()
    @permission_required("settings.manage")
    @blp.arguments(ReceiptTemplateUpdateSchema)
    def patch(self, data, template_id):
        template = TemplateService().update_receipt_template(current_user_id(), template_id, **data)
        return success_response(template.to_dict(), "Receipt template updated")

    @jwt_required()
    @permission_required("settings.manage")
    def delete(self, template_id):
        TemplateService().delete_receipt_template(current_user_id(), template_id)
        return success_response(None, "Receipt template deleted")


@blp.route("/receipts/<int:template_id>/set-default")
class ReceiptTemplateSetDefaultResource(MethodView):
    @jwt_required()
    @permission_required("settings.manage")
    def post(self, template_id):
        template = TemplateService().set_default_receipt_template(current_user_id(), template_id)
        return success_response(template.to_dict(), "Default receipt template updated")


@blp.route("/labels")
class LabelTemplatesListResource(MethodView):
    @jwt_required()
    def get(self):
        templates = TemplateService().list_label_templates()
        return success_response([t.to_dict() for t in templates])

    @jwt_required()
    @permission_required("settings.manage")
    @blp.arguments(LabelTemplateCreateSchema)
    def post(self, data):
        template = TemplateService().create_label_template(current_user_id(), **data)
        return success_response(template.to_dict(), "Label template created", 201)


@blp.route("/labels/<int:template_id>")
class LabelTemplateDetailResource(MethodView):
    @jwt_required()
    def get(self, template_id):
        template = TemplateService().get_label_template(template_id)
        return success_response(template.to_dict())

    @jwt_required()
    @permission_required("settings.manage")
    @blp.arguments(LabelTemplateUpdateSchema)
    def patch(self, data, template_id):
        template = TemplateService().update_label_template(current_user_id(), template_id, **data)
        return success_response(template.to_dict(), "Label template updated")

    @jwt_required()
    @permission_required("settings.manage")
    def delete(self, template_id):
        TemplateService().delete_label_template(current_user_id(), template_id)
        return success_response(None, "Label template deleted")


@blp.route("/labels/<int:template_id>/set-default")
class LabelTemplateSetDefaultResource(MethodView):
    @jwt_required()
    @permission_required("settings.manage")
    def post(self, template_id):
        template = TemplateService().set_default_label_template(current_user_id(), template_id)
        return success_response(template.to_dict(), "Default label template updated")
