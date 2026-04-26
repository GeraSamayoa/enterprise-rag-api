from pydantic import BaseModel, Field


class GoldenSetQuestionCreate(BaseModel):
    question: str = Field(min_length=1)
    expected_answer: str | None = None
    expected_document_id: int | None = None
    expected_document_ids: list[int] | None = None
    expected_source_identifier: str | None = None
    difficulty: str | None = None
    tags: dict | None = None


class GoldenSetBulkCreateRequest(BaseModel):
    items: list[GoldenSetQuestionCreate]


class RunEvaluationRequest(BaseModel):
    top_k: int = Field(default=3, ge=1, le=20)
    retrieval_mode: str = Field(default="hybrid", pattern="^(semantic|keyword|hybrid)$")
    embedding_model_key: str = Field(default="primary", pattern="^(primary|secondary)$")
    use_reranking: bool = True
    rerank_top_n: int = Field(default=6, ge=1, le=50)
    chunk_size_filter: int | None = None
    chunk_overlap_filter: int | None = None


class RunRagasEvaluationRequest(BaseModel):
    top_k: int = Field(default=3, ge=1, le=10)
    retrieval_mode: str = Field(default="hybrid", pattern="^(semantic|keyword|hybrid)$")
    embedding_model_key: str = Field(default="primary", pattern="^(primary|secondary)$")
    use_reranking: bool = True
    rerank_top_n: int = Field(default=6, ge=1, le=20)
    llm_provider: str = Field(default="groq", pattern="^(groq|openrouter)$")
    llm_model: str | None = None


class RunAnswerEvaluationRequest(BaseModel):
    top_k: int = Field(default=3, ge=1, le=10)
    retrieval_mode: str = Field(default="hybrid", pattern="^(semantic|keyword|hybrid)$")
    embedding_model_key: str = Field(default="primary", pattern="^(primary|secondary)$")
    use_reranking: bool = True
    rerank_top_n: int = Field(default=6, ge=1, le=20)
    llm_provider: str = Field(default="groq", pattern="^(groq|openrouter)$")
    llm_model: str | None = None