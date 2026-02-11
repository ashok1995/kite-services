#!/bin/bash
# Run staging locally on port 8279
# Use this to test changes before deploying to prod on VM

set -e
cd "$(dirname "$0")/.."
echo "🚀 Starting staging (port 8279)..."
ENVIRONMENT=staging SERVICE_PORT=8279 poetry run python src/main.py
