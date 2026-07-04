# Deployment Guide

## Prerequisites
- Docker and Docker Compose
- Resend account with verified domain
- Anthropic API key (optional, for AI content generation)

## Quick Start

```bash
# 1. Clone and enter directory
cd citadel-marketing-platform

# 2. Run setup
chmod +x scripts/setup.sh
./scripts/setup.sh

# 3. Open dashboard
open http://localhost:3000
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable | Required | Description |
|----------|----------|-------------|
| RESEND_API_KEY | Yes | Resend API key for email delivery |
| ANTHROPIC_API_KEY | No | Claude API key for AI content generation |
| APP_SECRET_KEY | Yes | Random secret for JWT signing |
| POSTGRES_PASSWORD | Yes | Database password |
| MAX_DAILY_SENDS | No | Daily send limit (default: 5000) |
| SEND_RATE_PER_MINUTE | No | Emails per minute (default: 60) |

## Domain Verification

1. Log into Resend dashboard
2. Add your sending domain
3. Add DNS records (DKIM, SPF, DMARC) to your domain registrar
4. Verify in the Settings page of the dashboard

## Backup

```bash
./scripts/backup.sh
```

Backups are stored in `backups/` directory. Last 30 are kept automatically.

## Warmup Schedule

New sending domains should follow a warmup schedule:
```bash
python scripts/warmup.py
```

## Monitoring

- Prometheus: http://localhost:9090
- API health: http://localhost:8000/api/v1/health
- API docs: http://localhost:8000/api/docs
