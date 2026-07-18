from app.models.user import User
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository):
    model = User

    def get_by_username(self, username):
        return User.query.filter_by(username=username).first()

    def get_by_email(self, email):
        return User.query.filter_by(email=email).first()

    def username_exists(self, username):
        return User.query.filter_by(username=username).first() is not None

    def email_exists(self, email):
        return User.query.filter_by(email=email).first() is not None
