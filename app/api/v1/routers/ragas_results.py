from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import NOT_FOUND, SUCCESS_RETRIEVED
from app.core.responses import success_response
from app.core.security import get_current_user
from app.infrastructure.db.models.ragas_evaluation_run import RagasEvaluationRun
from app.infrastructure.db.models.user import User
from app.infrastructure.db.session import get_db
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/ragas-results", tags=["ragas-results"])


@router.get("", response_model=ApiResponse)
def list_ragas_runs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    runs = db.execute(
        select(RagasEvaluationRun)
        .order_by(RagasEvaluationRun.created_at.desc())
        .limit(50)
    ).scalars().all()

    items = [
        {
            "id": run.id,
            "top_k": run.top_k,
            "retrieval_mode": run.retrieval_mode,
            "embedding_model_key": run.embedding_model_key,
            "use_reranking": run.use_reranking,
            "rerank_top_n": run.rerank_top_n,
            "llm_provider": run.llm_provider,
            "llm_model": run.llm_model,
            "faithfulness": run.faithfulness,
            "answer_relevancy": run.answer_relevancy,
            "context_precision": run.context_precision,
            "created_at": run.created_at.isoformat(),
        }
        for run in runs
    ]

    return success_response(
        data={
            "total": len(items),
            "items": items,
        },
        message=SUCCESS_RETRIEVED,
        code=200,
    )


@router.get("/{run_id}", response_model=ApiResponse)
def get_ragas_run(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    run = db.get(RagasEvaluationRun, run_id)

    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=NOT_FOUND,
        )

    return success_response(
        data={
            "id": run.id,
            "top_k": run.top_k,
            "retrieval_mode": run.retrieval_mode,
            "embedding_model_key": run.embedding_model_key,
            "use_reranking": run.use_reranking,
            "rerank_top_n": run.rerank_top_n,
            "llm_provider": run.llm_provider,
            "llm_model": run.llm_model,
            "faithfulness": run.faithfulness,
            "answer_relevancy": run.answer_relevancy,
            "context_precision": run.context_precision,
            "metrics_json": run.metrics_json,
            "created_at": run.created_at.isoformat(),
        },
        message=SUCCESS_RETRIEVED,
        code=200,
    )