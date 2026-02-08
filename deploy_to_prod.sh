#!/bin/bash
# Production Deployment Script for Kite Services
# Run this on the production VM

set -e

echo "🚀 Kite Services Production Deployment"
echo "======================================"

# 1. Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "📦 Installing Docker..."
    apt-get update -qq
    apt-get install -y -qq ca-certificates curl gnupg lsb-release > /dev/null 2>&1
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update -qq
    apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin > /dev/null 2>&1
    systemctl enable docker
    systemctl start docker
    echo "✅ Docker installed"
else
    echo "✅ Docker already installed"
fi

docker --version
docker compose version

# 2. Create deployment directory
DEPLOY_DIR="/opt/kite-services"
echo "📁 Creating deployment directory: $DEPLOY_DIR"
mkdir -p $DEPLOY_DIR
cd $DEPLOY_DIR

# 3. Stop any existing containers
echo "🛑 Stopping existing containers..."
docker compose -f docker-compose.prod.yml down 2>/dev/null || true

# 4. Build and start
echo "🔨 Building Docker image..."
docker compose -f docker-compose.prod.yml build --no-cache

echo "🚀 Starting services..."
docker compose -f docker-compose.prod.yml up -d

# 5. Wait for health check
echo "⏳ Waiting for service to be healthy..."
sleep 10
for i in {1..30}; do
    if curl -f http://localhost:8179/health > /dev/null 2>&1; then
        echo "✅ Service is healthy!"
        break
    fi
    echo "   Attempt $i/30..."
    sleep 2
done

# 6. Show status
echo ""
echo "📊 Container Status:"
docker compose -f docker-compose.prod.yml ps

echo ""
echo "✅ Deployment complete!"
echo "🌐 Service available at: http://203.57.85.72:8179"
echo "📚 Docs: http://203.57.85.72:8179/docs"
echo "❤️  Health: http://203.57.85.72:8179/health"
