#!/bin/bash
# Deploy Kite Services to Staging (local only, port 8279)
# Pulls image from GHCR (no local build). Run from repo root.

set -e

cd "$(dirname "$0")"
SERVICE_PORT="8279"
COMPOSE_FILE="docker-compose.staging.yml"

echo "Deploying Kite Services to Staging (GHCR pull, port $SERVICE_PORT)..."
echo ""

echo "Stopping old containers..."
docker compose -f "$COMPOSE_FILE" down --remove-orphans 2>/dev/null || true

echo "Pulling latest staging image from GHCR..."
docker compose -f "$COMPOSE_FILE" pull

echo "Starting containers..."
docker compose -f "$COMPOSE_FILE" up -d

echo "Waiting for service to start (up to 60s)..."
for i in $(seq 1 12); do
    sleep 5
    if curl -sf "http://localhost:$SERVICE_PORT/health" > /dev/null 2>&1; then break; fi
    if [ "$i" -eq 12 ]; then
        echo "Health check timed out"
        docker compose -f "$COMPOSE_FILE" logs --tail=50
        exit 1
    fi
done

if curl -sf "http://localhost:$SERVICE_PORT/health" > /dev/null 2>&1; then
    echo "Staging is healthy!"
    curl -s "http://localhost:$SERVICE_PORT/health" | python3 -m json.tool 2>/dev/null || curl -s "http://localhost:$SERVICE_PORT/health"
else
    echo "Staging health check failed"
    docker compose -f "$COMPOSE_FILE" logs --tail=50
    exit 1
fi

echo ""
echo "Staging deployment complete!"
echo "Running on: http://localhost:$SERVICE_PORT"
