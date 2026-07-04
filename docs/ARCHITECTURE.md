# Citadel Marketing Platform — Architecture

## System Overview

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Browser    │────▶│    Nginx     │────▶│  Frontend   │
│  Dashboard   │     │  (reverse    │     │  React 19   │
└─────────────┘     │   proxy)     │     │  Vite       │
                    └──────┬───────┘     └─────────────┘
                           │
                    ┌──────▼───────┐     ┌─────────────┐
                    │   Backend    │────▶│ PostgreSQL   │
                    │  FastAPI     │     │  16          │
                    │  Python 3.12 │     └─────────────┘
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐     ┌─────────────┐
                    │   Celery     │────▶│   Redis 7   │
                    │  Workers     │     │  (broker +   │
                    │  + Beat      │     │   cache)     │
                    └──────┬───────┘     └─────────────┘
                           │
                    ┌──────▼───────┐
                    │   Resend     │
                    │  (email      │
                    │   delivery)  │
                    └──────────────┘
```

## Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Backend API | FastAPI + SQLAlchemy 2.0 | REST API, business logic |
| Workers | Celery 5 | Campaign sending, CSV import, analytics |
| Scheduler | Celery Beat | Scheduled campaigns, segment refresh, cleanup |
| Database | PostgreSQL 16 | Contacts, campaigns, events, workflows |
| Cache/Broker | Redis 7 | Task queue, rate limiting, caching |
| Frontend | React 19 + Vite + Recharts | Dashboard, campaign builder |
| Proxy | Nginx | Reverse proxy, rate limiting, security headers |
| Monitoring | Prometheus | Metrics collection |
| Email | Resend API | Email delivery with DKIM/SPF |
| AI | Anthropic Claude | Campaign content generation |

## Data Flow

### CSV Import
CSV upload → Save to disk → Create ImportJob → Celery task → Pandas read → Validate emails → Dedup against DB → Bulk insert → Update job status

### Campaign Send
Create campaign → Select segment → Schedule/Send now → Celery task → Load recipients → Filter suppressed → Rate-limited send via Resend → Track events via webhooks

### Webhook Processing
Resend webhook → Parse event → Create EmailEvent → Update campaign counters → Handle bounces/complaints → Update contact status
