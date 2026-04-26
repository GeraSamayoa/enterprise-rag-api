from sqlalchemy import select, tuple_
from sqlalchemy.orm import Session

from app.infrastructure.db.models.chunk_embedding import ChunkEmbedding
from app.infrastructure.db.models.document_chunk import DocumentChunk
from app.infrastructure.embeddings.provider import embed_texts


def index_embeddings_for_model(
    db: Session,
    model_key: str = "primary",
    batch_size: int = 64,
) -> dict:
    existing_pairs = db.execute(
        select(ChunkEmbedding.chunk_id, ChunkEmbedding.embedding_model)
        .where(ChunkEmbedding.embedding_model == model_key)
    ).all()

    existing_chunk_ids = {chunk_id for chunk_id, _ in existing_pairs}

    chunks = db.execute(
        select(DocumentChunk)
        .order_by(DocumentChunk.id.asc())
    ).scalars().all()

    chunks_to_index = [chunk for chunk in chunks if chunk.id not in existing_chunk_ids]

    total_indexed = 0

    for start in range(0, len(chunks_to_index), batch_size):
        batch = chunks_to_index[start:start + batch_size]
        texts = [chunk.text for chunk in batch]

        vectors = embed_texts(texts=texts, model_key=model_key)

        for chunk, vector in zip(batch, vectors, strict=True):
            db.add(
                ChunkEmbedding(
                    chunk_id=chunk.id,
                    embedding_model=model_key,
                    embedding=vector,
                )
            )
            total_indexed += 1

        db.commit()

    return {
        "model_key": model_key,
        "indexed_chunks": total_indexed,
        "total_chunks_in_db": len(chunks),
    }