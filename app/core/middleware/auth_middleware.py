"""Helpers for retrieving the currently authenticated user inside a request."""
from flask_jwt_extended import get_jwt_identity, get_current_user, jwt_required


def current_user():
    """Return the authenticated User model instance (requires @jwt_required())."""
    return get_current_user()


def current_user_id():
    return get_jwt_identity()


auth_required = jwt_required
