#!/bin/bash
# Run staging locally on port 8279 (uses envs/staging.env)
set -e
cd "$(dirname "$0")/.."
echo "🚀 Starting staging (port 8279)..."
export ENVIRONMENT=staging
poetry run python src/main.py
