#!/usr/bin/env bash
set -euo pipefail

echo "=== Citadel Marketing Platform Setup ==="
echo ""

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "Docker is required but not installed."; exit 1; }
command -v docker compose >/dev/null 2>&1 || { echo "Docker Compose is required."; exit 1; }

cd "$(dirname "$0")/.."

# Create .env if missing
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env from .env.example"

    # Generate secret key
    SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(48))" 2>/dev/null || openssl rand -base64 48)
    sed -i "s/generate_a_secure_random_key_here/$SECRET/" .env

    read -p "Resend API key: " RESEND_KEY
    sed -i "s/re_your_key_here/$RESEND_KEY/" .env

    read -p "Anthropic API key (optional, press Enter to skip): " ANTHROPIC_KEY
    if [ -n "$ANTHROPIC_KEY" ]; then
        sed -i "s/sk-ant-your_key_here/$ANTHROPIC_KEY/" .env
    fi
fi

echo ""
echo "Building containers..."
docker compose -f docker/compose.yml build

echo "Starting services..."
docker compose -f docker/compose.yml up -d

echo "Waiting for PostgreSQL..."
sleep 5
until docker compose -f docker/compose.yml exec -T postgres pg_isready -U citadel 2>/dev/null; do
    sleep 2
done

echo "Running database migrations..."
docker compose -f docker/compose.yml exec -T backend alembic upgrade head

echo ""
echo "=== Setup Complete ==="
echo "Dashboard:  http://localhost:3000"
echo "API:        http://localhost:8000/api/docs"
echo "Prometheus: http://localhost:9090"
echo ""
echo "Create your admin account at http://localhost:3000"
