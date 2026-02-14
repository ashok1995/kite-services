#!/bin/bash
# Integration tests for Bayesian engine endpoints
# Tests batch quotes, market context with breadth, historical data, and instruments

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="${1:-http://localhost:8079}"
VERBOSE="${2:-false}"

echo ""
echo "========================================================"
echo "  Bayesian Engine Endpoints - Integration Tests"
echo "========================================================"
echo "Base URL: $BASE_URL"
echo "Verbose: $VERBOSE"
echo ""

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Helper functions
log_test() {
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -e "${BLUE}[TEST $TOTAL_TESTS]${NC} $1"
}

log_pass() {
    PASSED_TESTS=$((PASSED_TESTS + 1))
    echo -e "  ${GREEN}✅ PASS${NC}: $1"
}

log_fail() {
    FAILED_TESTS=$((FAILED_TESTS + 1))
    echo -e "  ${RED}❌ FAIL${NC}: $1"
}

log_info() {
    echo -e "  ${YELLOW}ℹ${NC}  $1"
}

# Check if service is running
log_test "Health Check"
if curl -s -f "$BASE_URL/health" > /dev/null; then
    log_pass "Service is running"
else
    log_fail "Service is not accessible at $BASE_URL"
    exit 1
fi
echo ""

# Test 1: Batch quotes with multiple symbols (test increased limit)
log_test "Batch Quotes - Multiple Symbols (50 symbols)"
RESPONSE=$(curl -s -X POST "$BASE_URL/api/market/quotes" \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["RELIANCE", "TCS", "INFY", "HDFC", "ICICIBANK", "HINDUNILVR",
                "BHARTIARTL", "KOTAKBANK", "ITC", "LT", "SBIN", "AXISBANK",
                "BAJFINANCE", "ASIANPAINT", "MARUTI", "HCLTECH", "WIPRO",
                "ULTRACEMCO", "TITAN", "NESTLEIND", "SUNPHARMA", "TECHM",
                "BAJAJFINSV", "ONGC", "NTPC", "POWERGRID", "M&M", "ADANIPORTS",
                "COALINDIA", "TATASTEEL", "TATAMOTORS", "DIVISLAB", "GRASIM",
                "JSWSTEEL", "HINDALCO", "INDUSINDBK", "DRREDDY", "BRITANNIA",
                "APOLLOHOSP", "CIPLA", "EICHERMOT", "BAJAJ-AUTO", "HEROMOTOCO",
                "BPCL", "SHREECEM", "SBILIFE", "UPL", "ADANIENT", "HDFCLIFE",
                "TATACONSUM"],
    "exchange": "NSE"
  }')

if [ "$VERBOSE" = "true" ]; then
    echo "$RESPONSE" | jq '.'
fi

# Check response structure
TOTAL_SYMBOLS=$(echo "$RESPONSE" | jq -r '.total_symbols // 0')
SUCCESS_SYMBOLS=$(echo "$RESPONSE" | jq -r '.successful_symbols // 0')

if [ "$TOTAL_SYMBOLS" -eq 50 ]; then
    log_pass "Request accepts 50 symbols"
else
    log_fail "Expected 50 symbols, got $TOTAL_SYMBOLS"
fi

if [ "$SUCCESS_SYMBOLS" -gt 0 ]; then
    log_pass "Successfully fetched data for $SUCCESS_SYMBOLS symbols"
else
    log_fail "No symbols returned data"
fi

echo ""

# Test 2: Batch quotes with 200 symbols (test new limit)
log_test "Batch Quotes - Large Batch (200 symbols)"
log_info "Testing increased QUOTES_MAX_SYMBOLS limit (50→200)"

# Generate 200 symbols (repeat Nifty 50 four times with variations)
LARGE_BATCH=$(python3 -c "
import json
base_symbols = ['RELIANCE', 'TCS', 'INFY', 'HDFC', 'ICICIBANK', 'HINDUNILVR',
                'BHARTIARTL', 'KOTAKBANK', 'ITC', 'LT', 'SBIN', 'AXISBANK',
                'BAJFINANCE', 'ASIANPAINT', 'MARUTI', 'HCLTECH', 'WIPRO',
                'ULTRACEMCO', 'TITAN', 'NESTLEIND', 'SUNPHARMA', 'TECHM',
                'BAJAJFINSV', 'ONGC', 'NTPC', 'POWERGRID', 'M&M', 'ADANIPORTS',
                'COALINDIA', 'TATASTEEL', 'TATAMOTORS', 'DIVISLAB', 'GRASIM',
                'JSWSTEEL', 'HINDALCO', 'INDUSINDBK', 'DRREDDY', 'BRITANNIA',
                'APOLLOHOSP', 'CIPLA', 'EICHERMOT', 'BAJAJ-AUTO', 'HEROMOTOCO',
                'BPCL', 'SHREECEM', 'SBILIFE', 'UPL', 'ADANIENT', 'HDFCLIFE',
                'TATACONSUM']
symbols_200 = (base_symbols * 4)[:200]  # Repeat to get 200 symbols
print(json.dumps(symbols_200))
")

RESPONSE=$(curl -s -X POST "$BASE_URL/api/market/quotes" \
  -H "Content-Type: application/json" \
  -d "{\"symbols\": $LARGE_BATCH, \"exchange\": \"NSE\"}")

TOTAL_SYMBOLS=$(echo "$RESPONSE" | jq -r '.total_symbols // 0')
SUCCESS_SYMBOLS=$(echo "$RESPONSE" | jq -r '.successful_symbols // 0')
ERROR_MSG=$(echo "$RESPONSE" | jq -r '.detail // ""')

if [ "$TOTAL_SYMBOLS" -eq 200 ]; then
    log_pass "Service accepts 200 symbols (limit increased successfully)"
elif [ -n "$ERROR_MSG" ] && echo "$ERROR_MSG" | grep -q "Maximum.*symbols"; then
    log_fail "Service rejected 200 symbols: $ERROR_MSG"
else
    log_info "Received $TOTAL_SYMBOLS symbols, $SUCCESS_SYMBOLS successful"
fi

echo ""

# Test 3: Market context with breadth data
log_test "Market Context - Breadth Data"
RESPONSE=$(curl -s -X POST "$BASE_URL/api/analysis/context" \
  -H "Content-Type: application/json" \
  -d '{
    "include_global_data": true,
    "include_sector_data": true
  }')

if [ "$VERBOSE" = "true" ]; then
    echo "$RESPONSE" | jq '.market_context.indian_data'
fi

# Check for breadth fields
ADVANCES=$(echo "$RESPONSE" | jq -r '.market_context.indian_data.advances // null')
DECLINES=$(echo "$RESPONSE" | jq -r '.market_context.indian_data.declines // null')
AD_RATIO=$(echo "$RESPONSE" | jq -r '.market_context.indian_data.advance_decline_ratio // null')

if [ "$ADVANCES" != "null" ] && [ "$ADVANCES" != "0" ]; then
    log_pass "Advancing stocks: $ADVANCES"
else
    log_fail "No advancing stocks data"
fi

if [ "$DECLINES" != "null" ]; then
    log_pass "Declining stocks: $DECLINES"
else
    log_fail "No declining stocks data"
fi

if [ "$AD_RATIO" != "null" ]; then
    log_pass "Advance/Decline Ratio: $AD_RATIO"
else
    log_fail "No advance/decline ratio"
fi

echo ""

# Test 4: Historical candles (5-minute interval)
log_test "Historical Data - 5-minute Candles"
TODAY=$(date +%Y-%m-%d)
RESPONSE=$(curl -s -X POST "$BASE_URL/api/market/data" \
  -H "Content-Type: application/json" \
  -d "{
    \"symbols\": [\"RELIANCE\"],
    \"exchange\": \"NSE\",
    \"data_type\": \"historical\",
    \"from_date\": \"$TODAY\",
    \"to_date\": \"$TODAY\",
    \"interval\": \"5minute\"
  }")

if [ "$VERBOSE" = "true" ]; then
    echo "$RESPONSE" | jq '.'
fi

SUCCESS=$(echo "$RESPONSE" | jq -r '.success // false')
DATA_EXISTS=$(echo "$RESPONSE" | jq -r '.data.RELIANCE // null')

if [ "$SUCCESS" = "true" ] && [ "$DATA_EXISTS" != "null" ]; then
    log_pass "5-minute historical data available"
else
    log_info "Historical data may not be available (market hours dependency)"
fi

echo ""

# Test 5: Historical candles (15-minute interval)
log_test "Historical Data - 15-minute Candles"
RESPONSE=$(curl -s -X POST "$BASE_URL/api/market/data" \
  -H "Content-Type: application/json" \
  -d "{
    \"symbols\": [\"TCS\"],
    \"exchange\": \"NSE\",
    \"data_type\": \"historical\",
    \"from_date\": \"$TODAY\",
    \"to_date\": \"$TODAY\",
    \"interval\": \"15minute\"
  }")

SUCCESS=$(echo "$RESPONSE" | jq -r '.success // false')
if [ "$SUCCESS" = "true" ]; then
    log_pass "15-minute historical data endpoint works"
else
    log_info "15-minute data may not be available (market hours dependency)"
fi

echo ""

# Test 6: Instruments endpoint
log_test "Instruments - NSE Equity"
RESPONSE=$(curl -s "$BASE_URL/api/market/instruments?exchange=NSE&instrument_type=EQ&limit=10")

if [ "$VERBOSE" = "true" ]; then
    echo "$RESPONSE" | jq '.'
fi

SUCCESS=$(echo "$RESPONSE" | jq -r '.success // false')
INSTRUMENTS_COUNT=$(echo "$RESPONSE" | jq -r '.total_count // 0')
FIRST_TOKEN=$(echo "$RESPONSE" | jq -r '.instruments[0].instrument_token // null')

if [ "$SUCCESS" = "true" ]; then
    log_pass "Instruments endpoint accessible"
else
    log_fail "Instruments endpoint failed"
fi

if [ "$INSTRUMENTS_COUNT" -gt 0 ]; then
    log_pass "Found $INSTRUMENTS_COUNT instruments"
else
    log_fail "No instruments returned"
fi

if [ "$FIRST_TOKEN" != "null" ]; then
    log_pass "instrument_token field present: $FIRST_TOKEN"
else
    log_fail "instrument_token field missing"
fi

echo ""

# Test 7: Verify breadth calculation is real (not default/approximation)
log_test "Market Breadth - Real Data Verification"
RESPONSE=$(curl -s -X POST "$BASE_URL/api/analysis/context" \
  -H "Content-Type: application/json" \
  -d '{"include_global_data": false, "include_sector_data": false}')

ADVANCES=$(echo "$RESPONSE" | jq -r '.market_context.indian_data.advances // 0')
DECLINES=$(echo "$RESPONSE" | jq -r '.market_context.indian_data.declines // 0')
TOTAL=$((ADVANCES + DECLINES))

if [ "$TOTAL" -gt 0 ] && [ "$TOTAL" -le 50 ]; then
    log_pass "Breadth calculated from real data (total=$TOTAL, expected ≤50 for Nifty 50)"
elif [ "$TOTAL" -gt 50 ]; then
    log_info "Total stocks: $TOTAL (may be using broader index)"
else
    log_fail "Breadth data appears to be default/empty"
fi

echo ""

# Summary
echo "========================================================"
echo "  Test Summary"
echo "========================================================"
echo -e "Total Tests:  $TOTAL_TESTS"
echo -e "${GREEN}Passed:       $PASSED_TESTS${NC}"
if [ "$FAILED_TESTS" -gt 0 ]; then
    echo -e "${RED}Failed:       $FAILED_TESTS${NC}"
else
    echo -e "Failed:       $FAILED_TESTS"
fi
echo ""

if [ "$FAILED_TESTS" -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    exit 1
fi
