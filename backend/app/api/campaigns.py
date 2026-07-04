import threading

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.campaign import Campaign
from app.models.user import User
from app.schemas.campaign import (
    CampaignCreate, CampaignGenerateRequest, CampaignListResponse,
    CampaignResponse, CampaignScheduleRequest, CampaignUpdate,
)

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


def _to_response(c: Campaign) -> CampaignResponse:
    data = CampaignResponse.model_validate(c)
    data.open_rate = c.open_rate
    data.click_rate = c.click_rate
    return data


@router.get("/", response_model=CampaignListResponse)
async def list_campaigns(
    page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100),
    status: str | None = None,
    db: AsyncSession = Depends(get_db), _user: User = Depends(get_current_user),
):
    query = select(Campaign)
    count_query = select(func.count()).select_from(Campaign)
    if status:
        query = query.where(Campaign.status == status)
        count_query = count_query.where(Campaign.status == status)
    query = query.order_by(Campaign.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    total = await db.scalar(count_query) or 0
    result = await db.execute(query)
    return CampaignListResponse(items=[_to_response(c) for c in result.scalars().all()], total=total, page=page, per_page=per_page)


@router.post("/", response_model=CampaignResponse, status_code=201)
async def create_campaign(body: CampaignCreate, db: AsyncSession = Depends(get_db), _user: User = Depends(get_current_user)):
    campaign = Campaign(**body.model_dump())
    db.add(campaign)
    await db.flush()
    return _to_response(campaign)


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(campaign_id: str, db: AsyncSession = Depends(get_db), _user: User = Depends(get_current_user)):
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return _to_response(campaign)


@router.patch("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(campaign_id: str, body: CampaignUpdate, db: AsyncSession = Depends(get_db), _user: User = Depends(get_current_user)):
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if campaign.status != "draft":
        raise HTTPException(status_code=400, detail="Can only edit draft campaigns")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(campaign, field, value)
    await db.flush()
    return _to_response(campaign)


@router.post("/{campaign_id}/schedule", response_model=CampaignResponse)
async def schedule_campaign(campaign_id: str, body: CampaignScheduleRequest, db: AsyncSession = Depends(get_db), _user: User = Depends(get_current_user)):
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if campaign.status not in ("draft", "paused"):
        raise HTTPException(status_code=400, detail="Cannot schedule in current state")
    campaign.scheduled_at = body.scheduled_at
    campaign.status = "scheduled"
    await db.flush()
    return _to_response(campaign)


@router.post("/{campaign_id}/send", response_model=CampaignResponse)
async def send_campaign(campaign_id: str, db: AsyncSession = Depends(get_db), _user: User = Depends(get_current_user)):
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if campaign.status not in ("draft", "scheduled"):
        raise HTTPException(status_code=400, detail="Cannot send in current state")
    campaign.status = "sending"
    await db.flush()

    # Background send (no Celery in local dev)
    def _bg_send():
        import asyncio
        from app.workers.send_campaign import _execute_send
        asyncio.run(_execute_send(campaign_id))

    threading.Thread(target=_bg_send, daemon=True).start()
    return _to_response(campaign)


@router.post("/{campaign_id}/pause")
async def pause_campaign(campaign_id: str, db: AsyncSession = Depends(get_db), _user: User = Depends(get_current_user)):
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    campaign.status = "paused"
    await db.flush()
    return {"success": True, "message": "Campaign paused"}


@router.post("/{campaign_id}/cancel")
async def cancel_campaign(campaign_id: str, db: AsyncSession = Depends(get_db), _user: User = Depends(get_current_user)):
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    campaign.status = "cancelled"
    await db.flush()
    return {"success": True, "message": "Campaign cancelled"}


@router.post("/generate")
async def generate_campaign(body: CampaignGenerateRequest, _user: User = Depends(get_current_user)):
    from app.services.ai_content import AIContentGenerator
    generator = AIContentGenerator()
    content = await generator.generate_campaign(topic=body.topic, tone=body.tone, audience=body.audience, length=body.length)
    return {"success": True, "data": content}
