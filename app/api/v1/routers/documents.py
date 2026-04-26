from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import NOT_FOUND, SUCCESS_RETRIEVED
from app.core.responses import success_response
from app.core.security import get_current_user
from app.infrastructure.db.models.document import Document
from app.infrastructure.db.models.document_chunk import DocumentChunk
from app.infrastructure.db.models.user import User
from app.infrastructure.db.session import get_db
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=ApiResponse)
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    documents = db.execute(
        select(Document).order_by(Document.ingested_at.desc())
    ).scalars().all()

    items = [
        {
            "id": doc.id,
            "title": doc.title,
            "source_type": doc.source_type,
            "source_subtype": doc.source_subtype,
            "file_name": doc.file_name,
            "source_identifier": doc.source_identifier,
            "language": doc.language,
            "author": doc.author,
            "ingested_at": doc.ingested_at.isoformat(),
        }
        for doc in documents
    ]

    return success_response(
        data={
            "total": len(items),
            "items": items,
        },
        message=SUCCESS_RETRIEVED,
        code=200,
    )


@router.get("/{document_id}", response_model=ApiResponse)
def get_document_detail(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    document = db.get(Document, document_id)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=NOT_FOUND,
        )

    return success_response(
        data={
            "id": document.id,
            "external_id": document.external_id,
            "title": document.title,
            "source_type": document.source_type,
            "source_subtype": document.source_subtype,
            "file_name": document.file_name,
            "source_identifier": document.source_identifier,
            "language": document.language,
            "author": document.author,
            "metadata_json": document.metadata_json,
            "ingested_at": document.ingested_at.isoformat(),
        },
        message=SUCCESS_RETRIEVED,
        code=200,
    )


@router.get("/{document_id}/chunks", response_model=ApiResponse)
def list_document_chunks(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    document = db.get(Document, document_id)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=NOT_FOUND,
        )

    chunks = db.execute(
        select(DocumentChunk)
        .where(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index.asc())
    ).scalars().all()

    items = [
        {
            "id": chunk.id,
            "document_id": chunk.document_id,
            "chunk_index": chunk.chunk_index,
            "text": chunk.text,
            "char_count": chunk.char_count,
            "page_number": chunk.page_number,
            "section_title": chunk.section_title,
            "metadata_json": chunk.metadata_json,
        }
        for chunk in chunks
    ]

    return success_response(
        data={
            "document_id": document.id,
            "document_title": document.title,
            "total_chunks": len(items),
            "items": items,
        },
        message=SUCCESS_RETRIEVED,
        code=200,
    )