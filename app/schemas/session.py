from pydantic import BaseModel, Field


class CreateChatSessionRequest(BaseModel):
    title: str | None = Field(default=None, max_length=255)


class ChatSessionResponse(BaseModel):
    id: int
    title: str | None
    created_at: str
    updated_at: str


class ChatMessageResponse(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    created_at: str