from pydantic import BaseModel, Field


class RetrievalRequest(BaseModel):
    question: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    model_key: str = Field(default="primary", pattern="^(primary|secondary)$")
    mode: str = Field(default="semantic", pattern="^(semantic|keyword|hybrid)$")
    use_reranking: bool = True
    rerank_top_n: int = Field(default=10, ge=1, le=50)

    chunk_size_filter: int | None = None
    chunk_overlap_filter: int | None = None

    source_type_filter: str | None = None
    source_subtype_filter: str | None = None
    department_filter: str | None = None
    period_filter: str | None = None