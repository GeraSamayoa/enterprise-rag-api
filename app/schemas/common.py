from typing import Any

from pydantic import BaseModel


class ApiResponse(BaseModel):
    code: str
    message: str
    data: Any | None = None