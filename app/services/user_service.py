"""Business logic for managing user accounts and their roles."""
from app.core.middleware.error_handler import ConflictError, NotFoundError
from app.core.security.password import hash_password
from app.extensions import db
from app.repositories.user_repository import UserRepository
from app.repositories.role_repository import RoleRepository
from app.services.audit_service import AuditService


class UserService:
    def __init__(self):
        self.repo = UserRepository()
        self.role_repo = RoleRepository()
        self.audit_service = AuditService()

    def list_users(self):
        return self.repo.get_all()

    def get_user(self, user_id):
        user = self.repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found.")
        return user

    def create_user(self, actor_id, username, full_name, password, role_name, email=None, phone=None):
        if self.repo.username_exists(username):
            raise ConflictError("Username already exists.")
        if email and self.repo.email_exists(email):
            raise ConflictError("Email already in use.")
        role = self.role_repo.get_by_name(role_name)
        if not role:
            raise NotFoundError(f"Role '{role_name}' does not exist.")

        user = self.repo.create(
            username=username, full_name=full_name, email=email, phone=phone,
            password_hash=hash_password(password), role_id=role.id,
        )
        self.audit_service.log(actor_id, "user.create", "user", user.id)
        return user

    def update_user(self, actor_id, user_id, **fields):
        user = self.get_user(user_id)
        role_name = fields.pop("role_name", None)
        if role_name:
            role = self.role_repo.get_by_name(role_name)
            if not role:
                raise NotFoundError(f"Role '{role_name}' does not exist.")
            user.role_id = role.id
        for key, value in fields.items():
            if value is not None:
                setattr(user, key, value)
        db.session.commit()
        self.audit_service.log(actor_id, "user.update", "user", user.id, details=fields)
        return user

    def deactivate_user(self, actor_id, user_id):
        user = self.get_user(user_id)
        user.is_active = False
        db.session.commit()
        self.audit_service.log(actor_id, "user.deactivate", "user", user.id)
        return user

    def reactivate_user(self, actor_id, user_id):
        user = self.get_user(user_id)
        user.is_active = True
        db.session.commit()
        self.audit_service.log(actor_id, "user.reactivate", "user", user.id)
        return user

    def reset_password(self, actor_id, user_id, new_password):
        user = self.get_user(user_id)
        user.password_hash = hash_password(new_password)
        db.session.commit()
        self.audit_service.log(actor_id, "user.reset_password", "user", user.id)
        return user
