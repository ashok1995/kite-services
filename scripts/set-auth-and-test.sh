#!/usr/bin/env bash
# Set Kite credentials and access token via API, then run endpoint tests.
# Usage:
#   export KITE_API_KEY=your_api_key KITE_API_SECRET=your_secret KITE_ACCESS_TOKEN=your_token
#   ./scripts/set-auth-and-test.sh
# Or: KITE_API_KEY=... KITE_API_SECRET=... KITE_ACCESS_TOKEN=... ./scripts/set-auth-and-test.sh

set -e
cd "$(dirname "$0")/.."
BASE="${TEST_BASE_URL:-http://127.0.0.1:8079}"

if [ -z "$KITE_API_KEY" ] || [ -z "$KITE_API_SECRET" ]; then
  echo "Set KITE_API_KEY and KITE_API_SECRET (and optionally KITE_ACCESS_TOKEN)."
  echo "Example: export KITE_API_KEY=xxx KITE_API_SECRET=yyy KITE_ACCESS_TOKEN=zzz"
  exit 1
fi

echo "=== Setting credentials at $BASE ==="
curl -s -X POST "$BASE/api/auth/credentials" \
  -H "Content-Type: application/json" \
  -d "{\"api_key\": \"$KITE_API_KEY\", \"api_secret\": \"$KITE_API_SECRET\"}" | head -5
echo ""

if [ -n "$KITE_ACCESS_TOKEN" ]; then
  echo "=== Setting access token ==="
  curl -s -X PUT "$BASE/api/auth/token" \
    -H "Content-Type: application/json" \
    -d "{\"access_token\": \"$KITE_ACCESS_TOKEN\"}" | head -5
  echo ""
fi

echo "=== Auth status ==="
curl -s "$BASE/api/auth/status" | head -5
echo ""

echo "=== Running endpoint tests ==="
export TEST_BASE_URL="$BASE"
poetry run pytest tests/e2e/test_prod_endpoints.py tests/integration/test_auth_token_flow.py tests/e2e/test_deployment_reliability.py -v --tb=short
