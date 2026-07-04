import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    first_name: Mapped[str | None] = mapped_column(String(100))
    last_name: Mapped[str | None] = mapped_column(String(100))
    phone: Mapped[str | None] = mapped_column(String(50))
    company: Mapped[str | None] = mapped_column(String(200))
    tags: Mapped[str] = mapped_column(Text, default="")  # comma-separated for SQLite compat
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="manual")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", index=True)
    consent: Mapped[str] = mapped_column(String(20), nullable=False, default="none")  # none, implicit, confirmed, revoked
    consent_source: Mapped[str | None] = mapped_column(String(100))  # how consent was obtained
    consent_at: Mapped[str | None] = mapped_column(String(30))  # when consent was granted
    engagement_score: Mapped[int] = mapped_column(Integer, default=0)
    metadata_json: Mapped[str | None] = mapped_column("metadata", Text)
    test_mode: Mapped[int] = mapped_column(Integer, default=0)  # 1 = test sends only
    bounce_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[str] = mapped_column(String(30), default=lambda: datetime.utcnow().isoformat())
    updated_at: Mapped[str] = mapped_column(
        String(30), default=lambda: datetime.utcnow().isoformat(), onupdate=lambda: datetime.utcnow().isoformat()
    )
    last_engaged_at: Mapped[str | None] = mapped_column(String(30))
    unsubscribed_at: Mapped[str | None] = mapped_column(String(30))

    @property
    def tags_list(self) -> list[str]:
        return [t.strip() for t in (self.tags or "").split(",") if t.strip()]

    @tags_list.setter
    def tags_list(self, value: list[str]):
        self.tags = ",".join(value) if value else ""

    @property
    def full_name(self) -> str:
        parts = [p for p in [self.first_name, self.last_name] if p]
        return " ".join(parts) if parts else self.email
