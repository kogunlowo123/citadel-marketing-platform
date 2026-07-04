import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    preview_text: Mapped[str | None] = mapped_column(String(200))
    html_content: Mapped[str | None] = mapped_column(Text)
    text_content: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)
    segment_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("segments.id"), nullable=True)
    scheduled_at: Mapped[str | None] = mapped_column(String(30))
    sent_at: Mapped[str | None] = mapped_column(String(30))
    completed_at: Mapped[str | None] = mapped_column(String(30))
    send_rate: Mapped[int] = mapped_column(Integer, default=60)
    total_recipients: Mapped[int] = mapped_column(Integer, default=0)
    sent_count: Mapped[int] = mapped_column(Integer, default=0)
    open_count: Mapped[int] = mapped_column(Integer, default=0)
    click_count: Mapped[int] = mapped_column(Integer, default=0)
    bounce_count: Mapped[int] = mapped_column(Integer, default=0)
    unsubscribe_count: Mapped[int] = mapped_column(Integer, default=0)
    complaint_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[str] = mapped_column(String(30), default=lambda: datetime.utcnow().isoformat())
    updated_at: Mapped[str] = mapped_column(
        String(30), default=lambda: datetime.utcnow().isoformat(), onupdate=lambda: datetime.utcnow().isoformat()
    )

    segment = relationship("Segment", lazy="selectin")

    @property
    def open_rate(self) -> float:
        return (self.open_count / self.sent_count * 100) if self.sent_count > 0 else 0.0

    @property
    def click_rate(self) -> float:
        return (self.click_count / self.sent_count * 100) if self.sent_count > 0 else 0.0
