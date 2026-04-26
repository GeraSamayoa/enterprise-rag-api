import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.use_cases.hybrid_search import hybrid_search_chunks
from app.application.use_cases.keyword_search import keyword_search_chunks
from app.application.use_cases.rerank_results import apply_reranking
from app.application.use_cases.semantic_search import semantic_search_chunks
from app.evaluation.metrics.retrieval_metrics import (
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)
from app.infrastructure.db.models.golden_set_question import GoldenSetQuestion


def _get_expected_document_ids(question: GoldenSetQuestion) -> list[int]:
    if question.expected_document_ids:
        return list(question.expected_document_ids)

    if question.expected_document_id:
        return [question.expected_document_id]

    return []


def _retrieve(
    db: Session,
    question: str,
    top_k: int,
    retrieval_mode: str,
    embedding_model_key: str,
    use_reranking: bool,
    rerank_top_n: int,
    chunk_size_filter: int | None = None,
    chunk_overlap_filter: int | None = None,
) -> list[dict]:
    base_top_k = max(top_k, rerank_top_n) if use_reranking else top_k

    if retrieval_mode == "semantic":
        result = semantic_search_chunks(
            db=db,
            question=question,
            top_k=base_top_k,
            model_key=embedding_model_key,
            chunk_size_filter=chunk_size_filter,
            chunk_overlap_filter=chunk_overlap_filter,
        )
    elif retrieval_mode == "keyword":
        result = keyword_search_chunks(
            db=db,
            question=question,
            top_k=base_top_k,
            chunk_size_filter=chunk_size_filter,
            chunk_overlap_filter=chunk_overlap_filter,
        )
    else:
        result = hybrid_search_chunks(
            db=db,
            question=question,
            top_k=base_top_k,
            model_key=embedding_model_key,
            chunk_size_filter=chunk_size_filter,
            chunk_overlap_filter=chunk_overlap_filter,
        )

    items = result["items"]

    if use_reranking:
        return apply_reranking(
            question=question,
            items=items[:rerank_top_n],
            top_k=top_k,
        )

    return items[:top_k]


def run_retrieval_evaluation(
    db: Session,
    top_k: int,
    retrieval_mode: str,
    embedding_model_key: str,
    use_reranking: bool,
    rerank_top_n: int,
    chunk_size_filter: int | None = None,
    chunk_overlap_filter: int | None = None,
) -> dict:
    questions = db.execute(
        select(GoldenSetQuestion)
        .where(
            (GoldenSetQuestion.expected_document_id.is_not(None))
            | (GoldenSetQuestion.expected_document_ids.is_not(None))
        )
        .order_by(GoldenSetQuestion.id.asc())
    ).scalars().all()

    results = []

    precision_values = []
    recall_values = []
    reciprocal_rank_values = []
    latency_values = []

    for golden_question in questions:
        expected_document_ids = _get_expected_document_ids(golden_question)

        started_at = time.perf_counter()

        items = _retrieve(
            db=db,
            question=golden_question.question,
            top_k=top_k,
            retrieval_mode=retrieval_mode,
            embedding_model_key=embedding_model_key,
            use_reranking=use_reranking,
            rerank_top_n=rerank_top_n,
            chunk_size_filter=chunk_size_filter,
            chunk_overlap_filter=chunk_overlap_filter,
        )

        latency_ms = int((time.perf_counter() - started_at) * 1000)
        latency_values.append(latency_ms)

        retrieved_document_ids = [item["document_id"] for item in items]

        p_at_k = precision_at_k(
            retrieved_document_ids=retrieved_document_ids,
            expected_document_ids=expected_document_ids,
            k=top_k,
        )
        r_at_k = recall_at_k(
            retrieved_document_ids=retrieved_document_ids,
            expected_document_ids=expected_document_ids,
            k=top_k,
        )
        rr = reciprocal_rank(
            retrieved_document_ids=retrieved_document_ids,
            expected_document_ids=expected_document_ids,
        )

        precision_values.append(p_at_k)
        recall_values.append(r_at_k)
        reciprocal_rank_values.append(rr)

        results.append(
            {
                "question_id": golden_question.id,
                "question": golden_question.question,
                "expected_document_ids": expected_document_ids,
                "retrieved_document_ids": retrieved_document_ids,
                "precision_at_k": p_at_k,
                "recall_at_k": r_at_k,
                "reciprocal_rank": rr,
                "latency_ms": latency_ms,
                "retrieved_items": items,
            }
        )

    total = len(results)

    avg_latency = sum(latency_values) / total if total else 0.0
    min_latency = min(latency_values) if latency_values else 0.0
    max_latency = max(latency_values) if latency_values else 0.0

    return {
        "config": {
            "top_k": top_k,
            "retrieval_mode": retrieval_mode,
            "embedding_model_key": embedding_model_key,
            "use_reranking": use_reranking,
            "rerank_top_n": rerank_top_n,
            "chunk_size_filter": chunk_size_filter,
            "chunk_overlap_filter": chunk_overlap_filter,
        },
        "summary": {
            "total_questions": total,
            "mean_precision_at_k": sum(precision_values) / total if total else 0.0,
            "mean_recall_at_k": sum(recall_values) / total if total else 0.0,
            "mrr": sum(reciprocal_rank_values) / total if total else 0.0,
            "avg_latency_ms": avg_latency,
            "min_latency_ms": min_latency,
            "max_latency_ms": max_latency,
        },
        "items": results,
    }