from app.extensions import db
from app.models._base import TimestampMixin, SerializerMixin


class User(db.Model, TimestampMixin, SerializerMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=True, index=True)
    full_name = db.Column(db.String(150), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_login_at = db.Column(db.DateTime(timezone=True), nullable=True)
    avatar_url = db.Column(db.String(255))

    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False)
    role = db.relationship("Role", back_populates="users")

    sales = db.relationship("Sale", back_populates="cashier", foreign_keys="Sale.cashier_id")

    def to_dict(self, exclude=None):
        exclude = set(exclude or []) | {"password_hash"}
        data = super().to_dict(exclude)
        data["role"] = self.role.name if self.role else None
        return data

    def __repr__(self):
        return f"<User {self.username}>"
