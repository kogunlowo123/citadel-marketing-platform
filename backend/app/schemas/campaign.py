from pydantic import BaseModel, ConfigDict


class CampaignBase(BaseModel):
    name: str
    subject: str
    preview_text: str | None = None
    html_content: str | None = None
    text_content: str | None = None


class CampaignCreate(CampaignBase):
    segment_id: str | None = None
    send_rate: int = 60


class CampaignUpdate(BaseModel):
    name: str | None = None
    subject: str | None = None
    preview_text: str | None = None
    html_content: str | None = None
    text_content: str | None = None
    segment_id: str | None = None
    send_rate: int | None = None


class CampaignResponse(CampaignBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str
    segment_id: str | None = None
    scheduled_at: str | None = None
    sent_at: str | None = None
    completed_at: str | None = None
    send_rate: int
    total_recipients: int
    sent_count: int
    open_count: int
    click_count: int
    bounce_count: int
    unsubscribe_count: int
    complaint_count: int
    open_rate: float = 0.0
    click_rate: float = 0.0
    created_at: str
    updated_at: str | None = None


class CampaignScheduleRequest(BaseModel):
    scheduled_at: str


class CampaignGenerateRequest(BaseModel):
    topic: str
    tone: str = "professional"
    audience: str = "cloud professionals"
    length: str = "medium"


class CampaignListResponse(BaseModel):
    items: list[CampaignResponse]
    total: int
    page: int
    per_page: int
