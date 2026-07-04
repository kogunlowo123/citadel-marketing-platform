import uuid

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import Contact
from app.models.segment import Segment

logger = structlog.get_logger()


class SegmentationEngine:
    async def get_segment_contacts(
        self, segment_id: str, db: AsyncSession, page: int = 1, per_page: int = 50
    ) -> tuple[list[Contact], int]:
        """Get contacts matching segment rules with pagination."""
        seg_result = await db.execute(select(Segment).where(Segment.id == uuid.UUID(segment_id)))
        segment = seg_result.scalar_one_or_none()
        if segment is None:
            return [], 0

        rules = segment.rules if isinstance(segment.rules, list) else segment.rules.get("rules", [])
        query = self._build_query(rules)
        count_query = select(func.count()).select_from(Contact).where(*self._build_filters(rules))

        total = await db.scalar(count_query) or 0
        query = query.offset((page - 1) * per_page).limit(per_page)
        result = await db.execute(query)
        contacts = result.scalars().all()
        return contacts, total

    async def refresh_segment_count(self, segment_id: str, db: AsyncSession) -> int:
        """Recompute and cache the contact count for a segment."""
        seg_result = await db.execute(select(Segment).where(Segment.id == uuid.UUID(segment_id)))
        segment = seg_result.scalar_one_or_none()
        if segment is None:
            return 0

        rules = segment.rules if isinstance(segment.rules, list) else segment.rules.get("rules", [])
        filters = self._build_filters(rules)
        count = await db.scalar(select(func.count()).select_from(Contact).where(*filters)) or 0
        segment.contact_count = count
        await db.flush()
        return count

    def _build_query(self, rules: list[dict]) -> select:
        filters = self._build_filters(rules)
        return select(Contact).where(*filters).order_by(Contact.created_at.desc())

    def _build_filters(self, rules: list[dict]) -> list:
        """Convert rule definitions to SQLAlchemy filter expressions."""
        filters = [Contact.status == "active"]  # Always filter to active contacts

        for rule in rules:
            field_name = rule.get("field", "")
            operator = rule.get("operator", "")
            value = rule.get("value")

            column = getattr(Contact, field_name, None)
            if column is None:
                continue

            if operator == "equals":
                filters.append(column == value)
            elif operator == "not_equals":
                filters.append(column != value)
            elif operator == "contains":
                if field_name == "tags":
                    filters.append(Contact.tags.any(value))
                else:
                    filters.append(column.ilike(f"%{value}%"))
            elif operator == "not_contains":
                if field_name == "tags":
                    filters.append(~Contact.tags.any(value))
                else:
                    filters.append(~column.ilike(f"%{value}%"))
            elif operator == "greater_than":
                filters.append(column > value)
            elif operator == "less_than":
                filters.append(column < value)
            elif operator == "is_empty":
                filters.append(column.is_(None))
            elif operator == "is_not_empty":
                filters.append(column.isnot(None))

        return filters
