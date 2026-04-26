from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.constants import COULD_NOT_VALIDATE_CREDENTIALS, USER_INACTIVE, USER_NOT_FOUND
from app.infrastructure.db.models.user import User
from app.infrastructure.db.session import get_db


bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        token_type = payload.get("type")
        user_id = payload.get("sub")

        if token_type != "access" or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=COULD_NOT_VALIDATE_CREDENTIALS,
            )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=COULD_NOT_VALIDATE_CREDENTIALS,
        ) from exc

    user = db.get(User, int(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=USER_NOT_FOUND,
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=USER_INACTIVE,
        )

    return user