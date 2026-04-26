from datetime import datetime, timedelta, timezone
from jose import jwt

from app.core.config import settings


def create_access_token(user_id: int, email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "email": email,
        "type": "access",
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: int, email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_token_expire_days)
    payload = {
        "sub": str(user_id),
        "email": email,
        "type": "refresh",
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_refresh_secret_key, algorithm=settings.jwt_algorithm)