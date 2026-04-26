from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "enterprise-rag-api"
    app_env: str = "local"
    app_debug: bool = True
    api_v1_prefix: str = "/api/v1"

    database_url_pooled: str
    database_url_direct: str

    db_echo: bool = False
    db_pool_pre_ping: bool = True
    db_pool_recycle: int = 300

    jwt_secret_key: str
    jwt_refresh_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    embedding_model: str
    embedding_model_alt: str
    rerank_model: str

    default_top_k: int = 5
    default_rerank_top_n: int = 20
    default_chunk_size: int = 600
    default_chunk_overlap: int = 100

    retrieval_mode: str = "hybrid"
    enable_reranking: bool = True
    enable_memory: bool = True
    enable_insufficient_evidence: bool = True

    default_llm_model: str = "primary"
    default_prompt_version: str = "v1_strict_grounded"

    llm_primary_provider: str | None = None
    llm_primary_base_url: str | None = None
    llm_primary_api_key: str | None = None
    llm_primary_model: str | None = None

    llm_secondary_provider: str | None = None
    llm_secondary_base_url: str | None = None
    llm_secondary_api_key: str | None = None
    llm_secondary_model: str | None = None

    ragas_llm_provider: str | None = None
    ragas_llm_base_url: str | None = None
    ragas_llm_api_key: str | None = None
    ragas_llm_model: str | None = None

    openrouter_referer: str | None = None
    openrouter_app_name: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()