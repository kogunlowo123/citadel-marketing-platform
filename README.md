# Citadel Marketing Platform

Self-hosted marketing automation for Citadel Cloud Management. Import contacts, segment audiences, create AI-powered campaigns, schedule sends, track engagement, and automate follow-ups — all running locally via Docker.

## Features

- **CSV Import** — Bulk import contacts with auto-column detection, email validation, deduplication
- **Audience Segmentation** — Dynamic segments with rule-based filtering
- **Campaign Builder** — Create, schedule, and send email campaigns
- **AI Content Generation** — Generate email content with Claude API
- **Analytics Dashboard** — Opens, clicks, bounces, engagement trends
- **Workflow Automation** — Welcome series, follow-ups, re-engagement, cleanup
- **Compliance** — CAN-SPAM footer, one-click unsubscribe, bounce handling, rate limiting
- **DKIM/SPF/DMARC** — Domain verification checks
- **Resend Integration** — Reliable email delivery with webhook tracking

## Architecture

```
Frontend (React 19) → Nginx → Backend (FastAPI)
                                  ↓
                        PostgreSQL + Redis
                                  ↓
                        Celery Workers → Resend API
```

## Quick Start

```bash
# 1. Setup
./scripts/setup.sh

# 2. Open dashboard
open http://localhost:3000
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0, Celery |
| Frontend | React 19, TypeScript, Vite, Recharts, Tailwind |
| Database | PostgreSQL 16 |
| Cache | Redis 7 |
| Email | Resend API |
| AI | Anthropic Claude API |
| Deploy | Docker Compose |
| Monitoring | Prometheus |

## Project Structure

```
citadel-marketing-platform/
├── docker/          # Docker Compose + service configs
├── backend/         # FastAPI app (API, services, workers)
├── frontend/        # React dashboard
├── workflows/       # Reusable workflow templates (JSON)
├── scripts/         # Setup, backup, warmup scripts
├── docs/            # Architecture, deployment, API docs
└── .env.example     # Environment variable template
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [API Reference](http://localhost:8000/api/docs) (when running)

## License

MIT — Citadel Cloud Management
