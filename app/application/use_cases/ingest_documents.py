from pathlib import Path

from sqlalchemy.orm import Session

from app.infrastructure.db.models.document import Document
from app.infrastructure.db.models.document_chunk import DocumentChunk
from app.infrastructure.parsing.text_extractors import extract_text_from_file
from app.rag.chunking.text_chunker import chunk_text


def ingest_document_file(
    db: Session,
    file_path: str,
    original_file_name: str,
    chunk_size: int,
    chunk_overlap: int,
) -> dict:
    path = Path(original_file_name)
    extracted_text, extracted_metadata = extract_text_from_file(file_path)

    document = Document(
        title=path.stem,
        source_type="document",
        source_subtype=path.suffix.lower().replace(".", ""),
        file_name=original_file_name,
        source_identifier=original_file_name,
        metadata_json={
            **extracted_metadata,
            "original_file_name": original_file_name,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
        },
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    db.add(document)
    db.flush()

    chunks = chunk_text(
        text=extracted_text,
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
                    "file_name": original_file_name,
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