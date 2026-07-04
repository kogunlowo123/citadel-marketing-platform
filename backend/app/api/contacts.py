import csv
import io
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from app.api.deps import get_current_user
from app.database import get_db
from app.models.contact import Contact
from app.models.user import User
from app.schemas.contact import ContactListResponse, ContactResponse, ContactUpdate

router = APIRouter(prefix="/contacts", tags=["contacts"])


def _contact_to_response(c: Contact) -> ContactResponse:
    return ContactResponse(
        id=c.id, email=c.email, first_name=c.first_name, last_name=c.last_name,
        phone=c.phone, company=c.company, tags=c.tags_list,
        status=c.status, source=c.source, engagement_score=c.engagement_score,
        bounce_count=c.bounce_count, created_at=c.created_at,
        updated_at=c.updated_at, last_engaged_at=c.last_engaged_at,
        unsubscribed_at=c.unsubscribed_at,
    )


@router.get("/", response_model=ContactListResponse)
async def list_contacts(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    status: str | None = None,
    source: str | None = None,
    tag: str | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    query = select(Contact)
    count_query = select(func.count()).select_from(Contact)

    if status:
        query = query.where(Contact.status == status)
        count_query = count_query.where(Contact.status == status)
    if source:
        query = query.where(Contact.source == source)
        count_query = count_query.where(Contact.source == source)
    if tag:
        query = query.where(Contact.tags.contains(tag))
        count_query = count_query.where(Contact.tags.contains(tag))
    if search:
        pattern = f"%{search}%"
        search_filter = or_(
            Contact.email.ilike(pattern),
            Contact.first_name.ilike(pattern),
            Contact.last_name.ilike(pattern),
            Contact.company.ilike(pattern),
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    query = query.order_by(Contact.created_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)

    total = await db.scalar(count_query) or 0
    result = await db.execute(query)
    contacts = result.scalars().all()

    return ContactListResponse(
        items=[_contact_to_response(c) for c in contacts],
        total=total, page=page, per_page=per_page,
    )


@router.get("/export")
async def export_contacts(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    result = await db.execute(select(Contact).where(Contact.status == "active"))
    contacts = result.scalars().all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["email", "first_name", "last_name", "phone", "company", "tags", "status", "score"])
    for c in contacts:
        writer.writerow([c.email, c.first_name, c.last_name, c.phone, c.company, c.tags, c.status, c.engagement_score])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]), media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=contacts_export.csv"},
    )


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(contact_id: str, db: AsyncSession = Depends(get_db), _user: User = Depends(get_current_user)):
    result = await db.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return _contact_to_response(contact)


@router.patch("/{contact_id}", response_model=ContactResponse)
async def update_contact(contact_id: str, body: ContactUpdate, db: AsyncSession = Depends(get_db), _user: User = Depends(get_current_user)):
    result = await db.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    update_data = body.model_dump(exclude_unset=True)
    if "tags" in update_data and update_data["tags"] is not None:
        contact.tags_list = update_data.pop("tags")
    for field, value in update_data.items():
        setattr(contact, field, value)
    await db.flush()
    return _contact_to_response(contact)


@router.delete("/{contact_id}")
async def delete_contact(contact_id: str, db: AsyncSession = Depends(get_db), _user: User = Depends(get_current_user)):
    result = await db.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    contact.status = "cleaned"
    await db.flush()
    return {"success": True, "message": "Contact removed"}


@router.post("/{contact_id}/unsubscribe")
async def unsubscribe_contact(contact_id: str, db: AsyncSession = Depends(get_db), _user: User = Depends(get_current_user)):
    result = await db.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    contact.status = "unsubscribed"
    contact.unsubscribed_at = datetime.now(timezone.utc).isoformat()
    await db.flush()
    return {"success": True, "message": "Contact unsubscribed"}
