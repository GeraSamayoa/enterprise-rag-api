from sqlalchemy.orm import Session

from app.infrastructure.db.models.document import Document
from app.infrastructure.db.models.document_chunk import DocumentChunk
from app.rag.chunking.text_chunker import chunk_text
from app.schemas.ingestion import RecordIngestionRequest


def ingest_record_as_document(
    db: Session,
    payload: RecordIngestionRequest,
    chunk_size: int,
    chunk_overlap: int,
) -> dict:
    metadata = payload.metadata or {}

    document = Document(
        external_id=payload.external_id,
        title=payload.title,
        source_type="db_record",
        source_subtype=payload.source_subtype,
        source_identifier=payload.source_identifier,
        metadata_json={
            **metadata,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
        },
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    db.add(document)
    db.flush()

    chunks = chunk_text(
        text=payload.content,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    for chunk in chunks:
        db.add(
            DocumentChunk(
                document_id=document.id,
                chunk_index=chunk.chunk_index,
                text=chunk.text,
                char_count=chunk.char_count,
                tsv=chunk.text,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                metadata_json={
                    **metadata,
                    "chunk_size": chunk_size,
                    "chunk_overlap": chunk_overlap,
                },
            )
        )

    db.commit()
    db.refresh(document)

    return {
        "document_id": document.id,
        "title": document.title,
        "source_type": document.source_type,
        "source_subtype": document.source_subtype,
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        "chunks_created": len(chunks),
    }