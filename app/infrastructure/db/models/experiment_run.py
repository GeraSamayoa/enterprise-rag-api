from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base


class ExperimentRun(Base):
    __tablename__ = "experiment_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    top_k: Mapped[int] = mapped_column(Integer)
    retrieval_mode: Mapped[str] = mapped_column(String(50))
    embedding_model_key: Mapped[str] = mapped_column(String(50))
    rerank_enabled: Mapped[bool] = mapped_column(Boolean)
    rerank_top_n: Mapped[int | None] = mapped_column(Integer, nullable=True)

    chunk_size_filter: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chunk_overlap_filter: Mapped[int | None] = mapped_column(Integer, nullable=True)

    mean_precision_at_k: Mapped[float] = mapped_column(Float)
    mean_recall_at_k: Mapped[float] = mapped_column(Float)
    mrr: Mapped[float] = mapped_column(Float)

    avg_latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    min_latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)

    metrics_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)