from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector

from app.infrastructure.db.base import Base


class ChunkEmbedding(Base):
    __tablename__ = "chunk_embeddings"

    chunk_id: Mapped[int] = mapped_column(ForeignKey("document_chunks.id", ondelete="CASCADE"), primary_key=True)
    embedding_model: Mapped[str] = mapped_column(String(255), primary_key=True)
    embedding: Mapped[list[float]] = mapped_column(Vector(384))