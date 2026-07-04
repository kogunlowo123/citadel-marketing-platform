import asyncio
from pathlib import Path

import structlog
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.services.csv_importer import CSVImporter
from app.workers.celery_app import celery_app

logger = structlog.get_logger()
settings = get_settings()

UPLOAD_DIR = Path("/app/uploads")


def _get_async_session() -> async_sessionmaker:
    engine = create_async_engine(settings.DATABASE_URL, pool_size=5)
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def _execute_import(job_id: str):
    session_factory = _get_async_session()
    importer = CSVImporter()

    async with session_factory() as db:
        from sqlalchemy import select
        from app.models.import_job import ImportJob

        result = await db.execute(select(ImportJob).where(ImportJob.id == job_id))
        job = result.scalar_one_or_none()
        if job is None:
            logger.error("import_job_not_found", job_id=job_id)
            return

        file_path = str(UPLOAD_DIR / job.filename)
        await importer.import_file(
            file_path=file_path,
            job_id=job_id,
            column_mapping=job.column_mapping,
            tags=job.tags_to_apply,
            db=db,
        )


@celery_app.task(name="app.workers.process_import.process_import_task", bind=True, max_retries=2)
def process_import_task(self, job_id: str):
    """Celery task to process a CSV import."""
    try:
        asyncio.run(_execute_import(job_id))
    except Exception as exc:
        logger.error("import_failed", job_id=job_id, error=str(exc))
        self.retry(exc=exc, countdown=30)
