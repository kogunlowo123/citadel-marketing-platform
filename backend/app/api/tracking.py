"""Open-pixel and click-redirect tracking endpoints.

These are unauthenticated — they're hit from email clients.
"""
import base64
from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import RedirectResponse, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.contact import Contact
from app.models.email_event import EmailEvent

router = APIRouter(prefix="/t", tags=["tracking"])
logger = structlog.get_logger()

# 1x1 transparent GIF
PIXEL_GIF = base64.b64decode("R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7")


@router.get("/o/{campaign_id}/{contact_id}.gif")
async def track_open(
    campaign_id: str,
    contact_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Record an email open event and return a 1x1 tracking pixel."""
    event = EmailEvent(
        campaign_id=campaign_id,
        contact_id=contact_id,
        event_type="opened",
    )
    db.add(event)

    # Update contact engagement
    result = await db.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()
    if contact:
        contact.last_engaged_at = datetime.now(timezone.utc).isoformat()

    # Update campaign open count
    from app.models.campaign import Campaign
    camp_result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = camp_result.scalar_one_or_none()
    if campaign:
        campaign.open_count += 1

    await db.flush()
    logger.info("open_tracked", campaign_id=campaign_id, contact_id=contact_id)

    return Response(
        content=PIXEL_GIF,
        media_type="image/gif",
        headers={"Cache-Control": "no-store, no-cache, must-revalidate", "Pragma": "no-cache"},
    )


@router.get("/c/{campaign_id}/{contact_id}")
async def track_click(
    campaign_id: str,
    contact_id: str,
    url: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Record a click event and redirect to the target URL."""
    event = EmailEvent(
        campaign_id=campaign_id,
        contact_id=contact_id,
        event_type="clicked",
        link_url=url,
    )
    db.add(event)

    # Update contact engagement
    result = await db.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()
    if contact:
        contact.last_engaged_at = datetime.now(timezone.utc).isoformat()

    # Update campaign click count
    from app.models.campaign import Campaign
    camp_result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = camp_result.scalar_one_or_none()
    if campaign:
        campaign.click_count += 1

    await db.flush()
    logger.info("click_tracked", campaign_id=campaign_id, contact_id=contact_id, url=url)

    return RedirectResponse(url=url, status_code=302)
