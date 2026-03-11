#!/bin/bash
# Run ON the VM: ssh root@35.232.205.155, then:
#   cd /opt/kite-services && ./scripts/deploy_on_vm.sh
#
# Image built in CI and pushed to ghcr.io. VM only pulls (~15–30 sec).
# No build on VM; avoids 3hr+ builds on 4GB.

set -e

cd /opt/kite-services || { git clone https://github.com/ashok1995/kite-services.git /opt/kite-services && cd /opt/kite-services; }

echo "📥 Fetching latest from main..."
git fetch origin main
git checkout main
git reset --hard origin/main
echo "📦 Pulling image from ghcr.io..."
docker compose -f docker-compose.prod.yml pull
echo "🔄 Restarting containers..."
docker compose -f docker-compose.prod.yml up -d --force-recreate

echo "⏳ Waiting for health (up to 60s)..."
for i in $(seq 1 12); do
  sleep 5
  curl -sf http://localhost:8179/health >/dev/null 2>&1 && break
  [ "$i" -eq 12 ] && { echo "❌ Timeout"; docker compose -f docker-compose.prod.yml logs --tail=30; exit 1; }
done

echo "✅ Done. Health:" && curl -s http://localhost:8179/health | head -5
