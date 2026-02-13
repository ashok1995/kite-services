#!/bin/bash
# Deploy Kite Services to Production VM
# Run this script on the production VM

set -e

VM_HOST="203.57.85.72"
VM_USER="root"
VM_PASSWORD="i1sS4UMRi7FXnDy9"
PROJECT_DIR="/opt/kite-services"
SERVICE_PORT="8179"

echo "🚀 Deploying Kite Services to Production..."
echo ""

# Check if running on VM or locally
if [ "$(hostname)" != "vm488109385" ] && [ ! -f "/opt/kite-services" ]; then
    echo "📡 Connecting to VM and deploying..."
    
    sshpass -p "$VM_PASSWORD" ssh -o StrictHostKeyChecking=no "$VM_USER@$VM_HOST" << 'ENDSSH'
        cd /opt/kite-services
        echo "📥 Pulling latest code from main branch..."
        git pull origin main || git clone https://github.com/ashok1995/kite-services.git /opt/kite-services
        
        cd /opt/kite-services
        echo "🐳 Building and starting Docker containers..."
        docker compose -f docker-compose.prod.yml pull || true
        docker compose -f docker-compose.prod.yml build
        docker compose -f docker-compose.prod.yml up -d --force-recreate
        
        echo "⏳ Waiting for service to start..."
        sleep 15
        
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
    
    echo "📥 Pulling latest code from main branch..."
    git pull origin main
    
    echo "🐳 Building and starting Docker containers..."
    docker compose -f docker-compose.prod.yml pull || true
    docker compose -f docker-compose.prod.yml build
    docker compose -f docker-compose.prod.yml up -d --force-recreate
    
    echo "⏳ Waiting for service to start..."
    sleep 15
    
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
