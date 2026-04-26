from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.use_cases.hybrid_search import hybrid_search_chunks
from app.application.use_cases.keyword_search import keyword_search_chunks
from app.application.use_cases.rerank_results import apply_reranking
from app.application.use_cases.semantic_search import semantic_search_chunks
from app.core.config import settings
from app.infrastructure.db.models.answer_evaluation_run import AnswerEvaluationRun
from app.infrastructure.db.models.golden_set_question import GoldenSetQuestion
from app.infrastructure.llm.provider import LLMProviderError, generate_chat_completion
from app.rag.prompting.answer_prompt import build_grounded_messages


NO_EVIDENCE_TEXT = "No tengo evidencia suficiente en los documentos recuperados."
LLM_ERROR_TEXT = "No fue posible generar una respuesta con el proveedor LLM configurado."


def _selected_llm_model(llm_provider: str, llm_model: str | None) -> str | None:
    if llm_model:
        return llm_model

    return (
        settings.llm_primary_model
        if llm_provider == "groq"
        else settings.llm_secondary_model
    )


def _retrieve_items(
    db: Session,
    question: str,
    top_k: int,
    retrieval_mode: str,
    embedding_model_key: str,
    use_reranking: bool,
    rerank_top_n: int,
) -> list[dict]:
    base_top_k = max(top_k, rerank_top_n) if use_reranking else top_k

    if retrieval_mode == "semantic":
        result = semantic_search_chunks(
            db=db,
            question=question,
            top_k=base_top_k,
            model_key=embedding_model_key,
        )
    elif retrieval_mode == "keyword":
        result = keyword_search_chunks(
            db=db,
            question=question,
            top_k=base_top_k,
        )
    else:
        result = hybrid_search_chunks(
            db=db,
            question=question,
            top_k=base_top_k,
            model_key=embedding_model_key,
        )

    items = result["items"]

    if use_reranking:
        return apply_reranking(
            question=question,
            items=items[:rerank_top_n],
            top_k=top_k,
        )

    return items[:top_k]


def _has_sufficient_evidence(items: list[dict]) -> bool:
    if not items:
        return False

    best = items[0]

    if "rerank_score" in best:
        return best["rerank_score"] >= 1.5

    if "similarity_score" in best:
        return best["similarity_score"] >= 0.35

    if "hybrid_score" in best:
        return best["hybrid_score"] >= 0.25

    return True


def _get_expected_document_ids(question: GoldenSetQuestion) -> list[int]:
    if question.expected_document_ids:
        return list(question.expected_document_ids)

    if question.expected_document_id:
        return [question.expected_document_id]

    return []


def _count_used_expected_sources(
    retrieved_document_ids: list[int],
    expected_document_ids: list[int],
) -> int:
    return len(set(retrieved_document_ids).intersection(set(expected_document_ids)))


def _safe_answer(answer: str | None) -> str:
    if answer is None:
        return LLM_ERROR_TEXT

    cleaned = answer.strip()

    if not cleaned:
        return LLM_ERROR_TEXT

    return cleaned


def _generate_answer_safely(
    messages: list[dict],
    llm_provider: str,
    llm_model: str | None,
) -> tuple[str, bool, str | None]:
    try:
        answer = generate_chat_completion(
            messages=messages,
            provider=llm_provider,
            model=llm_model,
            temperature=0.1,
        )

        return _safe_answer(answer), True, None

    except LLMProviderError as error:
        return LLM_ERROR_TEXT, False, str(error)

    except Exception as error:
        return LLM_ERROR_TEXT, False, str(error)


def run_answer_evaluation(
    db: Session,
    top_k: int,
    retrieval_mode: str,
    embedding_model_key: str,
    use_reranking: bool,
    rerank_top_n: int,
    llm_provider: str,
    llm_model: str | None,
) -> dict:
    questions = db.execute(
        select(GoldenSetQuestion)
        .where(GoldenSetQuestion.expected_answer.is_not(None))
        .order_by(GoldenSetQuestion.id.asc())
    ).scalars().all()

    items = []

    answer_lengths = []
    used_fragments_counts = []
    sources_counts = []
    evidence_scores = []
    no_evidence_count = 0
    llm_error_count = 0

    for golden_question in questions:
        retrieved_items = _retrieve_items(
            db=db,
            question=golden_question.question,
            top_k=top_k,
            retrieval_mode=retrieval_mode,
            embedding_model_key=embedding_model_key,
            use_reranking=use_reranking,
            rerank_top_n=rerank_top_n,
        )

        expected_document_ids = _get_expected_document_ids(golden_question)
        retrieved_document_ids = [
            item["document_id"]
            for item in retrieved_items
            if item.get("document_id") is not None
        ]

        has_evidence = _has_sufficient_evidence(retrieved_items)
        llm_success = False
        llm_error = None

        if not has_evidence:
            answer = NO_EVIDENCE_TEXT
        else:
            messages = build_grounded_messages(
                question=golden_question.question,
                contexts=retrieved_items,
                memory=None,
            )

            answer, llm_success, llm_error = _generate_answer_safely(
                messages=messages,
                llm_provider=llm_provider,
                llm_model=llm_model,
            )

            if not llm_success:
                llm_error_count += 1

        answer_length = len(answer)
        used_fragments_count = len(retrieved_items)
        sources_count = len(set(retrieved_document_ids))

        used_expected_sources = _count_used_expected_sources(
            retrieved_document_ids=retrieved_document_ids,
            expected_document_ids=expected_document_ids,
        )

        evidence_coverage = (
            used_expected_sources / len(set(expected_document_ids))
            if expected_document_ids
            else 0.0
        )

        is_no_evidence = answer.strip() == NO_EVIDENCE_TEXT

        if is_no_evidence:
            no_evidence_count += 1

        answer_lengths.append(answer_length)
        used_fragments_counts.append(used_fragments_count)
        sources_counts.append(sources_count)
        evidence_scores.append(evidence_coverage)

        items.append(
            {
                "question_id": golden_question.id,
                "question": golden_question.question,
                "expected_document_ids": expected_document_ids,
                "retrieved_document_ids": retrieved_document_ids,
                "answer": answer,
                "answer_length": answer_length,
                "used_fragments_count": used_fragments_count,
                "sources_count": sources_count,
                "used_expected_sources": used_expected_sources,
                "evidence_coverage_score": evidence_coverage,
                "has_sufficient_evidence": has_evidence,
                "is_no_evidence_response": is_no_evidence,
                "llm_success": llm_success,
                "llm_error": llm_error,
            }
        )

    total = len(items)

    summary = {
        "total_questions": total,
        "mean_answer_length": sum(answer_lengths) / total if total else 0.0,
        "mean_used_fragments": sum(used_fragments_counts) / total if total else 0.0,
        "mean_sources": sum(sources_counts) / total if total else 0.0,
        "evidence_coverage_score": sum(evidence_scores) / total if total else 0.0,
        "no_evidence_rate": no_evidence_count / total if total else 0.0,
        "llm_error_rate": llm_error_count / total if total else 0.0,
    }

    payload = {
        "config": {
            "top_k": top_k,
            "retrieval_mode": retrieval_mode,
            "embedding_model_key": embedding_model_key,
            "use_reranking": use_reranking,
            "rerank_top_n": rerank_top_n,
            "llm_provider": llm_provider,
            "llm_model": _selected_llm_model(llm_provider, llm_model),
        },
        "summary": summary,
        "items": items,
    }

    run = AnswerEvaluationRun(
        top_k=top_k,
        retrieval_mode=retrieval_mode,
        embedding_model_key=embedding_model_key,
        use_reranking=use_reranking,
        rerank_top_n=rerank_top_n,
        llm_provider=llm_provider,
        llm_model=_selected_llm_model(llm_provider, llm_model),
        mean_answer_length=summary["mean_answer_length"],
        mean_used_fragments=summary["mean_used_fragments"],
        mean_sources=summary["mean_sources"],
        evidence_coverage_score=summary["evidence_coverage_score"],
        no_evidence_rate=summary["no_evidence_rate"],
        metrics_json=payload,
    )

    db.add(run)
    db.commit()
    db.refresh(run)

    return {
        "answer_evaluation_run_id": run.id,
        **payload,
    }