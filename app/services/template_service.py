"""
Backend storage for the receipt/label visual designer. The actual
drag-and-drop editing UI lives in the frontend; this just persists the
resulting layout (an opaque JSON element list) and tracks which template
is the active default for rendering.
"""
from app.core.middleware.error_handler import NotFoundError
from app.extensions import db
from app.repositories.template_repository import ReceiptTemplateRepository, LabelTemplateRepository
from app.services.audit_service import AuditService


class TemplateService:
    def __init__(self):
        self.receipt_repo = ReceiptTemplateRepository()
        self.label_repo = LabelTemplateRepository()
        self.audit_service = AuditService()

    # ---------- Receipt templates ----------

    def list_receipt_templates(self):
        return self.receipt_repo.get_all()

    def get_receipt_template(self, template_id):
        template = self.receipt_repo.get_by_id(template_id)
        if not template:
            raise NotFoundError("Receipt template not found.")
        return template

    def get_default_receipt_template(self):
        return self.receipt_repo.get_default()

    def create_receipt_template(self, actor_id, name, paper_width_mm, layout, set_default=False):
        template = self.receipt_repo.create(name=name, paper_width_mm=paper_width_mm, layout=layout)
        if set_default:
            self.set_default_receipt_template(actor_id, template.id)
        self.audit_service.log(actor_id, "receipt_template.create", "receipt_template", template.id)
        return template

    def update_receipt_template(self, actor_id, template_id, **fields):
        template = self.get_receipt_template(template_id)
        for key, value in fields.items():
            if value is not None:
                setattr(template, key, value)
        db.session.commit()
        self.audit_service.log(actor_id, "receipt_template.update", "receipt_template", template.id)
        return template

    def set_default_receipt_template(self, actor_id, template_id):
        template = self.get_receipt_template(template_id)
        self.receipt_repo.clear_default()
        template.is_default = True
        db.session.commit()
        self.audit_service.log(actor_id, "receipt_template.set_default", "receipt_template", template.id)
        return template

    def delete_receipt_template(self, actor_id, template_id):
        template = self.get_receipt_template(template_id)
        self.receipt_repo.delete(template)
        self.audit_service.log(actor_id, "receipt_template.delete", "receipt_template", template_id)

    # ---------- Label templates ----------

    def list_label_templates(self):
        return self.label_repo.get_all()

    def get_label_template(self, template_id):
        template = self.label_repo.get_by_id(template_id)
        if not template:
            raise NotFoundError("Label template not found.")
        return template

    def create_label_template(self, actor_id, name, label_size, layout, set_default=False):
        template = self.label_repo.create(name=name, label_size=label_size, layout=layout)
        if set_default:
            self.set_default_label_template(actor_id, template.id)
        self.audit_service.log(actor_id, "label_template.create", "label_template", template.id)
        return template

    def update_label_template(self, actor_id, template_id, **fields):
        template = self.get_label_template(template_id)
        for key, value in fields.items():
            if value is not None:
                setattr(template, key, value)
        db.session.commit()
        self.audit_service.log(actor_id, "label_template.update", "label_template", template.id)
        return template

    def set_default_label_template(self, actor_id, template_id):
        template = self.get_label_template(template_id)
        self.label_repo.clear_default()
        template.is_default = True
        db.session.commit()
        self.audit_service.log(actor_id, "label_template.set_default", "label_template", template.id)
        return template

    def delete_label_template(self, actor_id, template_id):
        template = self.get_label_template(template_id)
        self.label_repo.delete(template)
        self.audit_service.log(actor_id, "label_template.delete", "label_template", template_id)
