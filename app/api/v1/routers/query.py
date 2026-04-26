import time
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.application.use_cases.hybrid_search import hybrid_search_chunks
from app.application.use_cases.keyword_search import keyword_search_chunks
from app.application.use_cases.log_query import save_query_log
from app.application.use_cases.rerank_results import apply_reranking
from app.application.use_cases.semantic_search import semantic_search_chunks
from app.core.config import settings
from app.core.constants import NOT_FOUND, SUCCESS_RETRIEVED
from app.core.responses import success_response
from app.core.security import get_current_user
from app.infrastructure.db.models.chat_message import ChatMessage
from app.infrastructure.db.models.chat_session import ChatSession
from app.infrastructure.db.models.user import User
from app.infrastructure.db.session import get_db
from app.infrastructure.llm.provider import generate_chat_completion
from app.rag.memory.chat_memory import format_memory_for_prompt, get_recent_memory_messages
from app.rag.prompting.answer_prompt import build_grounded_messages
from app.rag.prompting.chat_prompt import build_chat_messages
from app.schemas.common import ApiResponse
from app.schemas.query import AnswerRequest

router = APIRouter(prefix="/query", tags=["query"])


def _is_chat_message(question: str) -> bool:
    normalized = question.lower().strip()

    greetings = {
        "hola",
        "buenos dias",
        "buenos días",
        "buenas tardes",
        "buenas noches",
        "hey",
        "hello",
        "hi",
    }

    assistant_questions = [
        "que haces",
        "qué haces",
        "para que sirves",
        "para qué sirves",
        "en que te especializas",
        "en qué te especializas",
        "quien eres",
        "quién eres",
        "como funcionas",
        "cómo funcionas",
    ]

    if normalized in greetings:
        return True

    return any(text in normalized for text in assistant_questions)


def _get_or_create_session(
    db: Session,
    current_user: User,
    session_id: int | None,
    question: str,
) -> ChatSession:
    if session_id is not None:
        chat_session = db.get(ChatSession, session_id)

        if not chat_session or chat_session.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NOT_FOUND,
            )

        return chat_session

    title = question[:80] if len(question) > 80 else question
    chat_session = ChatSession(
        user_id=current_user.id,
        title=title,
    )
    db.add(chat_session)
    db.commit()
    db.refresh(chat_session)

    return chat_session


def _save_message(
    db: Session,
    session_id: int,
    role: str,
    content: str,
) -> None:
    db.add(
        ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
        )
    )


def _common_filters(payload: AnswerRequest) -> dict:
    return {
        "chunk_size_filter": payload.chunk_size_filter,
        "chunk_overlap_filter": payload.chunk_overlap_filter,
        "source_type_filter": payload.source_type_filter,
        "source_subtype_filter": payload.source_subtype_filter,
        "department_filter": payload.department_filter,
        "period_filter": payload.period_filter,
    }


def _retrieve_context(payload: AnswerRequest, db: Session) -> tuple[dict, int]:
    started_at = time.perf_counter()

    base_top_k = max(payload.top_k, payload.rerank_top_n) if payload.use_reranking else payload.top_k
    filters = _common_filters(payload)

    if payload.retrieval_mode == "semantic":
        result = semantic_search_chunks(
            db=db,
            question=payload.question,
            top_k=base_top_k,
            model_key=payload.embedding_model_key,
            **filters,
        )
    elif payload.retrieval_mode == "keyword":
        result = keyword_search_chunks(
            db=db,
            question=payload.question,
            top_k=base_top_k,
            **filters,
        )
    else:
        result = hybrid_search_chunks(
            db=db,
            question=payload.question,
            top_k=base_top_k,
            model_key=payload.embedding_model_key,
            **filters,
        )

    retrieval_latency_ms = int((time.perf_counter() - started_at) * 1000)
    return result, retrieval_latency_ms


def _apply_optional_reranking(payload: AnswerRequest, result: dict) -> tuple[list[dict], int | None]:
    items = result["items"]

    if not payload.use_reranking:
        return items[:payload.top_k], None

    started_at = time.perf_counter()

    reranked_items = apply_reranking(
        question=payload.question,
        items=items[:payload.rerank_top_n],
        top_k=payload.top_k,
    )

    rerank_latency_ms = int((time.perf_counter() - started_at) * 1000)
    return reranked_items, rerank_latency_ms


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


def _build_sources(items: list[dict]) -> list[dict]:
    seen = set()
    sources = []

    for item in items:
        key = (item.get("document_id"), item.get("source_type"), item.get("source_subtype"))
        if key in seen:
            continue

        seen.add(key)
        sources.append(
            {
                "document_id": item.get("document_id"),
                "document_title": item.get("document_title"),
                "source_type": item.get("source_type"),
                "source_subtype": item.get("source_subtype"),
            }
        )

    return sources


def _build_used_fragments(items: list[dict]) -> list[dict]:
    return [
        {
            "chunk_id": item.get("chunk_id"),
            "document_id": item.get("document_id"),
            "document_title": item.get("document_title"),
            "source_type": item.get("source_type"),
            "source_subtype": item.get("source_subtype"),
            "text": item.get("text"),
            "similarity_score": item.get("similarity_score"),
            "keyword_score": item.get("keyword_score"),
            "hybrid_score": item.get("hybrid_score"),
            "rerank_score": item.get("rerank_score"),
            "metadata_json": item.get("metadata_json"),
        }
        for item in items
    ]


def _selected_llm_model(payload: AnswerRequest) -> str | None:
    return payload.llm_model or (
        settings.llm_primary_model
        if payload.llm_provider == "groq"
        else settings.llm_secondary_model
    )


@router.post("/answer", response_model=ApiResponse)
def answer_question(
    payload: AnswerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    started_at = time.perf_counter()

    chat_session = _get_or_create_session(
        db=db,
        current_user=current_user,
        session_id=payload.session_id,
        question=payload.question,
    )

    memory_messages = []
    memory_text = ""

    if payload.use_memory and payload.memory_limit > 0:
        memory_messages = get_recent_memory_messages(
            db=db,
            session_id=chat_session.id,
            limit=payload.memory_limit,
        )
        memory_text = format_memory_for_prompt(memory_messages)

    should_chat = payload.answer_mode == "chat" or (
        payload.answer_mode == "auto" and _is_chat_message(payload.question)
    )

    if should_chat:
        messages = build_chat_messages(
            question=payload.question,
            memory=memory_text,
        )

        llm_started_at = time.perf_counter()
        answer = generate_chat_completion(
            messages=messages,
            provider=payload.llm_provider,
            model=payload.llm_model,
            temperature=payload.temperature,
        )
        llm_latency_ms = int((time.perf_counter() - llm_started_at) * 1000)

        _save_message(db, chat_session.id, "user", payload.question)
        _save_message(db, chat_session.id, "assistant", answer)
        chat_session.updated_at = datetime.utcnow()

        latency_ms = int((time.perf_counter() - started_at) * 1000)

        query_log_id = save_query_log(
            db=db,
            user_id=current_user.id,
            session_id=chat_session.id,
            question=payload.question,
            retrieval_mode="chat",
            top_k=0,
            embedding_model=None,
            llm_model=_selected_llm_model(payload),
            prompt_version="chat_v1",
            used_reranker=False,
            latency_ms=latency_ms,
            retrieval_latency_ms=None,
            rerank_latency_ms=None,
            llm_latency_ms=llm_latency_ms,
            answer=answer,
            has_sufficient_evidence=None,
            retrieved_items=[],
        )

        db.commit()

        return success_response(
            data={
                "answer": answer,
                "used_fragments": [],
                "sources": [],
                "has_sufficient_evidence": None,
                "answer_mode": "chat",
                "session_id": chat_session.id,
                "query_log_id": query_log_id,
                "memory": {
                    "enabled": payload.use_memory,
                    "messages_used": len(memory_messages),
                },
                "retrieval": None,
                "filters": _common_filters(payload),
                "llm": {
                    "provider": payload.llm_provider,
                    "model": _selected_llm_model(payload),
                },
                "latency_ms": latency_ms,
            },
            message=SUCCESS_RETRIEVED,
            code=200,
        )

    retrieval_result, retrieval_latency_ms = _retrieve_context(payload, db)
    contexts, rerank_latency_ms = _apply_optional_reranking(payload, retrieval_result)

    has_evidence = _has_sufficient_evidence(contexts)

    llm_latency_ms = None

    if not has_evidence:
        answer = "No tengo evidencia suficiente en los documentos recuperados."
    else:
        messages = build_grounded_messages(
            question=payload.question,
            contexts=contexts,
            memory=memory_text,
        )

        llm_started_at = time.perf_counter()
        answer = generate_chat_completion(
            messages=messages,
            provider=payload.llm_provider,
            model=payload.llm_model,
            temperature=payload.temperature,
        )
        llm_latency_ms = int((time.perf_counter() - llm_started_at) * 1000)

    _save_message(db, chat_session.id, "user", payload.question)
    _save_message(db, chat_session.id, "assistant", answer)
    chat_session.updated_at = datetime.utcnow()

    latency_ms = int((time.perf_counter() - started_at) * 1000)

    query_log_id = save_query_log(
        db=db,
        user_id=current_user.id,
        session_id=chat_session.id,
        question=payload.question,
        retrieval_mode=payload.retrieval_mode,
        top_k=payload.top_k,
        embedding_model=payload.embedding_model_key,
        llm_model=_selected_llm_model(payload),
        prompt_version="rag_grounded_v1",
        used_reranker=payload.use_reranking,
        latency_ms=latency_ms,
        retrieval_latency_ms=retrieval_latency_ms,
        rerank_latency_ms=rerank_latency_ms,
        llm_latency_ms=llm_latency_ms,
        answer=answer,
        has_sufficient_evidence=has_evidence,
        retrieved_items=contexts,
    )

    db.commit()

    return success_response(
        data={
            "answer": answer,
            "used_fragments": _build_used_fragments(contexts),
            "sources": _build_sources(contexts),
            "has_sufficient_evidence": has_evidence,
            "answer_mode": "rag",
            "session_id": chat_session.id,
            "query_log_id": query_log_id,
            "memory": {
                "enabled": payload.use_memory,
                "messages_used": len(memory_messages),
            },
            "retrieval": {
                "mode": payload.retrieval_mode,
                "top_k": payload.top_k,
                "embedding_model_key": payload.embedding_model_key,
                "use_reranking": payload.use_reranking,
                "rerank_top_n": payload.rerank_top_n,
                "retrieval_latency_ms": retrieval_latency_ms,
                "rerank_latency_ms": rerank_latency_ms,
            },
            "filters": _common_filters(payload),
            "llm": {
                "provider": payload.llm_provider,
                "model": _selected_llm_model(payload),
                "llm_latency_ms": llm_latency_ms,
            },
            "latency_ms": latency_ms,
        },
        message=SUCCESS_RETRIEVED,
        code=200,
    )