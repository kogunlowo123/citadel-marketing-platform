from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.contact import Contact
from app.models.email_event import EmailEvent
from app.services.compliance import ComplianceService

router = APIRouter(prefix="/unsubscribe", tags=["unsubscribe"])
compliance = ComplianceService()

UNSUBSCRIBE_PAGE = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Unsubscribe — Citadel Cloud Management</title>
<style>
body{{background:#0a0a0a;color:#e0e0e0;font-family:'DM Sans',sans-serif;display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0}}
.card{{background:#111;border:1px solid #1e1e1e;border-radius:12px;padding:40px;max-width:480px;text-align:center}}
h1{{font-family:'Syne',sans-serif;color:#00d4ff;font-size:1.5rem;margin-bottom:16px}}
p{{color:#888;line-height:1.6;margin-bottom:24px}}
form button{{background:#00d4ff;color:#0a0a0a;border:none;padding:12px 32px;border-radius:8px;font-weight:600;cursor:pointer;font-size:1rem}}
form button:hover{{opacity:0.9}}
.done{{color:#00c853}}
</style></head>
<body><div class="card">
<h1>{title}</h1>
<p>{message}</p>
{action}
</div></body></html>"""


@router.get("/{token}", response_class=HTMLResponse)
async def unsubscribe_page(token: str):
    try:
        contact_id, campaign_id = compliance.verify_unsubscribe_token(token)
    except Exception:
        return HTMLResponse(
            UNSUBSCRIBE_PAGE.format(
                title="Invalid Link",
                message="This unsubscribe link is invalid or has expired.",
                action="",
            ),
            status_code=400,
        )

    return HTMLResponse(
        UNSUBSCRIBE_PAGE.format(
            title="Unsubscribe",
            message="Click the button below to unsubscribe from our marketing emails. You will no longer receive promotional messages from Citadel Cloud Management.",
            action=f'<form method="POST"><button type="submit">Confirm Unsubscribe</button></form>',
        )
    )


@router.post("/{token}", response_class=HTMLResponse)
async def confirm_unsubscribe(token: str, db: AsyncSession = Depends(get_db)):
    try:
        contact_id, campaign_id = compliance.verify_unsubscribe_token(token)
    except Exception:
        return HTMLResponse(
            UNSUBSCRIBE_PAGE.format(
                title="Invalid Link",
                message="This unsubscribe link is invalid or has expired.",
                action="",
            ),
            status_code=400,
        )

    import uuid
    result = await db.execute(select(Contact).where(Contact.id == uuid.UUID(contact_id)))
    contact = result.scalar_one_or_none()
    if contact is None:
        return HTMLResponse(
            UNSUBSCRIBE_PAGE.format(title="Not Found", message="Contact not found.", action=""),
            status_code=404,
        )

    contact.status = "unsubscribed"
    contact.unsubscribed_at = datetime.now(timezone.utc)

    event = EmailEvent(
        campaign_id=uuid.UUID(campaign_id),
        contact_id=uuid.UUID(contact_id),
        event_type="unsubscribed",
    )
    db.add(event)
    await db.flush()

    return HTMLResponse(
        UNSUBSCRIBE_PAGE.format(
            title="Unsubscribed",
            message='<span class="done">You have been successfully unsubscribed.</span> You will no longer receive marketing emails from us.',
            action="",
        )
    )
