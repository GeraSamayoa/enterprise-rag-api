from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.application.use_cases.hybrid_search import hybrid_search_chunks
from app.application.use_cases.keyword_search import keyword_search_chunks
from app.application.use_cases.rerank_results import apply_reranking
from app.application.use_cases.semantic_search import semantic_search_chunks
from app.core.constants import SUCCESS_RETRIEVED
from app.core.responses import success_response
from app.core.security import get_current_user
from app.infrastructure.db.models.user import User
from app.infrastructure.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.retrieval import RetrievalRequest

router = APIRouter(prefix="/retrieval", tags=["retrieval"])


@router.post("/search", response_model=ApiResponse)
def retrieval_search(
    payload: RetrievalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    base_top_k = max(payload.top_k, payload.rerank_top_n) if payload.use_reranking else payload.top_k

    common_filters = {
        "chunk_size_filter": payload.chunk_size_filter,
        "chunk_overlap_filter": payload.chunk_overlap_filter,
        "source_type_filter": payload.source_type_filter,
        "source_subtype_filter": payload.source_subtype_filter,
        "department_filter": payload.department_filter,
        "period_filter": payload.period_filter,
    }

    if payload.mode == "semantic":
        result = semantic_search_chunks(
            db=db,
            question=payload.question,
            top_k=base_top_k,
            model_key=payload.model_key,
            **common_filters,
        )
    elif payload.mode == "keyword":
        result = keyword_search_chunks(
            db=db,
            question=payload.question,
            top_k=base_top_k,
            **common_filters,
        )
    else:
        result = hybrid_search_chunks(
            db=db,
            question=payload.question,
            top_k=base_top_k,
            model_key=payload.model_key,
            **common_filters,
        )

    items = result["items"]

    if payload.use_reranking:
        items = apply_reranking(
            question=payload.question,
            items=items[:payload.rerank_top_n],
            top_k=payload.top_k,
        )
        result["reranking"] = {
            "enabled": True,
            "rerank_top_n": payload.rerank_top_n,
        }
    else:
        items = items[:payload.top_k]
        result["reranking"] = {
            "enabled": False,
            "rerank_top_n": 0,
        }

    result["items"] = items

    return success_response(
        data=result,
        message=SUCCESS_RETRIEVED,
        code=200,
    )