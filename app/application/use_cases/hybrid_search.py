from app.application.use_cases.keyword_search import keyword_search_chunks
from app.application.use_cases.semantic_search import semantic_search_chunks


def hybrid_search_chunks(
    db,
    question: str,
    top_k: int = 5,
    model_key: str = "primary",
    semantic_weight: float = 0.7,
    keyword_weight: float = 0.3,
    chunk_size_filter: int | None = None,
    chunk_overlap_filter: int | None = None,
    source_type_filter: str | None = None,
    source_subtype_filter: str | None = None,
    department_filter: str | None = None,
    period_filter: str | None = None,
) -> dict:
    semantic_results = semantic_search_chunks(
        db=db,
        question=question,
        top_k=top_k * 3,
        model_key=model_key,
        chunk_size_filter=chunk_size_filter,
        chunk_overlap_filter=chunk_overlap_filter,
        source_type_filter=source_type_filter,
        source_subtype_filter=source_subtype_filter,
        department_filter=department_filter,
        period_filter=period_filter,
    )

    keyword_results = keyword_search_chunks(
        db=db,
        question=question,
        top_k=top_k * 3,
        chunk_size_filter=chunk_size_filter,
        chunk_overlap_filter=chunk_overlap_filter,
        source_type_filter=source_type_filter,
        source_subtype_filter=source_subtype_filter,
        department_filter=department_filter,
        period_filter=period_filter,
    )

    merged: dict[int, dict] = {}

    for item in semantic_results["items"]:
        merged[item["chunk_id"]] = {
            **item,
            "semantic_score": item["similarity_score"],
            "keyword_score": 0.0,
        }

    for item in keyword_results["items"]:
        if item["chunk_id"] in merged:
            merged[item["chunk_id"]]["keyword_score"] = item["score"]
        else:
            merged[item["chunk_id"]] = {
                "chunk_id": item["chunk_id"],
                "document_id": item["document_id"],
                "document_title": item["document_title"],
                "source_type": item["source_type"],
                "source_subtype": item["source_subtype"],
                "chunk_index": item["chunk_index"],
                "text": item["text"],
                "metadata_json": item["metadata_json"],
                "semantic_score": 0.0,
                "keyword_score": item["score"],
            }

    items = []
    for item in merged.values():
        hybrid_score = (
            item["semantic_score"] * semantic_weight
            + item["keyword_score"] * keyword_weight
        )
        item["hybrid_score"] = hybrid_score
        items.append(item)

    items.sort(key=lambda x: x["hybrid_score"], reverse=True)
    items = items[:top_k]

    return {
        "question": question,
        "top_k": top_k,
        "mode": "hybrid",
        "model_key": model_key,
        "filters": {
            "chunk_size": chunk_size_filter,
            "chunk_overlap": chunk_overlap_filter,
            "source_type": source_type_filter,
            "source_subtype": source_subtype_filter,
            "department": department_filter,
            "period": period_filter,
        },
        "items": items,
    }