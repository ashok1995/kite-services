#!/bin/bash
# Deploy Kite Services to Production VM
#
# Image is built in CI and pushed to ghcr.io. VM only pulls (no build on VM).
# ~15–30 sec deploy; no 3hr builds on 4GB VM.

set -e

VM_HOST="${VM_HOST:-35.232.205.155}"
VM_USER="${VM_USER:-root}"
VM_PASSWORD="${VM_PASSWORD:?Set VM_PASSWORD for SSH}"
PROJECT_DIR="/opt/kite-services"
SERVICE_PORT="8179"

echo "🚀 Deploying Kite Services to Production (pull-only, no build on VM)..."
echo ""

# Check if running on VM or locally
if [ "$(hostname)" != "vm488109385" ] && [ ! -f "/opt/kite-services" ]; then
    echo "📡 Connecting to VM and deploying..."

    sshpass -p "$VM_PASSWORD" ssh -o StrictHostKeyChecking=no "$VM_USER@$VM_HOST" "bash -s" << 'ENDSSH'
        cd /opt/kite-services || { git clone https://github.com/ashok1995/kite-services.git /opt/kite-services && cd /opt/kite-services; }
        echo "📥 Fetching latest from main..."
        git fetch origin main
        git checkout main
        git reset --hard origin/main
        echo "🛑 Stopping old containers..."
        docker compose -f docker-compose.prod.yml down --remove-orphans 2>/dev/null || true
        echo "📦 Pulling image from ghcr.io (no build on VM)..."
        docker compose -f docker-compose.prod.yml pull
        echo "🔄 Starting containers..."
        docker compose -f docker-compose.prod.yml up -d

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
        echo "🌐 Service running on: http://35.232.205.155:8179"
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

    echo "📥 Fetching latest from main..."
    git fetch origin main
    git checkout main
    git reset --hard origin/main
    echo "🛑 Stopping old containers..."
    docker compose -f docker-compose.prod.yml down --remove-orphans 2>/dev/null || true
    echo "📦 Pulling image from ghcr.io..."
    docker compose -f docker-compose.prod.yml pull
    echo "🔄 Starting containers..."
    docker compose -f docker-compose.prod.yml up -d

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
    echo "🌐 Service running on: http://35.232.205.155:$SERVICE_PORT"
fi
