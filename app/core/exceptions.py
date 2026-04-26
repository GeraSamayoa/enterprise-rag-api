from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.constants import (
    BAD_REQUEST,
    INTERNAL_SERVER_ERROR,
    VALIDATION_ERROR,
)
from app.schemas.common import ApiResponse


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
        message = exc.detail if isinstance(exc.detail, str) else BAD_REQUEST
        payload = ApiResponse(
            code=str(exc.status_code),
            message=message,
            data=None,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=payload.model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        payload = ApiResponse(
            code=str(status.HTTP_422_UNPROCESSABLE_ENTITY),
            message=VALIDATION_ERROR,
            data={
                "errors": exc.errors(),
            },
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=payload.model_dump(),
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(_: Request, __: Exception) -> JSONResponse:
        payload = ApiResponse(
            code=str(status.HTTP_500_INTERNAL_SERVER_ERROR),
            message=INTERNAL_SERVER_ERROR,
            data=None,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=payload.model_dump(),
        )