#!/bin/bash
# Prepare Git Repository for Push
# ================================

set -e

echo "🔧 Preparing Git repository for push..."

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📦 Initializing Git repository..."
    git init
    git branch -M main
fi

# Add all files
echo "📝 Staging files..."
git add .

# Check if there are changes
if git diff --staged --quiet; then
    echo "✅ No changes to commit"
else
    echo "💾 Creating commit..."
    git commit -m "feat: Complete CI/CD setup with production monitoring

- Add comprehensive CI/CD pipeline (GitHub Actions)
- Production deployment only from main/master branch
- Develop branch: image build + test stage
- Enhanced logging with request IDs and metrics
- Production monitoring endpoints (/health, /metrics)
- Poetry dependency management
- Comprehensive test suite
- Docker production deployment
- Git setup documentation"
    
    echo "✅ Commit created"
fi

# Show status
echo ""
echo "📊 Git Status:"
git status --short

echo ""
echo "🌿 Current branch:"
git branch

echo ""
echo "📋 Next steps:"
echo "1. Add remote repository:"
echo "   git remote add origin https://github.com/YOUR_USERNAME/kite-services.git"
echo ""
echo "2. Push to GitHub:"
echo "   git push -u origin main"
echo ""
echo "3. Create 'develop' branch:"
echo "   git checkout -b develop"
echo "   git push -u origin develop"
echo ""
echo "4. Set up GitHub Secrets (Settings → Secrets → Actions):"
echo "   - KITE_API_KEY"
echo "   - KITE_ACCESS_TOKEN"
echo "   - PROD_SSH_PRIVATE_KEY"
echo ""
echo "✅ Repository ready for push!"
