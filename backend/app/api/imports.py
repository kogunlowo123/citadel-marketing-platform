import uuid
from pathlib import Path

import aiofiles
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.import_job import ImportJob
from app.models.user import User
from app.schemas.import_job import ImportJobResponse

router = APIRouter(prefix="/imports", tags=["imports"])

UPLOAD_DIR = Path("/app/uploads")


@router.post("/", response_model=ImportJobResponse, status_code=201)
async def upload_csv(
    file: UploadFile = File(...),
    tags: str = Form(""),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    job_id = uuid.uuid4()
    saved_filename = f"{job_id}.csv"
    file_path = UPLOAD_DIR / saved_filename

    async with aiofiles.open(file_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    tags_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

    job = ImportJob(
        id=job_id,
        filename=saved_filename,
        original_filename=file.filename,
        tags_to_apply=tags_list,
    )
    db.add(job)
    await db.flush()

    from app.config import get_settings
    _settings = get_settings()

    if _settings.REDIS_URL:
        # Celery worker available — dispatch async
        from app.workers.process_import import process_import_task
        process_import_task.delay(str(job_id))
    else:
        # No Redis/Celery — run import synchronously in-process
        import asyncio
        import threading
        from app.services.csv_importer import CSVImporter
        from app.database import get_db as _get_db

        async def _run_import():
            from app.database import engine
            from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
            session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            async with session_factory() as import_db:
                importer = CSVImporter()
                await importer.import_file(
                    file_path=str(file_path),
                    job_id=str(job_id),
                    column_mapping=None,
                    tags=tags_list,
                    db=import_db,
                )

        def _bg():
            asyncio.run(_run_import())

        threading.Thread(target=_bg, daemon=True).start()

    return ImportJobResponse.model_validate(job)


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
    jobs = result.scalars().all()
    return [ImportJobResponse.model_validate(j) for j in jobs]


@router.get("/{job_id}", response_model=ImportJobResponse)
async def get_import(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    result = await db.execute(select(ImportJob).where(ImportJob.id == job_id))
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail="Import job not found")
    return ImportJobResponse.model_validate(job)
