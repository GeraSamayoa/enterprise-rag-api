from sqlalchemy import Boolean, ForeignKey, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base


class RetrievedChunkLog(Base):
    __tablename__ = "retrieved_chunks_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    query_log_id: Mapped[int] = mapped_column(ForeignKey("query_logs.id", ondelete="CASCADE"), index=True)
    chunk_id: Mapped[int] = mapped_column(ForeignKey("document_chunks.id", ondelete="CASCADE"), index=True)
    retrieval_rank: Mapped[int] = mapped_column(Integer)
    retrieval_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    rerank_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    was_used_in_prompt: Mapped[bool] = mapped_column(Boolean, default=True)