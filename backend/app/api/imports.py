import json
import uuid
from pathlib import Path

import aiofiles
import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.config import get_settings
from app.database import get_db
from app.models.import_job import ImportJob
from app.models.user import User
from app.schemas.import_job import ImportJobResponse

router = APIRouter(prefix="/imports", tags=["imports"])
logger = structlog.get_logger()
settings = get_settings()


def _job_to_response(j: ImportJob) -> ImportJobResponse:
    return ImportJobResponse(
        id=j.id, filename=j.filename, original_filename=j.original_filename,
        status=j.status, total_rows=j.total_rows, processed_rows=j.processed_rows,
        imported_count=j.imported_count, skipped_count=j.skipped_count,
        duplicate_count=j.duplicate_count, error_count=j.error_count,
        errors=json.loads(j.errors) if j.errors else None,
        created_at=j.created_at, completed_at=j.completed_at,
    )


@router.post("/", status_code=201)
async def upload_csv(
    file: UploadFile = File(...),
    tags: str = Form(""),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Upload CSV and import contacts inline."""
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")

    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    job_id = str(uuid.uuid4())
    saved_filename = f"{job_id}.csv"
    file_path = upload_dir / saved_filename

    async with aiofiles.open(file_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    tags_csv = tags.strip() if tags else ""

    job = ImportJob(
        id=job_id,
        filename=saved_filename,
        original_filename=file.filename,
        tags_to_apply=tags_csv,
    )
    db.add(job)
    await db.flush()
    await db.commit()

    # Run import inline — simpler and avoids SQLite threading issues
    from app.services.csv_importer import CSVImporter
    importer = CSVImporter()
    tags_list = [t.strip() for t in tags_csv.split(",") if t.strip()] if tags_csv else []

    try:
        result = await importer.import_file(
            file_path=str(file_path),
            job_id=job_id,
            column_mapping=None,
            tags=tags_list,
            db=db,
        )
        logger.info("csv_import_done", job_id=job_id, result=result)
    except Exception as e:
        logger.error("csv_import_error", job_id=job_id, error=str(e))

    # Reload the job to get updated stats
    await db.commit()
    result = await db.execute(select(ImportJob).where(ImportJob.id == job_id))
    updated_job = result.scalar_one_or_none()
    if updated_job:
        return _job_to_response(updated_job)
    return _job_to_response(job)


@router.get("/", response_model=list[ImportJobResponse])
async def list_imports(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ImportJob).order_by(ImportJob.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    )
    return [_job_to_response(j) for j in result.scalars().all()]


@router.get("/{job_id}", response_model=ImportJobResponse)
async def get_import(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    result = await db.execute(select(ImportJob).where(ImportJob.id == job_id))
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail="Import job not found")
    return _job_to_response(job)
