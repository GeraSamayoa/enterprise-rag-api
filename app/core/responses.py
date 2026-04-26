from app.schemas.common import ApiResponse


def success_response(
    data: object | None = None,
    message: str = "SUCCESS_RETRIEVED",
    code: int = 200,
) -> ApiResponse:
    return ApiResponse(
        code=str(code),
        message=message,
        data=data,
    )