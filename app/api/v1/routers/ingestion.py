from pathlib import Path
import tempfile

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.application.use_cases.ingest_documents import ingest_document_file
from app.application.use_cases.ingest_records import ingest_record_as_document
from app.core.config import settings
from app.core.constants import BAD_REQUEST, SUCCESS_CREATED
from app.core.responses import success_response
from app.core.security import get_current_user
from app.infrastructure.db.models.user import User
from app.infrastructure.db.session import get_db
from app.infrastructure.parsing.text_extractors import SUPPORTED_EXTENSIONS
from app.schemas.common import ApiResponse
from app.schemas.ingestion import RecordIngestionRequest

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


@router.post("/document", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def ingest_document(
    file: UploadFile = File(...),
    chunk_size: int = Query(default=None, ge=100, le=2000),
    chunk_overlap: int = Query(default=None, ge=0, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=BAD_REQUEST,
        )

    final_chunk_size = chunk_size or settings.default_chunk_size
    final_chunk_overlap = chunk_overlap if chunk_overlap is not None else settings.default_chunk_overlap

    if final_chunk_overlap >= final_chunk_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CHUNK_OVERLAP_MUST_BE_SMALLER_THAN_CHUNK_SIZE",
        )

    temp_file_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        result = ingest_document_file(
            db=db,
            file_path=temp_file_path,
            original_file_name=file.filename or "uploaded_file",
            chunk_size=final_chunk_size,
            chunk_overlap=final_chunk_overlap,
        )

        return success_response(
            data=result,
            message=SUCCESS_CREATED,
            code=201,
        )
    finally:
        if temp_file_path and Path(temp_file_path).exists():
            Path(temp_file_path).unlink(missing_ok=True)


@router.post("/record", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def ingest_record(
    payload: RecordIngestionRequest,
    chunk_size: int = Query(default=None, ge=100, le=2000),
    chunk_overlap: int = Query(default=None, ge=0, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    final_chunk_size = chunk_size or settings.default_chunk_size
    final_chunk_overlap = chunk_overlap if chunk_overlap is not None else settings.default_chunk_overlap

    if final_chunk_overlap >= final_chunk_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CHUNK_OVERLAP_MUST_BE_SMALLER_THAN_CHUNK_SIZE",
        )

    result = ingest_record_as_document(
        db=db,
        payload=payload,
        chunk_size=final_chunk_size,
        chunk_overlap=final_chunk_overlap,
    )

    return success_response(
        data=result,
        message=SUCCESS_CREATED,
        code=201,
    )