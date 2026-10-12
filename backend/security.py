from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError

from backend.config import Settings

_hasher = PasswordHasher()
# Equal-cost verification for unknown usernames without a database write.
_dummy_hash = _hasher.hash("unused-dummy-password")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    try:
        verified = _hasher.verify(password_hash or _dummy_hash, password)
        return bool(password_hash) and verified
    except (VerificationError, InvalidHashError):
        return False


def make_token(user_id: int, settings: Settings) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode({"sub": str(user_id), "iat": now,
                       "exp": now + timedelta(minutes=settings.access_token_minutes),
                       "iss": "bt3-backend", "aud": "bt3-api"},
                      settings.jwt_secret.get_secret_value(), algorithm="HS256")


def read_token(token: str, settings: Settings) -> int:
    payload = jwt.decode(token, settings.jwt_secret.get_secret_value(),
                         algorithms=["HS256"], issuer="bt3-backend", audience="bt3-api",
                         options={"require": ["sub", "iat", "exp"]})
    return int(payload["sub"])
