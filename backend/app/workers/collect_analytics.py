import asyncio
from datetime import datetime, timedelta, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.workers.celery_app import celery_app

logger = structlog.get_logger()
settings = get_settings()


def _get_async_session() -> async_sessionmaker:
    engine = create_async_engine(settings.DATABASE_URL, pool_size=5)
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@celery_app.task(name="app.workers.collect_analytics.check_scheduled_campaigns")
def check_scheduled_campaigns():
    """Find and trigger campaigns that are past their scheduled time."""
    async def _run():
        from app.models.campaign import Campaign
        session_factory = _get_async_session()
        async with session_factory() as db:
            now = datetime.now(timezone.utc)
            result = await db.execute(
                select(Campaign).where(
                    Campaign.status == "scheduled",
                    Campaign.scheduled_at <= now,
                )
            )
            campaigns = result.scalars().all()
            for campaign in campaigns:
                campaign.status = "sending"
                await db.commit()
                from app.workers.send_campaign import send_campaign_task
                send_campaign_task.delay(str(campaign.id))
                logger.info("scheduled_campaign_triggered", campaign_id=str(campaign.id))

    asyncio.run(_run())


@celery_app.task(name="app.workers.collect_analytics.refresh_dynamic_segments")
def refresh_dynamic_segments():
    """Refresh contact counts for all dynamic segments."""
    async def _run():
        from app.models.segment import Segment
        from app.services.segmentation import SegmentationEngine
        session_factory = _get_async_session()
        engine = SegmentationEngine()
        async with session_factory() as db:
            result = await db.execute(
                select(Segment).where(Segment.is_dynamic.is_(True))
            )
            segments = result.scalars().all()
            for segment in segments:
                await engine.refresh_segment_count(str(segment.id), db)
            await db.commit()
            logger.info("segments_refreshed", count=len(segments))

    asyncio.run(_run())


@celery_app.task(name="app.workers.collect_analytics.daily_cleanup")
def daily_cleanup():
    """Remove stale cleaned contacts and archive old events."""
    async def _run():
        from app.models.contact import Contact
        from app.models.email_event import EmailEvent
        session_factory = _get_async_session()
        async with session_factory() as db:
            cutoff_90 = datetime.now(timezone.utc) - timedelta(days=90)
            result = await db.execute(
                select(Contact).where(
                    Contact.status == "cleaned",
                    Contact.updated_at < cutoff_90,
                )
            )
            stale = result.scalars().all()
            for contact in stale:
                await db.delete(contact)
            await db.commit()
            logger.info("daily_cleanup_complete", removed=len(stale))

    asyncio.run(_run())


@celery_app.task(name="app.workers.collect_analytics.update_engagement_scores")
def update_engagement_scores():
    """Recalculate engagement scores for recently active contacts."""
    async def _run():
        from sqlalchemy import func
        from app.models.contact import Contact
        from app.models.email_event import EmailEvent
        session_factory = _get_async_session()
        async with session_factory() as db:
            seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
            result = await db.execute(
                select(EmailEvent.contact_id)
                .where(EmailEvent.created_at >= seven_days_ago)
                .distinct()
            )
            contact_ids = [row[0] for row in result.all()]

            for cid in contact_ids:
                opens = await db.scalar(
                    select(func.count()).select_from(EmailEvent).where(
                        EmailEvent.contact_id == cid,
                        EmailEvent.event_type == "opened",
                        EmailEvent.created_at >= seven_days_ago,
                    )
                ) or 0
                clicks = await db.scalar(
                    select(func.count()).select_from(EmailEvent).where(
                        EmailEvent.contact_id == cid,
                        EmailEvent.event_type == "clicked",
                        EmailEvent.created_at >= seven_days_ago,
                    )
                ) or 0
                score = min(100, opens * 5 + clicks * 10)
                contact_result = await db.execute(select(Contact).where(Contact.id == cid))
                contact = contact_result.scalar_one_or_none()
                if contact:
                    contact.engagement_score = score
            await db.commit()
            logger.info("engagement_scores_updated", contacts=len(contact_ids))

    asyncio.run(_run())
