"""JWT creation helpers and identity/claims callbacks registered on the JWTManager."""
from flask_jwt_extended import create_access_token, create_refresh_token

from app.extensions import jwt


def build_user_claims(user) -> dict:
    """Extra claims embedded in every token issued for `user`."""
    permissions = []
    if user.role:
        permissions = [p.code for p in user.role.permissions] if user.role.permissions else []
        if user.role.name == "admin":
            permissions = ["*"]
    return {
        "role": user.role.name if user.role else None,
        "permissions": permissions,
        "username": user.username,
        "full_name": user.full_name,
    }


def issue_tokens(user):
    claims = build_user_claims(user)
    access_token = create_access_token(identity=str(user.id), additional_claims=claims)
    refresh_token = create_refresh_token(identity=str(user.id), additional_claims=claims)
    return access_token, refresh_token


def issue_tokens_with_metadata(user):
    """Like issue_tokens, but also returns the access token's jti/expiry for session tracking."""
    from flask_jwt_extended import decode_token
    access_token, refresh_token = issue_tokens(user)
    decoded = decode_token(access_token)
    return access_token, refresh_token, decoded["jti"], decoded["exp"]


@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    from app.repositories.user_repository import UserRepository
    identity = jwt_data["sub"]
    return UserRepository().get_by_id(int(identity))


@jwt.additional_claims_loader
def add_claims(identity):
    from app.repositories.user_repository import UserRepository
    user = UserRepository().get_by_id(int(identity))
    if not user:
        return {}
    return build_user_claims(user)


@jwt.token_in_blocklist_loader
def check_if_token_revoked(_jwt_header, jwt_payload):
    """Used for forced logout / session revocation (see SessionService)."""
    from app.services.session_service import SessionService
    jti = jwt_payload["jti"]
    try:
        return SessionService().is_revoked(jti)
    except Exception:
        # If the sessions table isn't ready yet (e.g. during initial migration),
        # fail open rather than locking everyone out.
        return False
