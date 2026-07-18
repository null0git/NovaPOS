from app.extensions import db
from app.models._base import TimestampMixin, SerializerMixin

role_permissions = db.Table(
    "role_permissions",
    db.Column("role_id", db.Integer, db.ForeignKey("roles.id"), primary_key=True),
    db.Column("permission_id", db.Integer, db.ForeignKey("permissions.id"), primary_key=True),
)


class Permission(db.Model, TimestampMixin, SerializerMixin):
    __tablename__ = "permissions"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(100), unique=True, nullable=False)  # e.g. "products.manage"
    description = db.Column(db.String(255))

    def __repr__(self):
        return f"<Permission {self.code}>"
