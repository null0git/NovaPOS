"""Permission-checking decorators for route-level authorization.

Permissions are simple dotted strings, e.g. "products.manage".
A role with the wildcard "*" permission (admin) passes every check.
"""
from functools import wraps

from flask_jwt_extended import verify_jwt_in_request, get_jwt

from app.core.utils.response import error_response


def _user_permissions_from_claims(claims) -> set:
    return set(claims.get("permissions", []))


def permission_required(*required_permissions):
    """Require the caller's JWT to include at least one of the given permissions."""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_perms = _user_permissions_from_claims(claims)
            if "*" in user_perms:
                return fn(*args, **kwargs)
            if not required_permissions or user_perms.intersection(required_permissions):
                return fn(*args, **kwargs)
            return error_response("You do not have permission to perform this action.", 403)

        return wrapper

    return decorator


def role_required(*required_roles):
    """Require the caller's JWT to carry one of the given roles."""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_role = claims.get("role")
            if user_role not in required_roles:
                return error_response("This action requires a different role.", 403)
            return fn(*args, **kwargs)

        return wrapper

    return decorator
