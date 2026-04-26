from fastapi import APIRouter

from app.core.constants import SUCCESS_RETRIEVED
from app.core.responses import success_response
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=ApiResponse)
def health_check() -> ApiResponse:
    return success_response(
        data={
            "status": "ok",
            "service": "enterprise-rag-api",
        },
        message=SUCCESS_RETRIEVED,
        code=200,
    )