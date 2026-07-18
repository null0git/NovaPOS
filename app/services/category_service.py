"""Business logic for product categories."""
from app.core.middleware.error_handler import ConflictError, NotFoundError
from app.extensions import db
from app.repositories.category_repository import CategoryRepository
from app.services.audit_service import AuditService


class CategoryService:
    def __init__(self):
        self.repo = CategoryRepository()
        self.audit_service = AuditService()

    def list_categories(self, active_only=False):
        return self.repo.get_active() if active_only else self.repo.get_all()

    def get_category(self, category_id):
        category = self.repo.get_by_id(category_id)
        if not category:
            raise NotFoundError("Category not found.")
        return category

    def create_category(self, actor_id, name, description=None, parent_id=None):
        if self.repo.name_exists(name):
            raise ConflictError("A category with this name already exists.")
        if parent_id:
            self.get_category(parent_id)  # validates existence
        category = self.repo.create(name=name, description=description, parent_id=parent_id)
        self.audit_service.log(actor_id, "category.create", "category", category.id)
        return category

    def update_category(self, actor_id, category_id, **fields):
        category = self.get_category(category_id)
        name = fields.get("name")
        if name and self.repo.name_exists(name, exclude_id=category_id):
            raise ConflictError("A category with this name already exists.")
        for key, value in fields.items():
            if value is not None:
                setattr(category, key, value)
        db.session.commit()
        self.audit_service.log(actor_id, "category.update", "category", category.id, details=fields)
        return category

    def delete_category(self, actor_id, category_id):
        category = self.get_category(category_id)
        if category.products:
            raise ConflictError("Cannot delete a category that still has products assigned.")
        self.repo.delete(category)
        self.audit_service.log(actor_id, "category.delete", "category", category_id)
