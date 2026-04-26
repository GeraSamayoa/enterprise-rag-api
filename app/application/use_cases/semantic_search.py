from sqlalchemy import text
from sqlalchemy.orm import Session

from app.infrastructure.embeddings.provider import embed_texts


def semantic_search_chunks(
    db: Session,
    question: str,
    top_k: int = 5,
    model_key: str = "primary",
    chunk_size_filter: int | None = None,
    chunk_overlap_filter: int | None = None,
    source_type_filter: str | None = None,
    source_subtype_filter: str | None = None,
    department_filter: str | None = None,
    period_filter: str | None = None,
) -> dict:
    query_vector = embed_texts([question], model_key=model_key)[0]

    sql = text("""
        SELECT
            dc.id AS chunk_id,
            dc.document_id AS document_id,
            d.title AS document_title,
            d.source_type AS source_type,
            d.source_subtype AS source_subtype,
            dc.chunk_index AS chunk_index,
            dc.text AS text,
            dc.metadata_json AS metadata_json,
            1 - (ce.embedding <=> CAST(:query_vector AS vector)) AS similarity_score
        FROM chunk_embeddings ce
        JOIN document_chunks dc ON dc.id = ce.chunk_id
        JOIN documents d ON d.id = dc.document_id
        WHERE ce.embedding_model = :model_key
          AND (CAST(:chunk_size_filter AS INTEGER) IS NULL OR dc.chunk_size = CAST(:chunk_size_filter AS INTEGER))
          AND (CAST(:chunk_overlap_filter AS INTEGER) IS NULL OR dc.chunk_overlap = CAST(:chunk_overlap_filter AS INTEGER))
          AND (CAST(:source_type_filter AS TEXT) IS NULL OR d.source_type = CAST(:source_type_filter AS TEXT))
          AND (CAST(:source_subtype_filter AS TEXT) IS NULL OR d.source_subtype = CAST(:source_subtype_filter AS TEXT))
          AND (CAST(:department_filter AS TEXT) IS NULL OR dc.metadata_json ->> 'department' = CAST(:department_filter AS TEXT))
          AND (CAST(:period_filter AS TEXT) IS NULL OR dc.metadata_json ->> 'period' = CAST(:period_filter AS TEXT))
        ORDER BY ce.embedding <=> CAST(:query_vector AS vector)
        LIMIT :top_k
    """)

    result = db.execute(
        sql,
        {
            "query_vector": str(query_vector),
            "model_key": model_key,
            "top_k": top_k,
            "chunk_size_filter": chunk_size_filter,
            "chunk_overlap_filter": chunk_overlap_filter,
            "source_type_filter": source_type_filter,
            "source_subtype_filter": source_subtype_filter,
            "department_filter": department_filter,
            "period_filter": period_filter,
        },
    ).mappings().all()

    items = [
        {
            "chunk_id": row["chunk_id"],
            "document_id": row["document_id"],
            "document_title": row["document_title"],
            "source_type": row["source_type"],
            "source_subtype": row["source_subtype"],
            "chunk_index": row["chunk_index"],
            "text": row["text"],
            "similarity_score": float(row["similarity_score"]),
            "metadata_json": row["metadata_json"],
        }
        for row in result
    ]

    return {
        "question": question,
        "top_k": top_k,
        "mode": "semantic",
        "model_key": model_key,
        "filters": {
            "chunk_size": chunk_size_filter,
            "chunk_overlap": chunk_overlap_filter,
            "source_type": source_type_filter,
            "source_subtype": source_subtype_filter,
            "department": department_filter,
            "period": period_filter,
        },
        "items": items,
    }