"""Authentication business logic: login, token issuance, registration, password change."""
from datetime import datetime, timezone

from flask_jwt_extended import create_access_token, get_jwt

from app.core.middleware.error_handler import AuthError, ConflictError, NotFoundError
from app.core.security.jwt import issue_tokens_with_metadata, build_user_claims
from app.core.security.password import hash_password, verify_password
from app.core.utils.datetime_utils import utcnow
from app.extensions import db
from app.repositories.user_repository import UserRepository
from app.repositories.role_repository import RoleRepository
from app.services.audit_service import AuditService
from app.services.session_service import SessionService


class AuthService:
    def __init__(self):
        self.user_repo = UserRepository()
        self.role_repo = RoleRepository()
        self.audit_service = AuditService()
        self.session_service = SessionService()

    def login(self, username, password, ip_address=None, user_agent=None, terminal_id=None):
        user = self.user_repo.get_by_username(username)
        if not user or not verify_password(user.password_hash, password):
            raise AuthError("Invalid username or password.")
        if not user.is_active:
            raise AuthError("This account has been deactivated.")

        user.last_login_at = utcnow()
        db.session.commit()

        access_token, refresh_token, jti, exp_timestamp = issue_tokens_with_metadata(user)
        expires_at = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
        self.session_service.create_session(
            user_id=user.id, jti=jti, expires_at=expires_at,
            device_info=user_agent, terminal_id=terminal_id,
            ip_address=ip_address, user_agent=user_agent,
        )

        self.audit_service.log(user.id, "auth.login", "user", user.id, ip_address=ip_address)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user.to_dict(),
        }

    def refresh(self, identity):
        user = self.user_repo.get_by_id(int(identity))
        if not user or not user.is_active:
            raise AuthError("User no longer active.")
        claims = build_user_claims(user)
        access_token = create_access_token(identity=str(user.id), additional_claims=claims)
        return {"access_token": access_token}

    def register(self, username, full_name, password, role_name, email=None, phone=None):
        if self.user_repo.username_exists(username):
            raise ConflictError("Username already exists.")
        if email and self.user_repo.email_exists(email):
            raise ConflictError("Email already in use.")

        role = self.role_repo.get_by_name(role_name)
        if not role:
            raise NotFoundError(f"Role '{role_name}' does not exist.")

        user = self.user_repo.create(
            username=username,
            full_name=full_name,
            email=email,
            phone=phone,
            password_hash=hash_password(password),
            role_id=role.id,
        )
        self.audit_service.log(user.id, "auth.register", "user", user.id)
        return user

    def change_password(self, user, current_password, new_password):
        if not verify_password(user.password_hash, current_password):
            raise AuthError("Current password is incorrect.")
        user.password_hash = hash_password(new_password)
        db.session.commit()
        self.audit_service.log(user.id, "auth.change_password", "user", user.id)
        return user

    def get_current_permissions(self):
        claims = get_jwt()
        return claims.get("permissions", [])
