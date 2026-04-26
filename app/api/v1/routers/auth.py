from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.constants import (
    COULD_NOT_VALIDATE_CREDENTIALS,
    EMAIL_ALREADY_REGISTERED,
    INVALID_CREDENTIALS,
    INVALID_REFRESH_TOKEN,
    SUCCESS_CREATED,
    SUCCESS_RETRIEVED,
    UNAUTHORIZED,
    USER_INACTIVE,
    USER_NOT_FOUND,
)
from app.core.responses import success_response
from app.core.security import get_current_user
from app.infrastructure.db.models.refresh_token import RefreshToken
from app.infrastructure.db.models.user import User
from app.infrastructure.db.session import get_db
from app.infrastructure.security.jwt import create_access_token, create_refresh_token
from app.infrastructure.security.password import hash_password, verify_password
from app.schemas.auth import (
    RefreshTokenRequest,
    UserLoginRequest,
    UserRegisterRequest,
)
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserRegisterRequest, db: Session = Depends(get_db)) -> ApiResponse:
    existing_user = db.execute(
        select(User).where(User.email == payload.email)
    ).scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=EMAIL_ALREADY_REGISTERED,
        )

    user = User(
        email=payload.email,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return success_response(
        data={
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
        },
        message=SUCCESS_CREATED,
        code=201,
    )


@router.post("/login", response_model=ApiResponse)
def login_user(payload: UserLoginRequest, db: Session = Depends(get_db)) -> ApiResponse:
    user = db.execute(
        select(User).where(User.email == payload.email)
    ).scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_CREDENTIALS,
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=USER_INACTIVE,
        )

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_CREDENTIALS,
        )

    access_token = create_access_token(user.id, user.email)
    refresh_token = create_refresh_token(user.id, user.email)

    refresh_token_row = RefreshToken(
        user_id=user.id,
        token_hash=hash_password(refresh_token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_token_expire_days),
    )
    db.add(refresh_token_row)
    db.commit()

    return success_response(
        data={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        },
        message=SUCCESS_RETRIEVED,
        code=200,
    )


@router.post("/refresh", response_model=ApiResponse)
def refresh_access_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)) -> ApiResponse:
    try:
        decoded = jwt.decode(
            payload.refresh_token,
            settings.jwt_refresh_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        token_type = decoded.get("type")
        user_id = decoded.get("sub")
        email = decoded.get("email")

        if token_type != "refresh" or user_id is None or email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=INVALID_REFRESH_TOKEN,
            )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_REFRESH_TOKEN,
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

    stored_tokens = db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == user.id,
            RefreshToken.revoked_at.is_(None),
        )
    ).scalars().all()

    matched = any(
        verify_password(payload.refresh_token, token.token_hash)
        for token in stored_tokens
    )

    if not matched:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_REFRESH_TOKEN,
        )

    new_access_token = create_access_token(user.id, user.email)
    new_refresh_token = create_refresh_token(user.id, user.email)

    refresh_token_row = RefreshToken(
        user_id=user.id,
        token_hash=hash_password(new_refresh_token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_token_expire_days),
    )
    db.add(refresh_token_row)
    db.commit()

    return success_response(
        data={
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        },
        message=SUCCESS_RETRIEVED,
        code=200,
    )


@router.get("/me", response_model=ApiResponse)
def get_me(current_user: User = Depends(get_current_user)) -> ApiResponse:
    return success_response(
        data={
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "is_active": current_user.is_active,
        },
        message=SUCCESS_RETRIEVED,
        code=200,
    )