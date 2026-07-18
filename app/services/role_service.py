"""Business logic for role and permission management."""
from app.core.middleware.error_handler import ConflictError, NotFoundError
from app.extensions import db
from app.repositories.role_repository import RoleRepository
from app.services.audit_service import AuditService


class RoleService:
    def __init__(self):
        self.repo = RoleRepository()
        self.audit_service = AuditService()

    def list_roles(self):
        return self.repo.get_all()

    def get_role(self, role_id):
        role = self.repo.get_by_id(role_id)
        if not role:
            raise NotFoundError("Role not found.")
        return role

    def create_role(self, actor_id, name, description=None, permission_codes=None):
        if self.repo.name_exists(name):
            raise ConflictError("A role with this name already exists.")
        role = self.repo.create(name=name, description=description)
        if permission_codes:
            role.permissions = [
                self.repo.create_permission_if_missing(code) for code in permission_codes
            ]
            db.session.commit()
        self.audit_service.log(actor_id, "role.create", "role", role.id)
        return role

    def update_role(self, actor_id, role_id, description=None, permission_codes=None):
        role = self.get_role(role_id)
        if description is not None:
            role.description = description
        if permission_codes is not None:
            role.permissions = [
                self.repo.create_permission_if_missing(code) for code in permission_codes
            ]
        db.session.commit()
        self.audit_service.log(actor_id, "role.update", "role", role.id)
        return role

    def delete_role(self, actor_id, role_id):
        role = self.get_role(role_id)
        if role.users:
            raise ConflictError("Cannot delete a role that is still assigned to users.")
        self.repo.delete(role)
        self.audit_service.log(actor_id, "role.delete", "role", role_id)
