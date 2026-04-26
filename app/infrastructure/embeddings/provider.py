from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.core.config import settings


MODEL_REGISTRY = {
    "primary": settings.embedding_model,
    "secondary": settings.embedding_model_alt,
}


@lru_cache
def get_embedding_model(model_key: str = "primary") -> SentenceTransformer:
    model_name = MODEL_REGISTRY.get(model_key)
    if not model_name:
        raise ValueError(f"Unknown embedding model key: {model_key}")

    return SentenceTransformer(model_name)


def embed_texts(texts: list[str], model_key: str = "primary") -> list[list[float]]:
    model = get_embedding_model(model_key)
    vectors = model.encode(texts, normalize_embeddings=True)
    return [vector.tolist() for vector in vectors]