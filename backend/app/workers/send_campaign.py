import asyncio
from datetime import datetime, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.models.campaign import Campaign
from app.models.contact import Contact
from app.models.email_event import EmailEvent
from app.services.compliance import ComplianceService
from app.services.email_sender import EmailSender
from app.workers.celery_app import celery_app

logger = structlog.get_logger()
settings = get_settings()


def _get_async_session() -> async_sessionmaker:
    engine = create_async_engine(settings.DATABASE_URL, pool_size=5)
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def _execute_send(campaign_id: str):
    """Core async logic for sending a campaign."""
    session_factory = _get_async_session()
    sender = EmailSender()
    compliance = ComplianceService()

    async with session_factory() as db:
        # Load campaign
        result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
        campaign = result.scalar_one_or_none()
        if campaign is None:
            logger.error("campaign_not_found", campaign_id=campaign_id)
            return

        # Check send limits
        limits = await compliance.check_send_limits(db)
        if not limits["can_send"]:
            logger.warning("daily_send_limit_reached", campaign_id=campaign_id)
            campaign.status = "paused"
            await db.commit()
            return

        campaign.status = "sending"
        campaign.sent_at = datetime.now(timezone.utc)
        await db.commit()

        # Get recipients from segment or all active contacts
        if campaign.segment_id:
            from app.services.segmentation import SegmentationEngine
            seg_engine = SegmentationEngine()
            contacts, total = await seg_engine.get_segment_contacts(
                str(campaign.segment_id), db, page=1, per_page=100000
            )
        else:
            result = await db.execute(
                select(Contact).where(Contact.status == "active")
            )
            contacts = result.scalars().all()

        # Filter suppressed contacts
        recipients = []
        for contact in contacts:
            if not await compliance.check_suppression(contact.email, db):
                recipients.append({
                    "email": contact.email,
                    "contact_id": str(contact.id),
                    "first_name": contact.first_name,
                    "last_name": contact.last_name,
                    "company": contact.company,
                })

        campaign.total_recipients = len(recipients)
        await db.commit()

        logger.info("campaign_sending", campaign_id=campaign_id, recipients=len(recipients))

        # Send in batches
        batch_result = await sender.send_batch(
            recipients=recipients,
            subject=campaign.subject,
            html_content=campaign.html_content or "",
            text_content=campaign.text_content,
            campaign_id=str(campaign.id),
            rate_per_minute=campaign.send_rate,
        )

        campaign.sent_count = batch_result["sent"]
        campaign.status = "sent"
        campaign.completed_at = datetime.now(timezone.utc)
        await db.commit()

        logger.info(
            "campaign_sent",
            campaign_id=campaign_id,
            sent=batch_result["sent"],
            failed=batch_result["failed"],
        )


@celery_app.task(name="app.workers.send_campaign.send_campaign_task", bind=True, max_retries=3)
def send_campaign_task(self, campaign_id: str):
    """Celery task to send a campaign."""
    try:
        asyncio.run(_execute_send(campaign_id))
    except Exception as exc:
        logger.error("send_campaign_failed", campaign_id=campaign_id, error=str(exc))
        self.retry(exc=exc, countdown=60)
