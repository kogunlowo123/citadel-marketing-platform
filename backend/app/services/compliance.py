import base64
import hashlib
import hmac
from datetime import datetime, timezone

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.contact import Contact
from app.models.email_event import EmailEvent

logger = structlog.get_logger()
settings = get_settings()


class ComplianceService:
    def generate_unsubscribe_token(self, contact_id: str, campaign_id: str) -> str:
        """Generate a signed unsubscribe token."""
        payload = f"{contact_id}:{campaign_id}"
        signature = hmac.new(
            settings.APP_SECRET_KEY.encode(), payload.encode(), hashlib.sha256
        ).hexdigest()[:16]
        token_data = f"{payload}:{signature}"
        return base64.urlsafe_b64encode(token_data.encode()).decode()

    def verify_unsubscribe_token(self, token: str) -> tuple[str, str]:
        """Decode and verify an unsubscribe token. Returns (contact_id, campaign_id)."""
        try:
            decoded = base64.urlsafe_b64decode(token.encode()).decode()
            parts = decoded.split(":")
            if len(parts) != 3:
                raise ValueError("Invalid token format")
            contact_id, campaign_id, signature = parts

            expected_sig = hmac.new(
                settings.APP_SECRET_KEY.encode(),
                f"{contact_id}:{campaign_id}".encode(),
                hashlib.sha256,
            ).hexdigest()[:16]

            if not hmac.compare_digest(signature, expected_sig):
                raise ValueError("Invalid signature")

            return contact_id, campaign_id
        except Exception as e:
            logger.warning("invalid_unsubscribe_token", error=str(e))
            raise

    async def check_send_limits(self, db: AsyncSession) -> dict:
        """Check daily send count against configured maximum."""
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        sent_today = await db.scalar(
            select(func.count())
            .select_from(EmailEvent)
            .where(EmailEvent.event_type == "sent", EmailEvent.created_at >= today_start)
        ) or 0

        remaining = max(0, settings.MAX_DAILY_SENDS - sent_today)
        return {
            "can_send": remaining > 0,
            "sent_today": sent_today,
            "remaining": remaining,
            "daily_limit": settings.MAX_DAILY_SENDS,
        }

    def get_email_footer(self, contact_id: str, campaign_id: str) -> str:
        """Return a CAN-SPAM compliant email footer."""
        token = self.generate_unsubscribe_token(contact_id, campaign_id)
        url = f"{settings.UNSUBSCRIBE_BASE_URL}/{token}"
        return f"""
<div style="border-top:1px solid #333;margin-top:32px;padding-top:16px;text-align:center;font-size:12px;color:#666;">
  <p>{settings.COMPANY_NAME} | {settings.COMPANY_ADDRESS}</p>
  <p>You received this email because you subscribed to updates from {settings.COMPANY_NAME}.</p>
  <p><a href="{url}" style="color:#888;">Unsubscribe</a> from future emails.</p>
</div>"""

    async def process_bounce(self, contact_id: str, bounce_type: str, db: AsyncSession):
        """Handle a bounce event — hard bounces immediately suppress."""
        import uuid
        result = await db.execute(select(Contact).where(Contact.id == uuid.UUID(contact_id)))
        contact = result.scalar_one_or_none()
        if contact is None:
            return
        contact.bounce_count += 1
        if bounce_type == "hard" or contact.bounce_count >= 3:
            contact.status = "bounced"
            logger.info("contact_bounced", contact_id=contact_id, bounce_type=bounce_type)
        await db.flush()

    async def check_suppression(self, email: str, db: AsyncSession) -> bool:
        """Check if an email address is suppressed (bounced, unsubscribed, complained)."""
        result = await db.execute(
            select(Contact).where(Contact.email == email.lower())
        )
        contact = result.scalar_one_or_none()
        if contact is None:
            return False
        return contact.status in ("bounced", "unsubscribed", "complained", "cleaned")
