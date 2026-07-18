"""Password hashing/verification (Werkzeug's PBKDF2 implementation)."""
from werkzeug.security import generate_password_hash, check_password_hash


def hash_password(plain_password: str) -> str:
    return generate_password_hash(plain_password)


def verify_password(hashed_password: str, plain_password: str) -> bool:
    if not hashed_password or not plain_password:
        return False
    return check_password_hash(hashed_password, plain_password)
