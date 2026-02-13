#!/bin/bash
# Run endpoint tests against prod (8179) or dev (8079)
# Usage: ./tests/run_endpoint_tests.sh prod|dev

set -e

PORT="${1:-prod}"

if [ "$PORT" = "prod" ]; then
  BASE="http://203.57.85.72:8179"
  echo "=== Testing PROD ($BASE) ==="
elif [ "$PORT" = "dev" ]; then
  BASE="http://127.0.0.1:8079"
  echo "=== Testing DEV ($BASE) ==="
else
  echo "Usage: $0 prod|dev"
  exit 1
fi

export TEST_BASE_URL="$BASE"
poetry run pytest tests/e2e/test_prod_endpoints.py tests/integration/test_auth_token_flow.py -v --tb=short
