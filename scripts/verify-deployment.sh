#!/bin/bash

# HERMES Deployment Verification Script
# This script helps verify that the deployment configuration is correct

set -e

echo "🔍 HERMES Deployment Configuration Verification"
echo "================================================"

# Check if we're in the right directory
if [ ! -f "frontend/package.json" ] || [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Please run this script from the HERMES repository root directory"
    exit 1
fi

echo "✅ Repository structure verified"

# Check frontend dependencies
echo ""
echo "📦 Checking frontend dependencies..."
cd frontend
if npm list --depth=0 > /dev/null 2>&1; then
    echo "✅ Frontend dependencies installed"
else
    echo "⚠️  Installing frontend dependencies..."
    npm install
fi

# Test frontend build
echo ""
echo "🏗️  Testing frontend build..."
if npm run build > /dev/null 2>&1; then
    echo "✅ Frontend builds successfully"
    
    # Check if deployment info would be created
    if [ -n "$VITE_BACKEND_URL" ]; then
        echo "✅ Backend URL configured: $VITE_BACKEND_URL"
    else
        echo "ℹ️  No backend URL configured (demo mode will be used)"
    fi
else
    echo "❌ Frontend build failed"
    exit 1
fi

cd ..

# Check for deployment files
echo ""
echo "📋 Checking deployment configuration files..."

files=("render.yaml" "railway.toml" "docs/deployment.md" ".env.github-pages.example")
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file exists"
    else
        echo "❌ Missing: $file"
    fi
done

# Check GitHub Actions workflow
if [ -f ".github/workflows/deploy-pages.yml" ]; then
    echo "✅ GitHub Pages deployment workflow configured"
else
    echo "❌ Missing GitHub Pages workflow"
fi

# Check environment variable configuration
echo ""
echo "🔧 Environment Configuration Status:"
echo "   VITE_BACKEND_URL: ${VITE_BACKEND_URL:-'Not set (demo mode)'}"
echo "   VITE_BACKEND_WS_URL: ${VITE_BACKEND_WS_URL:-'Not set (demo mode)'}"
echo "   VITE_ENVIRONMENT: ${VITE_ENVIRONMENT:-'development'}"

echo ""
echo "🚀 Next Steps:"
echo "1. Deploy backend using: 'Deploy to Render' button in README"
echo "2. Set repository secrets in GitHub for your backend URL"
echo "3. Push changes to trigger GitHub Pages deployment"
echo "4. Visit your GitHub Pages URL to test full functionality"

echo ""
echo "📚 For detailed instructions, see:"
echo "   - README.md (Quick start)"
echo "   - docs/deployment.md (Complete guide)"
echo "   - .env.github-pages.example (Environment variables)"

echo ""
echo "✅ Deployment verification complete!"