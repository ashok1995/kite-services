#!/bin/bash
# Deploy Kite Services to Production VM
# Run this script on the production VM

set -e

VM_HOST="${VM_HOST:-203.57.85.72}"
VM_USER="${VM_USER:-root}"
# Set VM_PASSWORD in env (or .env) - never commit passwords to repo
VM_PASSWORD="${VM_PASSWORD:?Set VM_PASSWORD for SSH (e.g. export VM_PASSWORD=yourpass)}"
PROJECT_DIR="/opt/kite-services"
SERVICE_PORT="8179"

echo "🚀 Deploying Kite Services to Production..."
echo ""

# Check if running on VM or locally
if [ "$(hostname)" != "vm488109385" ] && [ ! -f "/opt/kite-services" ]; then
    echo "📡 Connecting to VM and deploying..."

    sshpass -p "$VM_PASSWORD" ssh -o StrictHostKeyChecking=no "$VM_USER@$VM_HOST" << 'ENDSSH'
        cd /opt/kite-services || { git clone https://github.com/ashok1995/kite-services.git /opt/kite-services && cd /opt/kite-services; }
        echo "📥 Fetching latest from main (hard reset to match remote)..."
        git fetch origin main
        git checkout main
        git reset --hard origin/main
        echo "🐳 Rebuilding image (no cache) and recreating containers..."
        docker compose -f docker-compose.prod.yml build --no-cache
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

    echo "🐳 Rebuilding image (no cache) and recreating containers..."
    docker compose -f docker-compose.prod.yml build --no-cache
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

    echo ""
    echo "✅ Deployment complete!"
    echo "🌐 Service running on: http://203.57.85.72:$SERVICE_PORT"
fi
