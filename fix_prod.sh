#!/bin/bash
# Quick Fix Script for Production
# Run this on the VM to fix database and restart service

set -e

echo "🔧 Fixing Production Service..."

# Fix database path in config
cd /opt/kite-services
sed -i 's|DATABASE_URL=sqlite+aiosqlite:///data/|DATABASE_URL=sqlite+aiosqlite:////app/data/|' envs/production.env

# Ensure data directory exists
mkdir -p data
chmod 777 data

# Stop containers
docker compose -f docker-compose.prod.yml down

# Rebuild and start
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

echo "⏳ Waiting for service to start..."
sleep 20

# Check status
docker compose -f docker-compose.prod.yml ps

echo ""
echo "🧪 Testing service..."
sleep 5
curl -s http://localhost:8179/health | python3 -m json.tool || curl -s http://localhost:8179/health

echo ""
echo "✅ Fix complete!"
