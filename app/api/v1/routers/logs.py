from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import NOT_FOUND, SUCCESS_RETRIEVED
from app.core.responses import success_response
from app.core.security import get_current_user
from app.infrastructure.db.models.document_chunk import DocumentChunk
from app.infrastructure.db.models.query_log import QueryLog
from app.infrastructure.db.models.retrieved_chunk_log import RetrievedChunkLog
from app.infrastructure.db.models.user import User
from app.infrastructure.db.session import get_db
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("/queries", response_model=ApiResponse)
def list_query_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    logs = db.execute(
        select(QueryLog)
        .where(QueryLog.user_id == current_user.id)
        .order_by(QueryLog.created_at.desc())
        .limit(50)
    ).scalars().all()

    items = [
        {
            "id": log.id,
            "session_id": log.session_id,
            "question": log.question,
            "retrieval_mode": log.retrieval_mode,
            "top_k": log.top_k,
            "embedding_model": log.embedding_model,
            "llm_model": log.llm_model,
            "used_reranker": log.used_reranker,
            "latency_ms": log.latency_ms,
            "retrieval_latency_ms": log.retrieval_latency_ms,
            "rerank_latency_ms": log.rerank_latency_ms,
            "llm_latency_ms": log.llm_latency_ms,
            "has_sufficient_evidence": log.has_sufficient_evidence,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]

    return success_response(
        data={
            "total": len(items),
            "items": items,
        },
        message=SUCCESS_RETRIEVED,
        code=200,
    )


@router.get("/queries/{query_log_id}", response_model=ApiResponse)
def get_query_log_detail(
    query_log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    log = db.get(QueryLog, query_log_id)

    if not log or log.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=NOT_FOUND,
        )

    retrieved_logs = db.execute(
        select(RetrievedChunkLog, DocumentChunk)
        .join(DocumentChunk, DocumentChunk.id == RetrievedChunkLog.chunk_id)
        .where(RetrievedChunkLog.query_log_id == query_log_id)
        .order_by(RetrievedChunkLog.retrieval_rank.asc())
    ).all()

    chunks = [
        {
            "chunk_id": chunk.id,
            "document_id": chunk.document_id,
            "chunk_index": chunk.chunk_index,
            "text": chunk.text,
            "retrieval_rank": retrieved.retrieval_rank,
            "retrieval_score": retrieved.retrieval_score,
            "rerank_score": retrieved.rerank_score,
            "was_used_in_prompt": retrieved.was_used_in_prompt,
            "metadata_json": chunk.metadata_json,
        }
        for retrieved, chunk in retrieved_logs
    ]

    return success_response(
        data={
            "id": log.id,
            "user_id": log.user_id,
            "session_id": log.session_id,
            "question": log.question,
            "normalized_question": log.normalized_question,
            "retrieval_mode": log.retrieval_mode,
            "top_k": log.top_k,
            "embedding_model": log.embedding_model,
            "llm_model": log.llm_model,
            "prompt_version": log.prompt_version,
            "used_reranker": log.used_reranker,
            "latency_ms": log.latency_ms,
            "retrieval_latency_ms": log.retrieval_latency_ms,
            "rerank_latency_ms": log.rerank_latency_ms,
            "llm_latency_ms": log.llm_latency_ms,
            "answer": log.answer,
            "has_sufficient_evidence": log.has_sufficient_evidence,
            "created_at": log.created_at.isoformat(),
            "retrieved_chunks": chunks,
        },
        message=SUCCESS_RETRIEVED,
        code=200,
    )