#!/bin/bash
# Run staging without Docker (port 8279). For Docker staging use ./deploy/deploy-staging.sh
set -e
cd "$(dirname "$0")/.."
echo "🚀 Starting staging without Docker (port 8279)..."
echo "   (For Docker-based staging run: ./deploy/deploy-staging.sh)"
export ENVIRONMENT=staging
poetry run python src/main.py
