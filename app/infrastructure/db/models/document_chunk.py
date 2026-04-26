from sqlalchemy import ForeignKey, Integer, String, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    char_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    section_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    tsv: Mapped[str | None] = mapped_column(Text, nullable=True)

    chunk_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chunk_overlap: Mapped[int | None] = mapped_column(Integer, nullable=True)