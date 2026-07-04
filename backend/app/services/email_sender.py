import asyncio
import base64

import resend
import structlog

from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


class EmailSender:
    def __init__(self):
        resend.api_key = settings.RESEND_API_KEY

    async def send_single(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str | None,
        campaign_id: str,
        contact_id: str,
    ) -> dict:
        """Send a single email via Resend."""
        from app.services.compliance import ComplianceService
        compliance = ComplianceService()

        html = self._personalize(html_content, {})
        html = self._inject_tracking_pixel(html, campaign_id, contact_id)
        html = self._rewrite_links(html, campaign_id, contact_id)
        html = self._inject_unsubscribe_link(html, contact_id, campaign_id)
        html += compliance.get_email_footer(contact_id, campaign_id)

        unsubscribe_token = compliance.generate_unsubscribe_token(contact_id, campaign_id)
        unsubscribe_url = f"{settings.UNSUBSCRIBE_BASE_URL}/{unsubscribe_token}"

        params = {
            "from": f"{settings.RESEND_FROM_NAME} <{settings.RESEND_FROM_EMAIL}>",
            "to": [to_email],
            "subject": subject,
            "html": html,
            "tags": [
                {"name": "campaign_id", "value": campaign_id},
                {"name": "contact_id", "value": contact_id},
            ],
            "headers": {
                "List-Unsubscribe": f"<{unsubscribe_url}>",
                "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
            },
        }
        if text_content:
            params["text"] = text_content

        try:
            result = resend.Emails.send(params)
            logger.info("email_sent", to=to_email, campaign_id=campaign_id, message_id=result.get("id"))
            return {"success": True, "message_id": result.get("id")}
        except Exception as e:
            logger.error("email_send_failed", to=to_email, error=str(e))
            return {"success": False, "error": str(e)}

    async def send_batch(
        self,
        recipients: list[dict],
        subject: str,
        html_content: str,
        text_content: str | None,
        campaign_id: str,
        rate_per_minute: int,
    ) -> dict:
        """Send to multiple recipients with rate limiting."""
        delay = 60.0 / rate_per_minute if rate_per_minute > 0 else 1.0
        sent = 0
        failed = 0

        for recipient in recipients:
            result = await self.send_single(
                to_email=recipient["email"],
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                campaign_id=campaign_id,
                contact_id=recipient["contact_id"],
            )
            if result["success"]:
                sent += 1
            else:
                failed += 1
            await asyncio.sleep(delay)

        return {"sent": sent, "failed": failed, "total": len(recipients)}

    def _inject_unsubscribe_link(self, html: str, contact_id: str, campaign_id: str) -> str:
        from app.services.compliance import ComplianceService
        compliance = ComplianceService()
        token = compliance.generate_unsubscribe_token(contact_id, campaign_id)
        url = f"{settings.UNSUBSCRIBE_BASE_URL}/{token}"
        link = f'<div style="text-align:center;padding:16px;"><a href="{url}" style="color:#888;font-size:12px;">Unsubscribe</a></div>'
        if "</body>" in html:
            return html.replace("</body>", f"{link}</body>")
        return html + link

    def _inject_tracking_pixel(self, html: str, campaign_id: str, contact_id: str) -> str:
        """Add 1x1 open tracking pixel before </body>."""
        pixel_url = f"{settings.APP_URL}/api/v1/t/o/{campaign_id}/{contact_id}.gif"
        pixel = f'<img src="{pixel_url}" width="1" height="1" alt="" style="display:none" />'
        if "</body>" in html:
            return html.replace("</body>", f"{pixel}</body>")
        return html + pixel

    def _rewrite_links(self, html: str, campaign_id: str, contact_id: str) -> str:
        """Rewrite <a href> links to go through click tracker."""
        import re
        base = f"{settings.APP_URL}/api/v1/t/c/{campaign_id}/{contact_id}"

        def _replace_href(match: re.Match) -> str:
            url = match.group(1)
            # Don't track unsubscribe links or mailto:
            if "unsubscribe" in url.lower() or url.startswith("mailto:"):
                return match.group(0)
            from urllib.parse import quote
            return f'href="{base}?url={quote(url, safe="")}"'

        return re.sub(r'href="(https?://[^"]+)"', _replace_href, html)

    def _personalize(self, html: str, contact: dict) -> str:
        replacements = {
            "{{first_name}}": contact.get("first_name", ""),
            "{{last_name}}": contact.get("last_name", ""),
            "{{email}}": contact.get("email", ""),
            "{{company}}": contact.get("company", ""),
        }
        for placeholder, value in replacements.items():
            html = html.replace(placeholder, value or "")
        return html
