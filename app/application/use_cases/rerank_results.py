from app.infrastructure.reranking.provider import rerank_pairs


def apply_reranking(
    question: str,
    items: list[dict],
    top_k: int,
) -> list[dict]:
    if not items:
        return []

    texts = [item["text"] for item in items]
    rerank_scores = rerank_pairs(question=question, texts=texts)

    enriched_items = []
    for item, rerank_score in zip(items, rerank_scores, strict=True):
        enriched = {
            **item,
            "rerank_score": rerank_score,
        }
        enriched_items.append(enriched)

    enriched_items.sort(key=lambda x: x["rerank_score"], reverse=True)
    return enriched_items[:top_k]