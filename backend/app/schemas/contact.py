from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class ContactBase(BaseModel):
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    company: str | None = None
    tags: list[str] = []


class ContactCreate(ContactBase):
    source: str = "manual"


class ContactUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    company: str | None = None
    tags: list[str] | None = None
    status: str | None = None
    engagement_score: int | None = None


class ContactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    company: str | None = None
    tags: list[str] = []
    status: str
    source: str
    engagement_score: int
    bounce_count: int = 0
    created_at: str
    updated_at: str | None = None
    last_engaged_at: str | None = None
    unsubscribed_at: str | None = None


class ContactListResponse(BaseModel):
    items: list[ContactResponse]
    total: int
    page: int
    per_page: int
