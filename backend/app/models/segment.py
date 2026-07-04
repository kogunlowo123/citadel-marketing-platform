import uuid
from datetime import datetime

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Segment(Base):
    __tablename__ = "segments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    rules: Mapped[str] = mapped_column(Text, nullable=False, default="[]")  # JSON string
    contact_count: Mapped[int] = mapped_column(Integer, default=0)
    is_dynamic: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[str] = mapped_column(String(30), default=lambda: datetime.utcnow().isoformat())
    updated_at: Mapped[str] = mapped_column(
        String(30), default=lambda: datetime.utcnow().isoformat(), onupdate=lambda: datetime.utcnow().isoformat()
    )

    @property
    def rules_list(self) -> list[dict]:
        import json
        try:
            return json.loads(self.rules) if self.rules else []
        except (json.JSONDecodeError, TypeError):
            return []

    @rules_list.setter
    def rules_list(self, value: list[dict]):
        import json
        self.rules = json.dumps(value)
