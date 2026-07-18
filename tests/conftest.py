import pytest

from app import create_app
from app.config import TestingConfig
from app.extensions import db as _db
from app.core.security.roles import DEFAULT_ROLE_PERMISSIONS
from app.core.security.password import hash_password


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    from app.core.middleware.rate_limit import _buckets
    _buckets.clear()
    yield
    _buckets.clear()


@pytest.fixture()
def app():
    application = create_app(TestingConfig)
    with application.app_context():
        _db.create_all()
        _seed(application)
        from app.services.settings_service import SettingsService
        SettingsService.clear_cache()
        yield application
        SettingsService.clear_cache()
        _db.session.remove()
        _db.drop_all()


def _seed(application):
    from app.models.role import Role
    from app.models.permission import Permission
    from app.models.user import User

    permission_cache = {}

    def get_or_create_permission(code):
        if code in permission_cache:
            return permission_cache[code]
        perm = Permission.query.filter_by(code=code).first()
        if not perm:
            perm = Permission(code=code)
            _db.session.add(perm)
            _db.session.flush()
        permission_cache[code] = perm
        return perm

    for role_name, perm_codes in DEFAULT_ROLE_PERMISSIONS.items():
        role = Role(name=role_name, description=f"Default {role_name}")
        _db.session.add(role)
        _db.session.flush()
        perms = [get_or_create_permission(code) for code in perm_codes if code != "*"]
        role.permissions = perms

    _db.session.commit()

    admin_role = Role.query.filter_by(name="admin").first()
    admin = User(
        username="admin", full_name="Admin", password_hash=hash_password("admin123"),
        role_id=admin_role.id,
    )
    _db.session.add(admin)
    _db.session.commit()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def auth_headers(client):
    resp = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    token = resp.get_json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}
