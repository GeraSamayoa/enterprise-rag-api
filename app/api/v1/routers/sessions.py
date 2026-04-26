from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import NOT_FOUND, SUCCESS_CREATED, SUCCESS_RETRIEVED
from app.core.responses import success_response
from app.core.security import get_current_user
from app.infrastructure.db.models.chat_message import ChatMessage
from app.infrastructure.db.models.chat_session import ChatSession
from app.infrastructure.db.models.user import User
from app.infrastructure.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.session import CreateChatSessionRequest

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    payload: CreateChatSessionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    session = ChatSession(
        user_id=current_user.id,
        title=payload.title or "Nueva conversación",
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return success_response(
        data={
            "id": session.id,
            "title": session.title,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
        },
        message=SUCCESS_CREATED,
        code=201,
    )


@router.get("", response_model=ApiResponse)
def list_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    sessions = db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.updated_at.desc())
    ).scalars().all()

    items = [
        {
            "id": session.id,
            "title": session.title,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
        }
        for session in sessions
    ]

    return success_response(
        data={
            "total": len(items),
            "items": items,
        },
        message=SUCCESS_RETRIEVED,
        code=200,
    )


@router.get("/{session_id}/messages", response_model=ApiResponse)
def list_session_messages(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    chat_session = db.get(ChatSession, session_id)

    if not chat_session or chat_session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=NOT_FOUND,
        )

    messages = db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    ).scalars().all()

    items = [
        {
            "id": message.id,
            "session_id": message.session_id,
            "role": message.role,
            "content": message.content,
            "created_at": message.created_at.isoformat(),
        }
        for message in messages
    ]

    return success_response(
        data={
            "session_id": session_id,
            "total": len(items),
            "items": items,
        },
        message=SUCCESS_RETRIEVED,
        code=200,
    )