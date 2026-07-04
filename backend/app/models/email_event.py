import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class EmailEvent(Base):
    __tablename__ = "email_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    campaign_id: Mapped[str] = mapped_column(String(36), ForeignKey("campaigns.id"), nullable=False, index=True)
    contact_id: Mapped[str] = mapped_column(String(36), ForeignKey("contacts.id"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(20), nullable=False)
    link_url: Mapped[str | None] = mapped_column(String(2048))
    bounce_type: Mapped[str | None] = mapped_column(String(20))
    user_agent: Mapped[str | None] = mapped_column(String(500))
    ip_address: Mapped[str | None] = mapped_column(String(45))
    metadata_json: Mapped[str | None] = mapped_column("metadata", Text)
    created_at: Mapped[str] = mapped_column(String(30), default=lambda: datetime.utcnow().isoformat())

    campaign = relationship("Campaign")
    contact = relationship("Contact", lazy="selectin")
