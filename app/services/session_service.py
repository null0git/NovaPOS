"""
Business logic for session management: every issued access token is tracked
as a UserSession row so admins can see who's logged in, on what device/
terminal, review login history, and force a specific session (or all of a
user's sessions) to log out by revoking it.
"""
from datetime import datetime, timezone

from app.core.middleware.error_handler import NotFoundError
from app.core.utils.datetime_utils import utcnow
from app.extensions import db
from app.repositories.session_repository import SessionRepository


class SessionService:
    def __init__(self):
        self.repo = SessionRepository()

    def create_session(self, user_id, jti, expires_at, device_info=None, terminal_id=None,
                        ip_address=None, user_agent=None):
        return self.repo.create(
            user_id=user_id, jti=jti, expires_at=expires_at, device_info=device_info,
            terminal_id=terminal_id, ip_address=ip_address, user_agent=user_agent,
            last_seen_at=utcnow(),
        )

    def touch_session(self, jti):
        session = self.repo.get_by_jti(jti)
        if session:
            session.last_seen_at = utcnow()
            db.session.commit()
        return session

    def is_revoked(self, jti):
        session = self.repo.get_by_jti(jti)
        if not session:
            return False  # unknown session (e.g. issued before this feature existed)
        if session.revoked:
            return True
        if session.expires_at and session.expires_at.replace(tzinfo=timezone.utc) < utcnow():
            return True
        return False

    def list_active_for_user(self, user_id):
        return self.repo.get_active_for_user(user_id)

    def list_all_active(self):
        return self.repo.get_active()

    def login_history(self, user_id):
        return self.repo.get_all_for_user(user_id)

    def revoke(self, session_id):
        session = self.repo.get_by_id(session_id)
        if not session:
            raise NotFoundError("Session not found.")
        session.revoked = True
        session.revoked_at = utcnow()
        db.session.commit()
        return session

    def revoke_all_for_user(self, user_id):
        sessions = self.repo.get_active_for_user(user_id).all()
        for session in sessions:
            session.revoked = True
            session.revoked_at = utcnow()
        db.session.commit()
        return sessions
