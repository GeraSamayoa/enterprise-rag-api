from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.db.models.chat_message import ChatMessage


def get_recent_memory_messages(
    db: Session,
    session_id: int,
    limit: int = 6,
) -> list[dict]:
    messages = db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
    ).scalars().all()

    ordered = list(reversed(messages))

    return [
        {
            "role": message.role,
            "content": message.content,
        }
        for message in ordered
        if message.role in {"user", "assistant"}
    ]


def format_memory_for_prompt(memory_messages: list[dict]) -> str:
    if not memory_messages:
        return ""

    lines = []
    for message in memory_messages:
        role = "Usuario" if message["role"] == "user" else "Asistente"
        lines.append(f"{role}: {message['content']}")

    return "\n".join(lines)