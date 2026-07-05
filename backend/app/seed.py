"""Auto-seed script that runs on every startup to ensure baseline data exists.

This solves the Render free-tier problem: ephemeral filesystem means SQLite DB
resets on every cold start. This script idempotently creates the admin user,
segments, workflows, and campaigns if they don't exist.
"""
import asyncio
import json

import bcrypt
import structlog

logger = structlog.get_logger()


async def seed_database():
    """Idempotently seed the database with baseline data."""
    from sqlalchemy import select, func
    from app.database import async_session_factory
    from app.models.user import User
    from app.models.segment import Segment
    from app.models.workflow import Workflow
    from app.models.campaign import Campaign

    async with async_session_factory() as db:
        # 1. Admin user
        user_count = await db.scalar(select(func.count()).select_from(User))
        if not user_count:
            hashed = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode("utf-8")
            db.add(User(email="admin@citadel.com", hashed_password=hashed, name="Sam O."))
            await db.commit()
            logger.info("seed_admin_created")

        # 2. Segments
        seg_count = await db.scalar(select(func.count()).select_from(Segment))
        if not seg_count:
            segments = [
                {"name": "All Active", "description": "Active contacts", "rules": json.dumps([{"field": "status", "operator": "equals", "value": "active"}])},
                {"name": "High Engagement", "description": "Score > 50", "rules": json.dumps([{"field": "engagement_score", "operator": "greater_than", "value": "50"}])},
                {"name": "Cloud Beginners", "description": "Tagged cloud", "rules": json.dumps([{"field": "tags", "operator": "contains", "value": "cloud"}])},
                {"name": "Newsletter Subscribers", "description": "Tagged newsletter", "rules": json.dumps([{"field": "tags", "operator": "contains", "value": "newsletter"}])},
                {"name": "CSV Imports", "description": "Imported via CSV", "rules": json.dumps([{"field": "source", "operator": "equals", "value": "csv_import"}])},
            ]
            for s in segments:
                db.add(Segment(**s))
            await db.commit()
            logger.info("seed_segments_created", count=len(segments))

        # 3. Workflows
        wf_count = await db.scalar(select(func.count()).select_from(Workflow))
        if not wf_count:
            workflows = [
                {"name": "Welcome Series", "description": "3-email welcome sequence", "trigger_type": "csv_import", "is_active": True,
                 "steps": json.dumps([{"step_type": "send_email", "config": {"subject": "Welcome to Citadel Cloud Management"}}, {"step_type": "wait", "config": {"duration_hours": 72}}, {"step_type": "send_email", "config": {"subject": "Your Cloud Learning Path Awaits"}}])},
                {"name": "Post-Campaign Follow-up", "description": "Engagement-based follow-up", "trigger_type": "campaign_sent", "is_active": True,
                 "steps": json.dumps([{"step_type": "wait", "config": {"duration_hours": 72}}, {"step_type": "send_email", "config": {"subject": "Thanks for reading"}}])},
                {"name": "Monthly Cleanup", "description": "Remove inactive contacts", "trigger_type": "date_trigger", "is_active": True,
                 "steps": json.dumps([{"step_type": "send_email", "config": {"subject": "We miss you at Citadel Cloud"}}, {"step_type": "wait", "config": {"duration_hours": 336}}])},
                {"name": "Re-engagement", "description": "Win back low-engagement contacts", "trigger_type": "segment_entered", "is_active": True,
                 "steps": json.dumps([{"step_type": "send_email", "config": {"subject": "Something special for you"}}, {"step_type": "wait", "config": {"duration_hours": 168}}])},
            ]
            for w in workflows:
                db.add(Workflow(**w))
            await db.commit()
            logger.info("seed_workflows_created", count=len(workflows))

        # 4. Campaigns
        camp_count = await db.scalar(select(func.count()).select_from(Campaign))
        if not camp_count:
            campaigns = [
                {"name": "Citadel Cloud Launch", "subject": "Your Free Cloud Career Starts Here", "status": "draft",
                 "html_content": '<html><body style="background:#0a0a0a;color:#e0e0e0;font-family:DM Sans,sans-serif;padding:40px;max-width:600px;margin:0 auto"><h1 style="color:#00d4ff;font-family:Syne,sans-serif">Your Cloud Career Starts Here</h1><p>Welcome to Citadel Cloud Management. We offer 17 free courses across 6 skill tracks covering AWS, Azure, GCP, Kubernetes, and more.</p><a href="https://www.citadelcloudmanagement.com/collections/free-courses" style="display:inline-block;background:#00d4ff;color:#0a0a0a;padding:14px 28px;border-radius:8px;font-weight:700;text-decoration:none">Explore Free Courses</a></body></html>'},
                {"name": "Cloud Career Newsletter #1", "subject": "Cloud Jobs: What Hiring Managers Want in 2026", "status": "draft",
                 "html_content": '<html><body style="background:#0a0a0a;color:#e0e0e0;font-family:DM Sans,sans-serif;padding:40px;max-width:600px;margin:0 auto"><h1 style="color:#00d4ff;font-family:Syne,sans-serif">Cloud Career Intelligence</h1><p>Multi-cloud skills command 20-30% premiums. AI/ML + cloud roles are fastest growing. Security certs remain in top demand.</p><a href="https://www.citadelcloudmanagement.com/collections/all" style="display:inline-block;background:#00d4ff;color:#0a0a0a;padding:14px 28px;border-radius:8px;font-weight:700;text-decoration:none">Browse Resources</a></body></html>'},
            ]
            for c in campaigns:
                db.add(Campaign(**c))
            await db.commit()
            logger.info("seed_campaigns_created", count=len(campaigns))

        logger.info("seed_complete")
