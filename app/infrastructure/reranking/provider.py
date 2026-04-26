from functools import lru_cache

from sentence_transformers import CrossEncoder

from app.core.config import settings


@lru_cache
def get_reranker_model() -> CrossEncoder:
    return CrossEncoder(settings.rerank_model)


def rerank_pairs(question: str, texts: list[str]) -> list[float]:
    model = get_reranker_model()
    pairs = [[question, text] for text in texts]
    scores = model.predict(pairs)
    return [float(score) for score in scores]