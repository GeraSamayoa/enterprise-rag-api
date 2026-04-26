from datetime import datetime

from sqlalchemy import DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base


class GoldenSetQuestion(Base):
    __tablename__ = "golden_set_questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    question: Mapped[str] = mapped_column(Text)
    expected_answer: Mapped[str | None] = mapped_column(Text, nullable=True)

    expected_document_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    expected_document_ids: Mapped[list[int] | None] = mapped_column(JSON, nullable=True)

    expected_source_identifier: Mapped[str | None] = mapped_column(String(255), nullable=True)
    difficulty: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tags_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)