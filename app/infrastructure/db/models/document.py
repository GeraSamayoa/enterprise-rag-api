from datetime import datetime
from sqlalchemy import String, DateTime, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    title: Mapped[str] = mapped_column(String(500))
    source_type: Mapped[str] = mapped_column(String(50))
    source_subtype: Mapped[str | None] = mapped_column(String(50), nullable=True)
    file_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_identifier: Mapped[str | None] = mapped_column(String(255), nullable=True)
    language: Mapped[str | None] = mapped_column(String(20), nullable=True)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at_source: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)

    chunk_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chunk_overlap: Mapped[int | None] = mapped_column(Integer, nullable=True)