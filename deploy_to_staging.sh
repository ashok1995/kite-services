#!/bin/bash
# Deploy Kite Services to Staging (local only, port 8279)
# Same process as prod: Docker build + compose. Run from repo root.
# Uses develop branch. By default uses Docker cache for fast deploys (~1–3 min).
# Use FULL_REBUILD=1 when you change pyproject.toml/poetry.lock.

set -e

cd "$(dirname "$0")"
SERVICE_PORT="8279"
COMPOSE_FILE="docker-compose.staging.yml"
BUILD_EXTRA=""
[ "${FULL_REBUILD:-0}" = "1" ] && BUILD_EXTRA="--no-cache"

echo "🚀 Deploying Kite Services to Staging (local, port $SERVICE_PORT)..."
[ -n "$BUILD_EXTRA" ] && echo "   (full rebuild: no cache)"
echo ""

# Rule: commit and push before deployment — deploy uses what's on remote
if [ -n "$(git status --porcelain)" ]; then
    echo "❌ Uncommitted changes detected. Commit and push to develop before deploying."
    echo "   git add -A && git commit -m '...' && git push origin develop"
    exit 1
fi
git fetch origin develop
git checkout develop
if [ -n "$(git rev-list origin/develop..HEAD 2>/dev/null)" ]; then
    echo "❌ Local develop is ahead of origin/develop. Push before deploying."
    echo "   git push origin develop"
    exit 1
fi

echo "📥 Using develop branch (syncing with remote)..."
git pull origin develop

echo "🐳 Building image (using cache unless FULL_REBUILD=1) and recreating containers..."
docker compose -f "$COMPOSE_FILE" build $BUILD_EXTRA
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

echo "🧹 Cleaning only kite-services dangling images (no effect on other services)..."
for id in $(docker images -f "dangling=true" -q 2>/dev/null); do
  [ "$(docker inspect --format '{{index .Config.Labels "project"}}' "$id" 2>/dev/null)" = "kite-services" ] && docker rmi "$id" 2>/dev/null || true
done
echo ""
echo "✅ Staging deployment complete!"
echo "🌐 Staging running on: http://localhost:$SERVICE_PORT"
