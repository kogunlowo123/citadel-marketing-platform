import uuid
from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.campaign import Campaign
from app.models.contact import Contact
from app.models.email_event import EmailEvent

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = structlog.get_logger()


@router.post("/resend")
async def resend_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle Resend delivery webhook events."""
    body = await request.json()
    event_type = body.get("type", "")
    data = body.get("data", {})

    logger.info("resend_webhook_received", event_type=event_type)

    # Map Resend event types to our event types
    event_map = {
        "email.sent": "sent",
        "email.delivered": "delivered",
        "email.opened": "opened",
        "email.clicked": "clicked",
        "email.bounced": "bounced",
        "email.complained": "complained",
    }

    our_event_type = event_map.get(event_type)
    if our_event_type is None:
        return {"status": "ignored", "reason": f"Unknown event type: {event_type}"}

    # Extract IDs from tags or headers
    tags = data.get("tags", {})
    campaign_id = tags.get("campaign_id")
    contact_id = tags.get("contact_id")

    if not campaign_id or not contact_id:
        logger.warning("webhook_missing_ids", event_type=event_type)
        return {"status": "ignored", "reason": "Missing campaign_id or contact_id"}

    try:
        campaign_uuid = uuid.UUID(campaign_id)
        contact_uuid = uuid.UUID(contact_id)
    except ValueError:
        return {"status": "ignored", "reason": "Invalid UUID format"}

    # Create event record
    event = EmailEvent(
        campaign_id=campaign_uuid,
        contact_id=contact_uuid,
        event_type=our_event_type,
        link_url=data.get("click", {}).get("link") if our_event_type == "clicked" else None,
        bounce_type=data.get("bounce", {}).get("type") if our_event_type == "bounced" else None,
        user_agent=data.get("user_agent"),
        ip_address=data.get("ip"),
        metadata_=data,
    )
    db.add(event)

    # Update campaign counters
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_uuid))
    campaign = result.scalar_one_or_none()
    if campaign:
        counter_map = {
            "opened": "open_count",
            "clicked": "click_count",
            "bounced": "bounce_count",
            "complained": "complaint_count",
        }
        counter_field = counter_map.get(our_event_type)
        if counter_field:
            setattr(campaign, counter_field, getattr(campaign, counter_field) + 1)

    # Handle bounces — update contact status
    if our_event_type == "bounced":
        contact_result = await db.execute(select(Contact).where(Contact.id == contact_uuid))
        contact = contact_result.scalar_one_or_none()
        if contact:
            contact.bounce_count += 1
            bounce_type = data.get("bounce", {}).get("type", "soft")
            if bounce_type == "hard" or contact.bounce_count >= 3:
                contact.status = "bounced"

    # Handle complaints
    if our_event_type == "complained":
        contact_result = await db.execute(select(Contact).where(Contact.id == contact_uuid))
        contact = contact_result.scalar_one_or_none()
        if contact:
            contact.status = "complained"

    # Update engagement timestamp
    if our_event_type in ("opened", "clicked"):
        contact_result = await db.execute(select(Contact).where(Contact.id == contact_uuid))
        contact = contact_result.scalar_one_or_none()
        if contact:
            contact.last_engaged_at = datetime.now(timezone.utc)

    await db.flush()
    logger.info("webhook_processed", event_type=our_event_type, campaign_id=campaign_id)
    return {"status": "processed", "event_type": our_event_type}
