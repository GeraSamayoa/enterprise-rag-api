from pydantic import BaseModel, Field


class ExperimentConfig(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    top_k: int = Field(ge=1, le=20)
    retrieval_mode: str = Field(pattern="^(semantic|keyword|hybrid)$")
    embedding_model_key: str = Field(pattern="^(primary|secondary)$")
    use_reranking: bool
    rerank_top_n: int = Field(default=6, ge=1, le=50)
    chunk_size_filter: int | None = None
    chunk_overlap_filter: int | None = None


class RunExperimentRequest(BaseModel):
    experiments: list[ExperimentConfig]