from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.application.use_cases.index_embeddings import index_embeddings_for_model
from app.core.constants import SUCCESS_CREATED
from app.core.responses import success_response
from app.core.security import get_current_user
from app.infrastructure.db.models.user import User
from app.infrastructure.db.session import get_db
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/indexing", tags=["indexing"])


@router.post("/embeddings", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def index_embeddings(
    model_key: str = Query(default="primary", pattern="^(primary|secondary)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    result = index_embeddings_for_model(
        db=db,
        model_key=model_key,
    )

    return success_response(
        data=result,
        message=SUCCESS_CREATED,
        code=201,
    )