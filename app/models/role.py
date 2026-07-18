from app.extensions import db
from app.models._base import TimestampMixin, SerializerMixin
from app.models.permission import role_permissions


class Role(db.Model, TimestampMixin, SerializerMixin):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))

    permissions = db.relationship(
        "Permission", secondary=role_permissions, backref="roles", lazy="joined"
    )
    users = db.relationship("User", back_populates="role")

    def to_dict(self, exclude=None):
        data = super().to_dict(exclude)
        data["permissions"] = [p.code for p in self.permissions]
        return data

    def __repr__(self):
        return f"<Role {self.name}>"
