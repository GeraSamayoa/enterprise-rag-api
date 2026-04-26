from pydantic import BaseModel


class DocumentListItem(BaseModel):
    id: int
    title: str
    source_type: str
    source_subtype: str | None = None
    file_name: str | None = None
    source_identifier: str | None = None
    language: str | None = None
    author: str | None = None
    ingested_at: str


class DocumentDetail(BaseModel):
    id: int
    external_id: str | None = None
    title: str
    source_type: str
    source_subtype: str | None = None
    file_name: str | None = None
    source_identifier: str | None = None
    language: str | None = None
    author: str | None = None
    metadata_json: dict | None = None
    ingested_at: str


class ChunkListItem(BaseModel):
    id: int
    document_id: int
    chunk_index: int
    text: str
    char_count: int | None = None
    page_number: int | None = None
    section_title: str | None = None
    metadata_json: dict | None = None