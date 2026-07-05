import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.segment import Segment
from app.models.user import User
from app.schemas.contact import ContactListResponse, ContactResponse
from app.schemas.segment import SegmentCreate, SegmentListResponse, SegmentResponse, SegmentUpdate
from app.services.segmentation import SegmentationEngine

router = APIRouter(prefix="/segments", tags=["segments"])
segmentation = SegmentationEngine()


@router.get("/", response_model=SegmentListResponse)
async def list_segments(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    total = await db.scalar(select(func.count()).select_from(Segment)) or 0
    result = await db.execute(
        select(Segment).order_by(Segment.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    )
    segments = result.scalars().all()
    return SegmentListResponse(
        items=[SegmentResponse.model_validate(s) for s in segments],
        total=total, page=page, per_page=per_page,
    )


@router.post("/", response_model=SegmentResponse, status_code=201)
async def create_segment(
    body: SegmentCreate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    import json as _json
    segment = Segment(
        name=body.name,
        description=body.description,
        rules=_json.dumps([r.model_dump() for r in body.rules]),
    )
    db.add(segment)
    await db.flush()
    count = await segmentation.refresh_segment_count(str(segment.id), db)
    segment.contact_count = count
    await db.flush()
    return SegmentResponse.model_validate(segment)


@router.get("/{segment_id}", response_model=SegmentResponse)
async def get_segment(
    segment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    result = await db.execute(select(Segment).where(Segment.id == segment_id))
    segment = result.scalar_one_or_none()
    if segment is None:
        raise HTTPException(status_code=404, detail="Segment not found")
    return SegmentResponse.model_validate(segment)


@router.patch("/{segment_id}", response_model=SegmentResponse)
async def update_segment(
    segment_id: uuid.UUID,
    body: SegmentUpdate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    result = await db.execute(select(Segment).where(Segment.id == segment_id))
    segment = result.scalar_one_or_none()
    if segment is None:
        raise HTTPException(status_code=404, detail="Segment not found")
    update_data = body.model_dump(exclude_unset=True)
    if "rules" in update_data and update_data["rules"] is not None:
        update_data["rules"] = [r.model_dump() if hasattr(r, "model_dump") else r for r in update_data["rules"]]
    for field, value in update_data.items():
        setattr(segment, field, value)
    await db.flush()
    return SegmentResponse.model_validate(segment)


@router.delete("/{segment_id}")
async def delete_segment(
    segment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    result = await db.execute(select(Segment).where(Segment.id == segment_id))
    segment = result.scalar_one_or_none()
    if segment is None:
        raise HTTPException(status_code=404, detail="Segment not found")
    await db.delete(segment)
    await db.flush()
    return {"success": True, "message": "Segment deleted"}


@router.get("/{segment_id}/contacts", response_model=ContactListResponse)
async def get_segment_contacts(
    segment_id: uuid.UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    result = await db.execute(select(Segment).where(Segment.id == segment_id))
    segment = result.scalar_one_or_none()
    if segment is None:
        raise HTTPException(status_code=404, detail="Segment not found")
    contacts, total = await segmentation.get_segment_contacts(str(segment_id), db, page, per_page)
    return ContactListResponse(
        items=[ContactResponse.model_validate(c) for c in contacts],
        total=total, page=page, per_page=per_page,
    )


@router.post("/{segment_id}/refresh")
async def refresh_segment(
    segment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    result = await db.execute(select(Segment).where(Segment.id == segment_id))
    segment = result.scalar_one_or_none()
    if segment is None:
        raise HTTPException(status_code=404, detail="Segment not found")
    count = await segmentation.refresh_segment_count(str(segment_id), db)
    return {"success": True, "contact_count": count}
