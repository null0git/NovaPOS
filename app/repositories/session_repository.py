from app.models.session import UserSession
from app.repositories.base_repository import BaseRepository


class SessionRepository(BaseRepository):
    model = UserSession

    def get_by_jti(self, jti):
        return UserSession.query.filter_by(jti=jti).first()

    def get_active_for_user(self, user_id):
        return UserSession.query.filter_by(user_id=user_id, revoked=False)

    def get_all_for_user(self, user_id):
        return UserSession.query.filter_by(user_id=user_id).order_by(UserSession.created_at.desc())

    def get_active(self):
        return UserSession.query.filter_by(revoked=False)
