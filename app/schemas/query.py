from pydantic import BaseModel, Field


class AnswerRequest(BaseModel):
    question: str = Field(min_length=1)
    session_id: int | None = None

    top_k: int = Field(default=3, ge=1, le=10)
    retrieval_mode: str = Field(default="hybrid", pattern="^(semantic|keyword|hybrid)$")
    embedding_model_key: str = Field(default="primary", pattern="^(primary|secondary)$")
    use_reranking: bool = True
    rerank_top_n: int = Field(default=6, ge=1, le=20)

    chunk_size_filter: int | None = None
    chunk_overlap_filter: int | None = None

    source_type_filter: str | None = None
    source_subtype_filter: str | None = None
    department_filter: str | None = None
    period_filter: str | None = None

    llm_provider: str = Field(default="groq", pattern="^(groq|openrouter)$")
    llm_model: str | None = None
    temperature: float = Field(default=0.1, ge=0, le=1)

    answer_mode: str = Field(default="auto", pattern="^(auto|rag|chat)$")
    use_memory: bool = True
    memory_limit: int = Field(default=6, ge=0, le=20)