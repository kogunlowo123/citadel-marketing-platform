import uuid
from datetime import datetime

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Workflow(Base):
    __tablename__ = "workflows"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    trigger_type: Mapped[str] = mapped_column(String(50), nullable=False)
    trigger_config: Mapped[str | None] = mapped_column(Text)  # JSON string
    steps: Mapped[str] = mapped_column(Text, nullable=False, default="[]")  # JSON string
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    run_count: Mapped[int] = mapped_column(Integer, default=0)
    last_run_at: Mapped[str | None] = mapped_column(String(30))
    created_at: Mapped[str] = mapped_column(String(30), default=lambda: datetime.utcnow().isoformat())
    updated_at: Mapped[str] = mapped_column(
        String(30), default=lambda: datetime.utcnow().isoformat(), onupdate=lambda: datetime.utcnow().isoformat()
    )
