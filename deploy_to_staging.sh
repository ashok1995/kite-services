#!/bin/bash
# Deploy Kite Services to Staging (local only, port 8279)
# Same process as prod: Docker build + compose. Run from repo root.
# Uses develop branch. After merge to develop, run this to deploy staging locally.

set -e

cd "$(dirname "$0")"
SERVICE_PORT="8279"
COMPOSE_FILE="docker-compose.staging.yml"

echo "🚀 Deploying Kite Services to Staging (local, port $SERVICE_PORT)..."
echo ""

echo "📥 Using develop branch..."
git fetch origin develop
git checkout develop
git pull origin develop

echo "🐳 Rebuilding image (no cache) and recreating containers..."
docker compose -f "$COMPOSE_FILE" build --no-cache
docker compose -f "$COMPOSE_FILE" up -d --force-recreate

echo "⏳ Waiting for service to start (up to 60s)..."
for i in $(seq 1 12); do
    sleep 5
    if curl -sf "http://localhost:$SERVICE_PORT/health" > /dev/null 2>&1; then break; fi
    if [ "$i" -eq 12 ]; then
        echo "❌ Health check timed out"
        docker compose -f "$COMPOSE_FILE" logs --tail=50
        exit 1
    fi
done

echo "🔍 Checking service health..."
if curl -sf "http://localhost:$SERVICE_PORT/health" > /dev/null 2>&1; then
    echo "✅ Staging is healthy!"
    curl -s "http://localhost:$SERVICE_PORT/health" | python3 -m json.tool 2>/dev/null || curl -s "http://localhost:$SERVICE_PORT/health"
else
    echo "❌ Staging health check failed"
    echo "📋 Container logs:"
    docker compose -f "$COMPOSE_FILE" logs --tail=50
    exit 1
fi

echo ""
echo "✅ Staging deployment complete!"
echo "🌐 Staging running on: http://localhost:$SERVICE_PORT"
