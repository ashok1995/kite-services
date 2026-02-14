#!/bin/bash
# Run staging without Docker (port 8279). For same process as prod use ./deploy_to_staging.sh
set -e
cd "$(dirname "$0")/.."
echo "🚀 Starting staging without Docker (port 8279)..."
echo "   (For Docker-based staging, same as prod, run: ./deploy_to_staging.sh)"
export ENVIRONMENT=staging
poetry run python src/main.py
