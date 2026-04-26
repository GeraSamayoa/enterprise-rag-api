from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import SUCCESS_RETRIEVED
from app.core.responses import success_response
from app.core.security import get_current_user
from app.infrastructure.db.models.document import Document
from app.infrastructure.db.models.experiment_run import ExperimentRun
from app.infrastructure.db.models.golden_set_question import GoldenSetQuestion
from app.infrastructure.db.models.ragas_evaluation_run import RagasEvaluationRun
from app.infrastructure.db.models.user import User
from app.infrastructure.db.session import get_db
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/report", tags=["report"])


@router.get("/technical-summary", response_model=ApiResponse)
def get_technical_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    documents = db.execute(select(Document)).scalars().all()
    golden_questions = db.execute(select(GoldenSetQuestion)).scalars().all()

    experiments = db.execute(
        select(ExperimentRun).order_by(ExperimentRun.created_at.desc())
    ).scalars().all()

    ragas_runs = db.execute(
        select(RagasEvaluationRun).order_by(RagasEvaluationRun.created_at.desc())
    ).scalars().all()

    best_experiment = None
    if experiments:
        best_experiment = max(
            experiments,
            key=lambda exp: (
                exp.mean_recall_at_k,
                exp.mrr,
                exp.mean_precision_at_k,
                -(exp.avg_latency_ms or 0),
            ),
        )

    best_ragas_run = None
    if ragas_runs:
        best_ragas_run = max(
            ragas_runs,
            key=lambda run: (
                run.faithfulness,
                run.answer_relevancy,
                run.context_precision,
            ),
        )

    source_type_counts = {}
    chunk_config_counts = {}

    for doc in documents:
        source_type_counts[doc.source_type] = source_type_counts.get(doc.source_type, 0) + 1
        key = f"chunk_size={doc.chunk_size},overlap={doc.chunk_overlap}"
        chunk_config_counts[key] = chunk_config_counts.get(key, 0) + 1

    experiment_items = [
        {
            "id": exp.id,
            "name": exp.name,
            "top_k": exp.top_k,
            "retrieval_mode": exp.retrieval_mode,
            "embedding_model_key": exp.embedding_model_key,
            "rerank_enabled": exp.rerank_enabled,
            "rerank_top_n": exp.rerank_top_n,
            "chunk_size_filter": exp.chunk_size_filter,
            "chunk_overlap_filter": exp.chunk_overlap_filter,
            "mean_precision_at_k": exp.mean_precision_at_k,
            "mean_recall_at_k": exp.mean_recall_at_k,
            "mrr": exp.mrr,
            "avg_latency_ms": exp.avg_latency_ms,
            "created_at": exp.created_at.isoformat(),
        }
        for exp in experiments
    ]

    ragas_items = [
        {
            "id": run.id,
            "top_k": run.top_k,
            "retrieval_mode": run.retrieval_mode,
            "embedding_model_key": run.embedding_model_key,
            "use_reranking": run.use_reranking,
            "rerank_top_n": run.rerank_top_n,
            "llm_provider": run.llm_provider,
            "llm_model": run.llm_model,
            "faithfulness": run.faithfulness,
            "answer_relevancy": run.answer_relevancy,
            "context_precision": run.context_precision,
            "created_at": run.created_at.isoformat(),
        }
        for run in ragas_runs
    ]

    best_experiment_summary = None
    if best_experiment:
        best_experiment_summary = {
            "id": best_experiment.id,
            "name": best_experiment.name,
            "decision": (
                "Esta configuración se selecciona como candidata porque obtuvo el mejor balance "
                "entre recall, MRR, precision y latencia promedio."
            ),
            "config": {
                "top_k": best_experiment.top_k,
                "retrieval_mode": best_experiment.retrieval_mode,
                "embedding_model_key": best_experiment.embedding_model_key,
                "rerank_enabled": best_experiment.rerank_enabled,
                "rerank_top_n": best_experiment.rerank_top_n,
                "chunk_size_filter": best_experiment.chunk_size_filter,
                "chunk_overlap_filter": best_experiment.chunk_overlap_filter,
            },
            "metrics": {
                "mean_precision_at_k": best_experiment.mean_precision_at_k,
                "mean_recall_at_k": best_experiment.mean_recall_at_k,
                "mrr": best_experiment.mrr,
                "avg_latency_ms": best_experiment.avg_latency_ms,
            },
        }

    best_ragas_summary = None
    if best_ragas_run:
        best_ragas_summary = {
            "id": best_ragas_run.id,
            "decision": (
                "Esta corrida muestra el mejor balance de calidad de respuesta, "
                "priorizando faithfulness, relevancia y precisión del contexto."
            ),
            "config": {
                "top_k": best_ragas_run.top_k,
                "retrieval_mode": best_ragas_run.retrieval_mode,
                "embedding_model_key": best_ragas_run.embedding_model_key,
                "use_reranking": best_ragas_run.use_reranking,
                "rerank_top_n": best_ragas_run.rerank_top_n,
                "llm_provider": best_ragas_run.llm_provider,
                "llm_model": best_ragas_run.llm_model,
            },
            "metrics": {
                "faithfulness": best_ragas_run.faithfulness,
                "answer_relevancy": best_ragas_run.answer_relevancy,
                "context_precision": best_ragas_run.context_precision,
            },
        }

    return success_response(
        data={
            "project": {
                "title": "Asistente de inteligencia documental para análisis empresarial",
                "objective": (
                    "Responder preguntas sobre reportes, documentos y registros empresariales "
                    "utilizando evidencia recuperada mediante un pipeline RAG."
                ),
            },
            "dataset": {
                "total_sources": len(documents),
                "source_type_counts": source_type_counts,
                "chunk_config_counts": chunk_config_counts,
            },
            "pipeline": {
                "ingestion": "Documentos y registros convertidos a texto.",
                "chunking": "Chunking configurable por chunk_size y chunk_overlap.",
                "embeddings": "Sentence Transformers con comparación primary/secondary.",
                "vector_store": "PostgreSQL + pgvector en Neon.",
                "retrieval": "Semantic, keyword e hybrid search.",
                "llm": "Groq como proveedor principal y OpenRouter como secundario.",
                "advanced_features": [
                    "Búsqueda híbrida",
                    "Reranking",
                    "Filtros por metadata/configuración de chunks",
                    "Respuesta sin evidencia suficiente",
                    "Memoria corta por sesión",
                    "Logs de trazabilidad",
                    "Evaluación automática con Ragas",
                ],
            },
            "evaluation": {
                "golden_set_questions": len(golden_questions),
                "retrieval_metrics": [
                    "Precision@k",
                    "Recall@k",
                    "MRR",
                    "Latencia promedio",
                ],
                "answer_quality_metrics": [
                    "Faithfulness",
                    "Answer relevancy",
                    "Context precision",
                ],
                "experiments": experiment_items,
                "ragas_runs": ragas_items,
                "best_retrieval_experiment": best_experiment_summary,
                "best_ragas_run": best_ragas_summary,
            },
            "limitations": [
                "La calidad depende de los documentos cargados.",
                "El chunking por caracteres puede cortar frases si el documento no tiene estructura clara.",
                "Los modelos gratuitos pueden tener límites de uso y latencia variable.",
                "La evaluación automática debe complementarse con revisión humana.",
            ],
        },
        message=SUCCESS_RETRIEVED,
        code=200,
    )