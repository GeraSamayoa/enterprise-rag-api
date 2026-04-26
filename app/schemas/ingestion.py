from pydantic import BaseModel, Field


class RecordIngestionRequest(BaseModel):
    external_id: str | None = None
    title: str = Field(min_length=1, max_length=500)
    source_subtype: str = Field(min_length=1, max_length=50)
    source_identifier: str | None = Field(default=None, max_length=255)
    content: str = Field(min_length=1)
    metadata: dict | None = None


class IngestionResultItem(BaseModel):
    document_id: int
    title: str
    source_type: str
    source_subtype: str | None = None
    chunks_created: int


class IngestionSummary(BaseModel):
    total_documents: int
    total_chunks: int
    items: list[IngestionResultItem]