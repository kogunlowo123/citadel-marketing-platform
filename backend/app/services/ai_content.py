import anthropic
import structlog

from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


class AIContentGenerator:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def generate_campaign(
        self, topic: str, tone: str = "professional", audience: str = "cloud professionals", length: str = "medium"
    ) -> dict:
        """Generate a complete email campaign using Claude."""
        length_guide = {"short": "150-200 words", "medium": "300-400 words", "long": "500-700 words"}
        word_count = length_guide.get(length, "300-400 words")

        prompt = f"""Generate a marketing email for Citadel Cloud Management about: {topic}

Target audience: {audience}
Tone: {tone}
Length: {word_count}

Citadel Cloud Management is a cloud education platform offering free courses, skill tracks, and professional certifications in AWS, Azure, GCP, DevOps, and cybersecurity.

Brand colors: background #0a0a0a, accent #00d4ff, text #e0e0e0
Fonts: Syne for headings, DM Sans for body text

Return a JSON object with these exact keys:
- "subject": compelling email subject line (under 60 chars)
- "preview_text": preview text for email clients (under 90 chars)
- "html_content": full HTML email with inline CSS, responsive design, dark theme, and a CTA button linking to https://www.citadelcloudmanagement.com
- "text_content": plain text version of the email

Return ONLY the JSON object, no markdown fences or extra text."""

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )
            import json
            content = message.content[0].text.strip()
            # Strip markdown fences if present
            if content.startswith("```"):
                content = content.split("\n", 1)[1]
                content = content.rsplit("```", 1)[0]
            result = json.loads(content)
            logger.info("ai_campaign_generated", topic=topic)
            return result
        except Exception as e:
            logger.error("ai_generation_failed", error=str(e))
            return {
                "subject": f"[Draft] {topic}",
                "preview_text": f"Learn about {topic} with Citadel Cloud Management",
                "html_content": f"<html><body style='background:#0a0a0a;color:#e0e0e0;font-family:DM Sans,sans-serif;padding:40px'><h1 style='color:#00d4ff;font-family:Syne,sans-serif'>{topic}</h1><p>Content generation failed. Please write your email content manually.</p></body></html>",
                "text_content": f"{topic}\n\nContent generation failed. Please write manually.",
            }

    async def generate_subject_lines(self, topic: str, count: int = 5) -> list[str]:
        """Generate multiple subject line options."""
        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": f"Generate {count} email subject lines for a marketing email about: {topic}\nTarget: cloud professionals.\nReturn ONLY a JSON array of strings, nothing else.",
                }],
            )
            import json
            content = message.content[0].text.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(content)
        except Exception as e:
            logger.error("subject_generation_failed", error=str(e))
            return [f"[Draft] {topic}"]

    async def rewrite_content(self, content: str, instruction: str) -> str:
        """Rewrite existing content with a specific instruction."""
        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                messages=[{
                    "role": "user",
                    "content": f"Rewrite this email content. Instruction: {instruction}\n\nOriginal:\n{content}\n\nReturn ONLY the rewritten content.",
                }],
            )
            return message.content[0].text.strip()
        except Exception as e:
            logger.error("rewrite_failed", error=str(e))
            return content
