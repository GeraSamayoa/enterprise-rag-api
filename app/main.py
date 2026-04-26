from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI

from app.api.v1.routers.auth import router as auth_router
from app.api.v1.routers.documents import router as documents_router
from app.api.v1.routers.health import router as health_router
from app.api.v1.routers.indexing import router as indexing_router
from app.api.v1.routers.ingestion import router as ingestion_router
from app.api.v1.routers.retrieval import router as retrieval_router
from app.api.v1.routers.query import router as query_router
from app.api.v1.routers.sessions import router as sessions_router
from app.api.v1.routers.logs import router as logs_router
from app.api.v1.routers.evaluation import router as evaluation_router
from app.api.v1.routers.experiments import router as experiments_router
from app.api.v1.routers.report import router as report_router
from app.api.v1.routers.ragas_results import router as ragas_results_router
from app.api.v1.routers.costs import router as costs_router

from app.core.config import settings
from app.core.exceptions import register_exception_handlers


app = FastAPI(
    title=settings.app_name,
    debug=settings.app_debug,
    version="0.1.0",
)

register_exception_handlers(app)

app.include_router(health_router, prefix=settings.api_v1_prefix)
app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(ingestion_router, prefix=settings.api_v1_prefix)
app.include_router(documents_router, prefix=settings.api_v1_prefix)
app.include_router(indexing_router, prefix=settings.api_v1_prefix)
app.include_router(retrieval_router, prefix=settings.api_v1_prefix)
app.include_router(query_router, prefix=settings.api_v1_prefix)
app.include_router(sessions_router, prefix=settings.api_v1_prefix)
app.include_router(logs_router, prefix=settings.api_v1_prefix)
app.include_router(evaluation_router, prefix=settings.api_v1_prefix)
app.include_router(experiments_router, prefix=settings.api_v1_prefix)
app.include_router(report_router, prefix=settings.api_v1_prefix)
app.include_router(ragas_results_router, prefix=settings.api_v1_prefix)
app.include_router(costs_router, prefix=settings.api_v1_prefix)


@app.get("/")
def root() -> dict:
    return {
        "message": "Enterprise RAG API is running",
        "docs": "/docs",
    }