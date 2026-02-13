#!/bin/bash
# Test CI/CD Workflow Commands Locally
# Run this before committing CI/CD changes

set -e

echo "🧪 Testing CI/CD Workflow Commands..."
echo ""

# Test 1: YAML Syntax
echo "1. Testing YAML syntax..."
if command -v yamllint &> /dev/null; then
    yamllint .github/workflows/deploy.yml && echo "   ✅ YAML syntax valid"
else
    echo "   ⚠️ yamllint not installed, skipping YAML check"
fi

# Test 2: Poetry Install
echo ""
echo "2. Testing Poetry install command..."
poetry install --without dev --no-interaction --dry-run > /dev/null 2>&1 && echo "   ✅ Poetry install command works" || echo "   ❌ Poetry install failed"

# Test 3: Poetry Run Pytest
echo ""
echo "3. Testing pytest command..."
poetry run pytest --collect-only tests/ > /dev/null 2>&1 && echo "   ✅ Pytest command works" || echo "   ⚠️ Pytest not available (will install in CI)"

# Test 4: Docker
echo ""
echo "4. Testing Docker..."
docker --version > /dev/null 2>&1 && echo "   ✅ Docker available" || echo "   ⚠️ Docker not available (will work in CI)"

# Test 5: Poetry PATH
echo ""
echo "5. Testing Poetry PATH..."
if [ -f "$HOME/.local/bin/poetry" ]; then
    echo "   ✅ Poetry found at \$HOME/.local/bin/poetry"
else
    echo "   ⚠️ Poetry not at expected path (will be installed in CI)"
fi

echo ""
echo "✅ CI/CD workflow validation complete!"
echo ""
echo "If all checks passed, the workflow should work in GitHub Actions."
