from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import SUCCESS_RETRIEVED
from app.core.responses import success_response
from app.core.security import get_current_user
from app.core.token_estimator import estimate_cost_usd, estimate_tokens
from app.infrastructure.db.models.query_log import QueryLog
from app.infrastructure.db.models.user import User
from app.infrastructure.db.session import get_db
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/costs", tags=["costs"])


@router.get("/summary", response_model=ApiResponse)
def get_cost_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    logs = db.execute(
        select(QueryLog)
        .where(QueryLog.user_id == current_user.id)
        .order_by(QueryLog.created_at.desc())
        .limit(200)
    ).scalars().all()

    items = []

    total_input_tokens = 0
    total_output_tokens = 0
    total_estimated_cost_usd = 0.0

    for log in logs:
        input_tokens = estimate_tokens(log.question)
        output_tokens = estimate_tokens(log.answer)

        estimated_cost_usd = estimate_cost_usd(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            input_cost_per_1m=0.0,
            output_cost_per_1m=0.0,
        )

        total_input_tokens += input_tokens
        total_output_tokens += output_tokens
        total_estimated_cost_usd += estimated_cost_usd

        items.append(
            {
                "query_log_id": log.id,
                "question": log.question,
                "llm_model": log.llm_model,
                "input_tokens_estimated": input_tokens,
                "output_tokens_estimated": output_tokens,
                "estimated_cost_usd": estimated_cost_usd,
                "latency_ms": log.latency_ms,
                "created_at": log.created_at.isoformat(),
            }
        )

    return success_response(
        data={
            "pricing_note": "Estimación aproximada. Para free tier se reporta costo monetario como 0, pero se mantienen tokens estimados.",
            "total_queries": len(items),
            "total_input_tokens_estimated": total_input_tokens,
            "total_output_tokens_estimated": total_output_tokens,
            "total_tokens_estimated": total_input_tokens + total_output_tokens,
            "total_estimated_cost_usd": round(total_estimated_cost_usd, 8),
            "items": items,
        },
        message=SUCCESS_RETRIEVED,
        code=200,
    )