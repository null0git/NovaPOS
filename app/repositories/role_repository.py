from app.models.role import Role
from app.models.permission import Permission
from app.repositories.base_repository import BaseRepository
from app.extensions import db


class RoleRepository(BaseRepository):
    model = Role

    def get_by_name(self, name):
        return Role.query.filter_by(name=name).first()

    def name_exists(self, name, exclude_id=None):
        query = Role.query.filter_by(name=name)
        if exclude_id:
            query = query.filter(Role.id != exclude_id)
        return query.first() is not None

    def get_permission_by_code(self, code):
        return Permission.query.filter_by(code=code).first()

    def get_all_permissions(self):
        return Permission.query.all()

    def create_permission_if_missing(self, code, description=""):
        perm = self.get_permission_by_code(code)
        if perm:
            return perm
        perm = Permission(code=code, description=description)
        db.session.add(perm)
        db.session.commit()
        return perm
