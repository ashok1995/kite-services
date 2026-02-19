#!/bin/bash
# Deploy Kite Services to Production VM
# Run this script on the production VM
#
# Speed: By default we use Docker cache so only code changes rebuild (~1–3 min).
# The slow part is "poetry install" (~30–60 min); it is cached unless deps change.
# Use FULL_REBUILD=1 when you change pyproject.toml/poetry.lock or want a clean image.

set -e

# VM: use IP 203.57.85.72 (hostname vm488109385.manageserver.in may not resolve from all networks)
VM_HOST="${VM_HOST:-203.57.85.72}"
VM_USER="${VM_USER:-root}"
# Set VM_PASSWORD in env - never commit passwords to repo
VM_PASSWORD="${VM_PASSWORD:?Set VM_PASSWORD for SSH (e.g. export VM_PASSWORD=yourpass)}"
PROJECT_DIR="/opt/kite-services"
SERVICE_PORT="8179"
# Use cache by default; set FULL_REBUILD=1 to force full rebuild (no cache)
USE_CACHE="${FULL_REBUILD:-0}"
BUILD_EXTRA=""
[ "$USE_CACHE" = "1" ] && BUILD_EXTRA="--no-cache"

echo "🚀 Deploying Kite Services to Production..."
[ "$USE_CACHE" = "1" ] && echo "   (full rebuild: no cache)"
echo ""

# Check if running on VM or locally
if [ "$(hostname)" != "vm488109385" ] && [ ! -f "/opt/kite-services" ]; then
    echo "📡 Connecting to VM and deploying..."

    sshpass -p "$VM_PASSWORD" ssh -o StrictHostKeyChecking=no "$VM_USER@$VM_HOST" "export FULL_REBUILD=$USE_CACHE; bash -s" << 'ENDSSH'
        BUILD_EXTRA=""
        [ "$FULL_REBUILD" = "1" ] && BUILD_EXTRA="--no-cache"
        cd /opt/kite-services || { git clone https://github.com/ashok1995/kite-services.git /opt/kite-services && cd /opt/kite-services; }
        echo "📥 Fetching latest from main (hard reset to match remote)..."
        git fetch origin main
        git checkout main
        git reset --hard origin/main
        echo "🐳 Building image (using cache unless FULL_REBUILD=1) and recreating containers..."
        docker compose -f docker-compose.prod.yml build $BUILD_EXTRA
        docker compose -f docker-compose.prod.yml up -d --force-recreate

        echo "⏳ Waiting for service to start (up to 60s)..."
        for i in $(seq 1 12); do
            sleep 5
            if curl -sf http://localhost:8179/health > /dev/null 2>&1; then break; fi
            [ "$i" -eq 12 ] && { echo "❌ Health check timed out"; docker compose -f docker-compose.prod.yml logs --tail=50; exit 1; }
        done

        echo "🔍 Checking service health..."
        if curl -f http://localhost:8179/health > /dev/null 2>&1; then
            echo "✅ Service is healthy!"
            curl -s http://localhost:8179/health | python3 -m json.tool || curl -s http://localhost:8179/health
        else
            echo "❌ Service health check failed"
            echo "📋 Container logs:"
            docker compose -f docker-compose.prod.yml logs --tail=50
            exit 1
        fi

        echo "🧹 Cleaning only kite-services dangling images (no effect on other services)..."
        for id in $(docker images -f "dangling=true" -q 2>/dev/null); do
          [ "$(docker inspect --format '{{index .Config.Labels "project"}}' "$id" 2>/dev/null)" = "kite-services" ] && docker rmi "$id" 2>/dev/null || true
        done
        echo ""
        echo "✅ Deployment complete!"
        echo "🌐 Service running on: http://203.57.85.72:8179"
ENDSSH

else
    # Running directly on VM
    echo "📍 Running on VM, deploying directly..."

    cd "$PROJECT_DIR" || {
        echo "❌ Project directory not found: $PROJECT_DIR"
        echo "📥 Cloning repository..."
        git clone https://github.com/ashok1995/kite-services.git "$PROJECT_DIR"
        cd "$PROJECT_DIR"
    }

    echo "📥 Fetching latest from main (hard reset to match remote)..."
    git fetch origin main
    git checkout main
    git reset --hard origin/main

    echo "🐳 Building image (using cache unless FULL_REBUILD=1) and recreating containers..."
    docker compose -f docker-compose.prod.yml build $BUILD_EXTRA
    docker compose -f docker-compose.prod.yml up -d --force-recreate

    echo "⏳ Waiting for service to start (up to 60s)..."
    for i in $(seq 1 12); do
        sleep 5
        if curl -sf http://localhost:$SERVICE_PORT/health > /dev/null 2>&1; then break; fi
        [ "$i" -eq 12 ] && { echo "❌ Health check timed out"; docker compose -f docker-compose.prod.yml logs --tail=50; exit 1; }
    done

    echo "🔍 Checking service health..."
    if curl -f http://localhost:$SERVICE_PORT/health > /dev/null 2>&1; then
        echo "✅ Service is healthy!"
        curl -s http://localhost:$SERVICE_PORT/health | python3 -m json.tool || curl -s http://localhost:$SERVICE_PORT/health
    else
        echo "❌ Service health check failed"
        echo "📋 Container logs:"
        docker compose -f docker-compose.prod.yml logs --tail=50
        exit 1
    fi

    echo "🧹 Cleaning only kite-services dangling images (no effect on other services)..."
    for id in $(docker images -f "dangling=true" -q 2>/dev/null); do
      [ "$(docker inspect --format '{{index .Config.Labels "project"}}' "$id" 2>/dev/null)" = "kite-services" ] && docker rmi "$id" 2>/dev/null || true
    done
    echo ""
    echo "✅ Deployment complete!"
    echo "🌐 Service running on: http://203.57.85.72:$SERVICE_PORT"
fi
