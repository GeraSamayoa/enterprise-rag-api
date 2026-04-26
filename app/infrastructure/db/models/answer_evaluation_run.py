from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base


class AnswerEvaluationRun(Base):
    __tablename__ = "answer_evaluation_runs"

    id: Mapped[int] = mapped_column(primary_key=True)

    top_k: Mapped[int] = mapped_column(Integer)
    retrieval_mode: Mapped[str] = mapped_column(String(50))
    embedding_model_key: Mapped[str] = mapped_column(String(50))
    use_reranking: Mapped[bool]
    rerank_top_n: Mapped[int] = mapped_column(Integer)

    llm_provider: Mapped[str] = mapped_column(String(50))
    llm_model: Mapped[str | None] = mapped_column(String(255), nullable=True)

    mean_answer_length: Mapped[float] = mapped_column(Float)
    mean_used_fragments: Mapped[float] = mapped_column(Float)
    mean_sources: Mapped[float] = mapped_column(Float)
    evidence_coverage_score: Mapped[float] = mapped_column(Float)
    no_evidence_rate: Mapped[float] = mapped_column(Float)

    metrics_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)