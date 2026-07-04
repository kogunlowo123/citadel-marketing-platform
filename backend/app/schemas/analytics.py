from pydantic import BaseModel


class OverviewStats(BaseModel):
    total_contacts: int
    active_contacts: int
    total_campaigns: int
    campaigns_sent: int
    total_emails_sent: int
    overall_open_rate: float
    overall_click_rate: float
    total_unsubscribes: int
    contacts_added_last_30_days: int


class EngagementData(BaseModel):
    date: str
    opens: int
    clicks: int
    sends: int


class EngagementResponse(BaseModel):
    data: list[EngagementData]
    period: str


class CampaignComparisonItem(BaseModel):
    campaign_id: str
    name: str
    sent: int
    opens: int
    clicks: int
    bounces: int
    open_rate: float
    click_rate: float


class ContactGrowthData(BaseModel):
    date: str
    count: int
