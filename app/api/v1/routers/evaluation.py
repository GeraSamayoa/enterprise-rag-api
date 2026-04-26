from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.use_cases.run_answer_evaluation import run_answer_evaluation
from app.application.use_cases.run_ragas_evaluation import run_ragas_evaluation
from app.application.use_cases.run_retrieval_evaluation import run_retrieval_evaluation
from app.core.constants import SUCCESS_CREATED, SUCCESS_RETRIEVED
from app.core.responses import success_response
from app.core.security import get_current_user
from app.infrastructure.db.models.golden_set_question import GoldenSetQuestion
from app.infrastructure.db.models.user import User
from app.infrastructure.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.evaluation import (
    GoldenSetBulkCreateRequest,
    GoldenSetQuestionCreate,
    RunAnswerEvaluationRequest,
    RunEvaluationRequest,
    RunRagasEvaluationRequest,
)

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


@router.post("/golden-set", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def create_golden_set_question(
    payload: GoldenSetQuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    question = GoldenSetQuestion(
        question=payload.question,
        expected_answer=payload.expected_answer,
        expected_document_id=payload.expected_document_id,
        expected_document_ids=payload.expected_document_ids,
        expected_source_identifier=payload.expected_source_identifier,
        difficulty=payload.difficulty,
        tags_json=payload.tags,
    )

    db.add(question)
    db.commit()
    db.refresh(question)

    return success_response(
        data={
            "id": question.id,
            "question": question.question,
            "expected_answer": question.expected_answer,
            "expected_document_id": question.expected_document_id,
            "expected_document_ids": question.expected_document_ids,
            "expected_source_identifier": question.expected_source_identifier,
            "difficulty": question.difficulty,
            "tags": question.tags_json,
        },
        message=SUCCESS_CREATED,
        code=201,
    )


@router.post("/golden-set/bulk", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def create_golden_set_questions_bulk(
    payload: GoldenSetBulkCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    created_questions = []

    for item in payload.items:
        question = GoldenSetQuestion(
            question=item.question,
            expected_answer=item.expected_answer,
            expected_document_id=item.expected_document_id,
            expected_document_ids=item.expected_document_ids,
            expected_source_identifier=item.expected_source_identifier,
            difficulty=item.difficulty,
            tags_json=item.tags,
        )

        db.add(question)
        db.flush()
        db.refresh(question)

        created_questions.append(
            {
                "id": question.id,
                "question": question.question,
                "expected_answer": question.expected_answer,
                "expected_document_id": question.expected_document_id,
                "expected_document_ids": question.expected_document_ids,
                "expected_source_identifier": question.expected_source_identifier,
                "difficulty": question.difficulty,
                "tags": question.tags_json,
            }
        )

    db.commit()

    return success_response(
        data={
            "total": len(created_questions),
            "items": created_questions,
        },
        message=SUCCESS_CREATED,
        code=201,
    )


@router.get("/golden-set", response_model=ApiResponse)
def list_golden_set_questions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    questions = db.execute(
        select(GoldenSetQuestion).order_by(GoldenSetQuestion.id.asc())
    ).scalars().all()

    items = [
        {
            "id": question.id,
            "question": question.question,
            "expected_answer": question.expected_answer,
            "expected_document_id": question.expected_document_id,
            "expected_document_ids": question.expected_document_ids,
            "expected_source_identifier": question.expected_source_identifier,
            "difficulty": question.difficulty,
            "tags": question.tags_json,
            "created_at": question.created_at.isoformat(),
        }
        for question in questions
    ]

    return success_response(
        data={
            "total": len(items),
            "items": items,
        },
        message=SUCCESS_RETRIEVED,
        code=200,
    )


@router.post("/retrieval/run", response_model=ApiResponse)
def run_retrieval_metrics(
    payload: RunEvaluationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    result = run_retrieval_evaluation(
        db=db,
        top_k=payload.top_k,
        retrieval_mode=payload.retrieval_mode,
        embedding_model_key=payload.embedding_model_key,
        use_reranking=payload.use_reranking,
        rerank_top_n=payload.rerank_top_n,
        chunk_size_filter=payload.chunk_size_filter,
        chunk_overlap_filter=payload.chunk_overlap_filter,
    )

    return success_response(
        data=result,
        message=SUCCESS_RETRIEVED,
        code=200,
    )


@router.post("/ragas/run", response_model=ApiResponse)
def run_ragas_metrics(
    payload: RunRagasEvaluationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    result = run_ragas_evaluation(
        db=db,
        top_k=payload.top_k,
        retrieval_mode=payload.retrieval_mode,
        embedding_model_key=payload.embedding_model_key,
        use_reranking=payload.use_reranking,
        rerank_top_n=payload.rerank_top_n,
        llm_provider=payload.llm_provider,
        llm_model=payload.llm_model,
    )

    return success_response(
        data=result,
        message=SUCCESS_RETRIEVED,
        code=200,
    )


@router.post("/answers/run", response_model=ApiResponse)
def run_answer_quality_metrics(
    payload: RunAnswerEvaluationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    result = run_answer_evaluation(
        db=db,
        top_k=payload.top_k,
        retrieval_mode=payload.retrieval_mode,
        embedding_model_key=payload.embedding_model_key,
        use_reranking=payload.use_reranking,
        rerank_top_n=payload.rerank_top_n,
        llm_provider=payload.llm_provider,
        llm_model=payload.llm_model,
    )

    return success_response(
        data=result,
        message=SUCCESS_RETRIEVED,
        code=200,
    )