#!/bin/bash
# Verification script for Bayesian engine integration changes (Phase 1 & 2)
# Run this after implementing Phase 1 & 2 to verify all changes are working

set -e  # Exit on error

echo "================================================"
echo "Bayesian Engine Integration - Verification"
echo "Phase 1 & 2 (Configuration + Market Breadth)"
echo "================================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the project root
if [ ! -f "src/main.py" ]; then
    echo -e "${RED}❌ Error: Must run from project root${NC}"
    exit 1
fi

echo "📋 Verification Checklist:"
echo ""

# 1. Check configuration files
echo "1️⃣  Checking configuration files..."

check_config() {
    local file=$1
    local key=$2
    local expected=$3

    if grep -q "${key}=${expected}" "$file"; then
        echo -e "   ${GREEN}✅${NC} $file: $key=$expected"
        return 0
    else
        echo -e "   ${RED}❌${NC} $file: $key not set to $expected"
        return 1
    fi
}

# Check all env files
check_config "envs/development.env" "QUOTES_MAX_SYMBOLS" "200"
check_config "envs/development.env" "MARKET_BREADTH_ENABLED" "true"
check_config "envs/staging.env" "QUOTES_MAX_SYMBOLS" "200"
check_config "envs/staging.env" "MARKET_BREADTH_ENABLED" "true"
check_config "envs/production.env" "QUOTES_MAX_SYMBOLS" "200"
check_config "envs/production.env" "MARKET_BREADTH_ENABLED" "true"

echo ""

# 2. Check new files exist
echo "2️⃣  Checking new files..."

check_file() {
    local file=$1
    if [ -f "$file" ]; then
        echo -e "   ${GREEN}✅${NC} $file exists"
        return 0
    else
        echo -e "   ${RED}❌${NC} $file missing"
        return 1
    fi
}

check_file "src/common/__init__.py"
check_file "src/common/constants.py"
check_file "src/services/market_breadth_service.py"
check_file "docs/integration/bayesian-engine-gap-analysis.md"
check_file "docs/integration/bayesian-implementation-plan.md"
check_file "docs/integration/bayesian-phase1-phase2-complete.md"

echo ""

# 3. Check Python syntax
echo "3️⃣  Checking Python syntax..."

check_syntax() {
    local file=$1
    if python3 -m py_compile "$file" 2>/dev/null; then
        echo -e "   ${GREEN}✅${NC} $file: Valid Python syntax"
        return 0
    else
        echo -e "   ${RED}❌${NC} $file: Syntax errors"
        return 1
    fi
}

check_syntax "src/common/constants.py"
check_syntax "src/services/market_breadth_service.py"
check_syntax "src/config/settings.py"

echo ""

# 4. Check imports
echo "4️⃣  Checking critical imports..."

check_import() {
    local file=$1
    local import_line=$2

    if grep -q "$import_line" "$file"; then
        echo -e "   ${GREEN}✅${NC} $file: Has required import"
        return 0
    else
        echo -e "   ${RED}❌${NC} $file: Missing import: $import_line"
        return 1
    fi
}

check_import "src/services/market_context_service.py" "from services.market_breadth_service import MarketBreadthService"
check_import "src/services/market_breadth_service.py" "from common.constants import NIFTY_50_CONSTITUENTS"

echo ""

# 5. Check constants
echo "5️⃣  Checking Nifty 50 constants..."

NIFTY_COUNT=$(grep -c "\"" src/common/constants.py | head -1 || echo "0")
if [ "$NIFTY_COUNT" -ge 50 ]; then
    echo -e "   ${GREEN}✅${NC} NIFTY_50_CONSTITUENTS has ~50 symbols"
else
    echo -e "   ${YELLOW}⚠️${NC}  NIFTY_50_CONSTITUENTS may have fewer than 50 symbols"
fi

echo ""

# 6. Check CHANGELOG
echo "6️⃣  Checking CHANGELOG..."

if grep -q "Market Breadth" CHANGELOG.md; then
    echo -e "   ${GREEN}✅${NC} CHANGELOG.md updated with market breadth changes"
else
    echo -e "   ${RED}❌${NC} CHANGELOG.md not updated"
fi

echo ""

# 7. Test settings loading (if Python environment is available)
echo "7️⃣  Testing settings loading..."

if command -v python3 &> /dev/null; then
    SETTINGS_TEST=$(python3 -c "
import sys
sys.path.insert(0, 'src')
try:
    from config.settings import get_settings
    s = get_settings()
    assert s.service.quotes_max_symbols == 200, f'quotes_max_symbols is {s.service.quotes_max_symbols}, expected 200'
    assert s.service.market_breadth_enabled == True, 'market_breadth_enabled is not True'
    print('SUCCESS')
except Exception as e:
    print(f'ERROR: {e}')
    sys.exit(1)
" 2>&1)

    if echo "$SETTINGS_TEST" | grep -q "SUCCESS"; then
        echo -e "   ${GREEN}✅${NC} Settings load correctly (quotes_max_symbols=200, market_breadth_enabled=True)"
    else
        echo -e "   ${RED}❌${NC} Settings loading failed:"
        echo "   $SETTINGS_TEST"
    fi
else
    echo -e "   ${YELLOW}⚠️${NC}  Python3 not available, skipping settings test"
fi

echo ""
echo "================================================"
echo "Verification Complete!"
echo "================================================"
echo ""
echo "📝 Next Steps:"
echo "   1. Run the service: python src/main.py (or scripts/run-dev.sh)"
echo "   2. Test market context endpoint:"
echo "      curl -X POST http://localhost:8079/api/analysis/context \\"
echo "        -H 'Content-Type: application/json' \\"
echo "        -d '{\"include_global_data\": true}' | jq '.market_context.indian_data'"
echo "   3. Verify breadth data is populated with real values"
echo ""
echo "📚 Documentation:"
echo "   - Gap Analysis: docs/integration/bayesian-engine-gap-analysis.md"
echo "   - Implementation Plan: docs/integration/bayesian-implementation-plan.md"
echo "   - Completion Summary: docs/integration/bayesian-phase1-phase2-complete.md"
echo ""
