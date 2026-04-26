import math
from typing import Any

from datasets import Dataset
from langchain_openai import ChatOpenAI
from ragas import evaluate
from ragas.metrics import (
    Faithfulness,
    LLMContextPrecisionWithoutReference,
    ResponseRelevancy,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.use_cases.hybrid_search import hybrid_search_chunks
from app.application.use_cases.keyword_search import keyword_search_chunks
from app.application.use_cases.rerank_results import apply_reranking
from app.application.use_cases.semantic_search import semantic_search_chunks
from app.core.config import settings
from app.infrastructure.db.models.golden_set_question import GoldenSetQuestion
from app.infrastructure.db.models.ragas_evaluation_run import RagasEvaluationRun
from app.infrastructure.llm.provider import generate_chat_completion
from app.rag.prompting.answer_prompt import build_grounded_messages


def _safe_float_for_db(value: Any) -> float:
    if value is None:
        return 0.0

    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return 0.0

    if math.isnan(numeric_value) or math.isinf(numeric_value):
        return 0.0

    return numeric_value


def _sanitize_json(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {key: _sanitize_json(value) for key, value in obj.items()}

    if isinstance(obj, list):
        return [_sanitize_json(value) for value in obj]

    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj

    try:
        numeric_value = float(obj)
        if math.isnan(numeric_value) or math.isinf(numeric_value):
            return None
    except (TypeError, ValueError):
        pass

    return obj


def _build_ragas_llm() -> ChatOpenAI:
    return ChatOpenAI(
        api_key=settings.ragas_llm_api_key,
        base_url=settings.ragas_llm_base_url,
        model=settings.ragas_llm_model,
        temperature=0,
    )


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


def _mean(records: list[dict], metric_name: str) -> float:
    values = []

    for row in records:
        value = row.get(metric_name)
        numeric_value = _safe_float_for_db(value)

        if numeric_value > 0:
            values.append(numeric_value)

    return sum(values) / len(values) if values else 0.0


def run_ragas_evaluation(
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

    rows = []

    for golden_question in questions:
        items = _retrieve_items(
            db=db,
            question=golden_question.question,
            top_k=top_k,
            retrieval_mode=retrieval_mode,
            embedding_model_key=embedding_model_key,
            use_reranking=use_reranking,
            rerank_top_n=rerank_top_n,
        )

        contexts = [item["text"] for item in items]

        messages = build_grounded_messages(
            question=golden_question.question,
            contexts=items,
            memory=None,
        )

        answer = generate_chat_completion(
            messages=messages,
            provider=llm_provider,
            model=llm_model,
            temperature=0.1,
        )

        rows.append(
            {
                "question": golden_question.question,
                "answer": answer,
                "contexts": contexts,
                "ground_truth": golden_question.expected_answer or "",
            }
        )

    if not rows:
        result_payload = {
            "summary": {
                "total_questions": 0,
                "faithfulness": 0.0,
                "answer_relevancy": 0.0,
                "context_precision": 0.0,
            },
            "items": [],
        }
    else:
        dataset = Dataset.from_list(rows)

        ragas_llm = _build_ragas_llm()

        result = evaluate(
            dataset=dataset,
            metrics=[
                Faithfulness(llm=ragas_llm),
                ResponseRelevancy(llm=ragas_llm),
                LLMContextPrecisionWithoutReference(llm=ragas_llm),
            ],
            raise_exceptions=False,
        )

        result_df = result.to_pandas()
        records = result_df.to_dict(orient="records")
        records = _sanitize_json(records)

        faithfulness = _mean(records, "faithfulness")
        answer_relevancy = _mean(records, "answer_relevancy")
        context_precision = _mean(records, "llm_context_precision_without_reference")

        result_payload = {
            "summary": {
                "total_questions": len(records),
                "faithfulness": faithfulness,
                "answer_relevancy": answer_relevancy,
                "context_precision": context_precision,
            },
            "items": records,
        }

    result_payload = _sanitize_json(result_payload)
    summary = result_payload["summary"]

    run = RagasEvaluationRun(
        top_k=top_k,
        retrieval_mode=retrieval_mode,
        embedding_model_key=embedding_model_key,
        use_reranking=use_reranking,
        rerank_top_n=rerank_top_n,
        llm_provider=llm_provider,
        llm_model=_selected_llm_model(llm_provider, llm_model),
        faithfulness=_safe_float_for_db(summary.get("faithfulness")),
        answer_relevancy=_safe_float_for_db(summary.get("answer_relevancy")),
        context_precision=_safe_float_for_db(summary.get("context_precision")),
        metrics_json=result_payload,
    )

    db.add(run)
    db.commit()
    db.refresh(run)

    return {
        "ragas_run_id": run.id,
        **result_payload,
    }