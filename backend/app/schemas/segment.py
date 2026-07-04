from typing import Any

from pydantic import BaseModel, ConfigDict


class SegmentRule(BaseModel):
    field: str
    operator: str
    value: Any


class SegmentBase(BaseModel):
    name: str
    description: str | None = None
    rules: list[SegmentRule]


class SegmentCreate(SegmentBase):
    pass


class SegmentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    rules: list[SegmentRule] | None = None
    is_dynamic: bool | None = None


class SegmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None = None
    rules: Any
    contact_count: int
    is_dynamic: bool
    created_at: str
    updated_at: str | None = None


class SegmentListResponse(BaseModel):
    items: list[SegmentResponse]
    total: int
    page: int
    per_page: int
