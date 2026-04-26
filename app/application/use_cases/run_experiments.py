from sqlalchemy.orm import Session

from app.application.use_cases.run_retrieval_evaluation import run_retrieval_evaluation
from app.infrastructure.db.models.experiment_run import ExperimentRun
from app.schemas.experiment import ExperimentConfig


def run_single_experiment(
    db: Session,
    config: ExperimentConfig,
) -> dict:
    evaluation_result = run_retrieval_evaluation(
        db=db,
        top_k=config.top_k,
        retrieval_mode=config.retrieval_mode,
        embedding_model_key=config.embedding_model_key,
        use_reranking=config.use_reranking,
        rerank_top_n=config.rerank_top_n,
        chunk_size_filter=config.chunk_size_filter,
        chunk_overlap_filter=config.chunk_overlap_filter,
    )

    summary = evaluation_result["summary"]

    experiment = ExperimentRun(
        name=config.name,
        top_k=config.top_k,
        retrieval_mode=config.retrieval_mode,
        embedding_model_key=config.embedding_model_key,
        rerank_enabled=config.use_reranking,
        rerank_top_n=config.rerank_top_n,
        chunk_size_filter=config.chunk_size_filter,
        chunk_overlap_filter=config.chunk_overlap_filter,
        mean_precision_at_k=summary["mean_precision_at_k"],
        mean_recall_at_k=summary["mean_recall_at_k"],
        mrr=summary["mrr"],
        avg_latency_ms=summary["avg_latency_ms"],
        min_latency_ms=summary["min_latency_ms"],
        max_latency_ms=summary["max_latency_ms"],
        metrics_json=evaluation_result,
    )

    db.add(experiment)
    db.commit()
    db.refresh(experiment)

    return {
        "experiment_id": experiment.id,
        "name": experiment.name,
        "config": evaluation_result["config"],
        "summary": summary,
    }


def run_experiment_batch(
    db: Session,
    configs: list[ExperimentConfig],
) -> dict:
    results = []

    for config in configs:
        results.append(
            run_single_experiment(
                db=db,
                config=config,
            )
        )

    return {
        "total_experiments": len(results),
        "items": results,
    }