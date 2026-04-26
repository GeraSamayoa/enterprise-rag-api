from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

from app.core.config import settings
from app.infrastructure.db.base import Base


# importa aquí tus modelos para que Alembic los vea
from app.infrastructure.db.models.user import User
from app.infrastructure.db.models.document import Document
from app.infrastructure.db.models.document_chunk import DocumentChunk
from app.infrastructure.db.models.chunk_embedding import ChunkEmbedding
from app.infrastructure.db.models.chat_session import ChatSession
from app.infrastructure.db.models.chat_message import ChatMessage
from app.infrastructure.db.models.query_log import QueryLog
from app.infrastructure.db.models.refresh_token import RefreshToken
from app.infrastructure.db.models.retrieved_chunk_log import RetrievedChunkLog
from app.infrastructure.db.models.golden_set_question import GoldenSetQuestion
from app.infrastructure.db.models.experiment_run import ExperimentRun
from app.infrastructure.db.models.ragas_evaluation_run import RagasEvaluationRun
from app.infrastructure.db.models.answer_evaluation_run import AnswerEvaluationRun

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# esta es la metadata que Alembic usará para autogenerate
target_metadata = Base.metadata

# sobrescribe la URL con la de Neon desde tu .env
config.set_main_option("sqlalchemy.url", settings.database_url_direct)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()