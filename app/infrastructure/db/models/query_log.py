from datetime import datetime
from sqlalchemy import ForeignKey, String, DateTime, Boolean, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base


class QueryLog(Base):
    __tablename__ = "query_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    session_id: Mapped[int | None] = mapped_column(ForeignKey("chat_sessions.id", ondelete="SET NULL"), nullable=True)
    question: Mapped[str] = mapped_column(Text)
    normalized_question: Mapped[str | None] = mapped_column(Text, nullable=True)
    retrieval_mode: Mapped[str] = mapped_column(String(50))
    top_k: Mapped[int] = mapped_column(Integer)
    embedding_model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    llm_model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    used_reranker: Mapped[bool] = mapped_column(Boolean, default=False)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    retrieval_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rerank_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    llm_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    has_sufficient_evidence: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)