#!/bin/bash
# Run ON the VM: ssh root@203.57.85.72, then:
#   cd /opt/kite-services && ./scripts/deploy_on_vm.sh
#
# Default: git pull + restart only (~10 sec). ./src is volume-mounted.
# Use: BUILD=1 ./scripts/deploy_on_vm.sh when pyproject.toml/poetry.lock changed.

set -e

cd /opt/kite-services || { git clone https://github.com/ashok1995/kite-services.git /opt/kite-services && cd /opt/kite-services; }

echo "📥 Fetching latest from main..."
git fetch origin main
git checkout main
git reset --hard origin/main

if [ "${BUILD:-0}" = "1" ]; then
  echo "🐳 Building (BUILD=1; RAM limit 2GB)..."
  docker build --memory=2g --memory-swap=2g -t kite-services:latest .
else
  echo "⚡ Skipping build (code only; ./src mounted). BUILD=1 to rebuild."
fi

echo "🔄 Restarting containers..."
docker compose -f docker-compose.prod.yml up -d --force-recreate

echo "⏳ Waiting for health (up to 60s)..."
for i in $(seq 1 12); do
  sleep 5
  curl -sf http://localhost:8179/health >/dev/null 2>&1 && break
  [ "$i" -eq 12 ] && { echo "❌ Timeout"; docker compose -f docker-compose.prod.yml logs --tail=30; exit 1; }
done

echo "✅ Done. Health:" && curl -s http://localhost:8179/health | head -5
