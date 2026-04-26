from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.use_cases.run_experiments import run_experiment_batch
from app.core.constants import NOT_FOUND, SUCCESS_CREATED, SUCCESS_RETRIEVED
from app.core.responses import success_response
from app.core.security import get_current_user
from app.infrastructure.db.models.experiment_run import ExperimentRun
from app.infrastructure.db.models.user import User
from app.infrastructure.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.experiment import RunExperimentRequest

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.post("/run", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def run_experiments(
    payload: RunExperimentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    result = run_experiment_batch(
        db=db,
        configs=payload.experiments,
    )

    return success_response(
        data=result,
        message=SUCCESS_CREATED,
        code=201,
    )


@router.get("", response_model=ApiResponse)
def list_experiments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    experiments = db.execute(
        select(ExperimentRun)
        .order_by(ExperimentRun.created_at.desc())
        .limit(50)
    ).scalars().all()

    items = [
        {
            "id": exp.id,
            "name": exp.name,
            "top_k": exp.top_k,
            "retrieval_mode": exp.retrieval_mode,
            "embedding_model_key": exp.embedding_model_key,
            "rerank_enabled": exp.rerank_enabled,
            "rerank_top_n": exp.rerank_top_n,
            "chunk_size_filter": exp.chunk_size_filter,
            "chunk_overlap_filter": exp.chunk_overlap_filter,
            "mean_precision_at_k": exp.mean_precision_at_k,
            "mean_recall_at_k": exp.mean_recall_at_k,
            "mrr": exp.mrr,
            "avg_latency_ms": exp.avg_latency_ms,
            "min_latency_ms": exp.min_latency_ms,
            "max_latency_ms": exp.max_latency_ms,
            "created_at": exp.created_at.isoformat(),
        }
        for exp in experiments
    ]

    return success_response(
        data={
            "total": len(items),
            "items": items,
        },
        message=SUCCESS_RETRIEVED,
        code=200,
    )


@router.get("/{experiment_id}", response_model=ApiResponse)
def get_experiment_detail(
    experiment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    experiment = db.get(ExperimentRun, experiment_id)

    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=NOT_FOUND,
        )

    return success_response(
        data={
            "id": experiment.id,
            "name": experiment.name,
            "top_k": experiment.top_k,
            "retrieval_mode": experiment.retrieval_mode,
            "embedding_model_key": experiment.embedding_model_key,
            "rerank_enabled": experiment.rerank_enabled,
            "rerank_top_n": experiment.rerank_top_n,
            "chunk_size_filter": experiment.chunk_size_filter,
            "chunk_overlap_filter": experiment.chunk_overlap_filter,
            "mean_precision_at_k": experiment.mean_precision_at_k,
            "mean_recall_at_k": experiment.mean_recall_at_k,
            "mrr": experiment.mrr,
            "avg_latency_ms": experiment.avg_latency_ms,
            "min_latency_ms": experiment.min_latency_ms,
            "max_latency_ms": experiment.max_latency_ms,
            "metrics_json": experiment.metrics_json,
            "created_at": experiment.created_at.isoformat(),
        },
        message=SUCCESS_RETRIEVED,
        code=200,
    )