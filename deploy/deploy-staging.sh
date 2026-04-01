#!/bin/bash
# =============================================================================
# Deploy Kite Services to Staging (local only, port 8279)
# Uses develop branch; builds image and runs docker-compose.staging.yml.
# Run from repo root: ./deploy/deploy-staging.sh
# =============================================================================
set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

SERVICE_PORT="8279"
COMPOSE_FILE="docker-compose.staging.yml"
BUILD_EXTRA=""
[ "${FULL_REBUILD:-0}" = "1" ] && BUILD_EXTRA="--no-cache"

echo "============================================"
echo "  Kite Services — Staging Deploy (local)"
echo "============================================"
echo "  Port:   http://localhost:${SERVICE_PORT}"
echo "============================================"
echo ""

if [ -n "$(git status --porcelain)" ]; then
  echo "❌ Uncommitted changes. Commit and push to develop first."
  exit 1
fi
git fetch origin develop
git checkout develop
if [ -n "$(git rev-list origin/develop..HEAD 2>/dev/null)" ]; then
  echo "❌ Local develop ahead of origin. Push first."
  exit 1
fi
git pull origin develop

echo "🐳 Build and start staging..."
docker compose -f "$COMPOSE_FILE" build $BUILD_EXTRA
docker compose -f "$COMPOSE_FILE" up -d --force-recreate

echo "⏳ Waiting for health (up to 60s)..."
for i in $(seq 1 12); do
  sleep 5
  curl -sf "http://localhost:$SERVICE_PORT/health" >/dev/null 2>&1 && break
  [ "$i" -eq 12 ] && { echo "❌ Timeout"; docker compose -f "$COMPOSE_FILE" logs --tail=50; exit 1; }
done

echo "✅ Staging OK: http://localhost:$SERVICE_PORT/health"
echo ""
