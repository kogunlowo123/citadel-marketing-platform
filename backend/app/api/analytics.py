from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, cast, func, select, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.campaign import Campaign
from app.models.contact import Contact
from app.models.email_event import EmailEvent
from app.models.user import User
from app.schemas.analytics import (
    CampaignComparisonItem,
    ContactGrowthData,
    EngagementData,
    EngagementResponse,
    OverviewStats,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=OverviewStats)
async def overview(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)

    total_contacts = await db.scalar(select(func.count()).select_from(Contact)) or 0
    active_contacts = await db.scalar(
        select(func.count()).select_from(Contact).where(Contact.status == "active")
    ) or 0
    total_campaigns = await db.scalar(select(func.count()).select_from(Campaign)) or 0
    campaigns_sent = await db.scalar(
        select(func.count()).select_from(Campaign).where(Campaign.status == "sent")
    ) or 0
    total_emails_sent = await db.scalar(
        select(func.coalesce(func.sum(Campaign.sent_count), 0)).select_from(Campaign)
    ) or 0
    total_opens = await db.scalar(
        select(func.coalesce(func.sum(Campaign.open_count), 0)).select_from(Campaign)
    ) or 0
    total_clicks = await db.scalar(
        select(func.coalesce(func.sum(Campaign.click_count), 0)).select_from(Campaign)
    ) or 0
    total_unsubscribes = await db.scalar(
        select(func.count()).select_from(Contact).where(Contact.status == "unsubscribed")
    ) or 0
    contacts_added_30d = await db.scalar(
        select(func.count()).select_from(Contact).where(Contact.created_at >= thirty_days_ago)
    ) or 0

    overall_open_rate = (total_opens / total_emails_sent * 100) if total_emails_sent > 0 else 0.0
    overall_click_rate = (total_clicks / total_emails_sent * 100) if total_emails_sent > 0 else 0.0

    return OverviewStats(
        total_contacts=total_contacts,
        active_contacts=active_contacts,
        total_campaigns=total_campaigns,
        campaigns_sent=campaigns_sent,
        total_emails_sent=total_emails_sent,
        overall_open_rate=round(overall_open_rate, 2),
        overall_click_rate=round(overall_click_rate, 2),
        total_unsubscribes=total_unsubscribes,
        contacts_added_last_30_days=contacts_added_30d,
    )


@router.get("/engagement", response_model=EngagementResponse)
async def engagement(
    days: int = Query(30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(
            cast(EmailEvent.created_at, Date).label("date"),
            func.count().filter(EmailEvent.event_type == "opened").label("opens"),
            func.count().filter(EmailEvent.event_type == "clicked").label("clicks"),
            func.count().filter(EmailEvent.event_type == "sent").label("sends"),
        )
        .where(EmailEvent.created_at >= since)
        .group_by(cast(EmailEvent.created_at, Date))
        .order_by(cast(EmailEvent.created_at, Date))
    )
    rows = result.all()
    data = [
        EngagementData(date=str(row.date), opens=row.opens, clicks=row.clicks, sends=row.sends)
        for row in rows
    ]
    return EngagementResponse(data=data, period=f"{days}d")


@router.get("/campaigns", response_model=list[CampaignComparisonItem])
async def campaign_comparison(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Campaign)
        .where(Campaign.sent_count > 0)
        .order_by(Campaign.sent_count.desc())
        .limit(limit)
    )
    campaigns = result.scalars().all()
    return [
        CampaignComparisonItem(
            campaign_id=c.id, name=c.name, sent=c.sent_count,
            opens=c.open_count, clicks=c.click_count, bounces=c.bounce_count,
            open_rate=c.open_rate, click_rate=c.click_rate,
        )
        for c in campaigns
    ]


@router.get("/contacts/growth", response_model=list[ContactGrowthData])
async def contact_growth(
    days: int = Query(90, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(
            cast(Contact.created_at, Date).label("date"),
            func.count().label("count"),
        )
        .where(Contact.created_at >= since)
        .group_by(cast(Contact.created_at, Date))
        .order_by(cast(Contact.created_at, Date))
    )
    return [ContactGrowthData(date=str(row.date), count=row.count) for row in result.all()]
