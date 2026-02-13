#!/bin/bash
# Push to GitHub - Execute this script
# =====================================

set -e

echo "🚀 Pushing Kite Services to GitHub..."
echo ""

# Check if remote exists
if ! git remote get-url origin > /dev/null 2>&1; then
    echo "❌ No remote configured!"
    echo "Run: git remote add origin https://github.com/YOUR_USERNAME/kite-services.git"
    exit 1
fi

REMOTE_URL=$(git remote get-url origin)
echo "📍 Remote: $REMOTE_URL"
echo ""

# Push main branch
echo "📤 Pushing main branch..."
git push -u origin main

# Push develop branch
echo ""
echo "📤 Pushing develop branch..."
git push -u origin develop

echo ""
echo "✅ Successfully pushed to GitHub!"
echo ""
echo "📋 Next steps:"
echo "1. Go to: https://github.com/$(echo $REMOTE_URL | sed 's/.*github.com[:/]\(.*\)\.git/\1/')"
echo "2. Go to: Settings → Secrets → Actions"
echo "3. Add secrets:"
echo "   - KITE_API_KEY"
echo "   - KITE_ACCESS_TOKEN"
echo "   - PROD_SSH_PRIVATE_KEY"
echo ""
echo "4. Protect branches (Settings → Branches):"
echo "   - main: Require PR, require approvals, require status checks"
echo "   - develop: Require PR, require status checks"
echo ""
echo "5. Check Actions tab to see CI/CD pipeline!"
echo ""
echo "🎉 Done! Your code is on GitHub with CI/CD pipeline ready!"
