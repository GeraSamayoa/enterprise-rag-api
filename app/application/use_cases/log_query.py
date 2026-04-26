from sqlalchemy.orm import Session

from app.infrastructure.db.models.query_log import QueryLog
from app.infrastructure.db.models.retrieved_chunk_log import RetrievedChunkLog


def save_query_log(
    db: Session,
    user_id: int | None,
    session_id: int | None,
    question: str,
    retrieval_mode: str,
    top_k: int,
    embedding_model: str | None,
    llm_model: str | None,
    prompt_version: str | None,
    used_reranker: bool,
    latency_ms: int,
    retrieval_latency_ms: int | None,
    rerank_latency_ms: int | None,
    llm_latency_ms: int | None,
    answer: str,
    has_sufficient_evidence: bool | None,
    retrieved_items: list[dict],
) -> int:
    query_log = QueryLog(
        user_id=user_id,
        session_id=session_id,
        question=question,
        normalized_question=question.lower().strip(),
        retrieval_mode=retrieval_mode,
        top_k=top_k,
        embedding_model=embedding_model,
        llm_model=llm_model,
        prompt_version=prompt_version,
        used_reranker=used_reranker,
        latency_ms=latency_ms,
        retrieval_latency_ms=retrieval_latency_ms,
        rerank_latency_ms=rerank_latency_ms,
        llm_latency_ms=llm_latency_ms,
        answer=answer,
        has_sufficient_evidence=bool(has_sufficient_evidence),
    )

    db.add(query_log)
    db.flush()

    for index, item in enumerate(retrieved_items, start=1):
        retrieval_score = (
            item.get("hybrid_score")
            or item.get("similarity_score")
            or item.get("keyword_score")
            or item.get("score")
        )

        db.add(
            RetrievedChunkLog(
                query_log_id=query_log.id,
                chunk_id=item["chunk_id"],
                retrieval_rank=index,
                retrieval_score=float(retrieval_score) if retrieval_score is not None else None,
                rerank_score=item.get("rerank_score"),
                was_used_in_prompt=True,
            )
        )

    db.flush()
    return query_log.id