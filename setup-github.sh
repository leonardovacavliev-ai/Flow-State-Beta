#!/bin/bash

# ESP Loyalty Helper - GitHub Setup Script

echo "🚀 ESP Loyalty Helper - GitHub Setup"
echo "===================================="
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install git first:"
    echo "   brew install git"
    exit 1
fi

# Check if already initialized
if [ -d .git ]; then
    echo "⚠️  Git repository already initialized"
    echo "   Current remote:"
    git remote -v
    echo ""
    read -p "Do you want to continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "📦 Initializing git repository..."
    git init
    echo "✅ Git initialized"
fi

echo ""
echo "📝 Staging files..."
git add .

echo ""
echo "📋 Files to be committed:"
git status --short

echo ""
read -p "Proceed with commit? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Aborted"
    exit 1
fi

echo ""
echo "💾 Creating initial commit..."
git commit -m "Initial commit: ESP Loyalty Helper App

- Flask backend with AI integration (Gemini/Claude)
- Vector database (ChromaDB) for RAG
- Analytics system (SQLite)
- Admin panel for ESP management
- Web crawler for documentation
- Frontend with Yotpo branding"

echo ""
echo "✅ Commit created successfully!"
echo ""
echo "📤 Next Steps:"
echo "-------------"
echo ""
echo "1. Create a new repository on GitHub:"
echo "   👉 https://github.com/new"
echo ""
echo "2. Repository settings:"
echo "   - Name: esp-loyalty-helper (or your choice)"
echo "   - Visibility: Private (recommended)"
echo "   - DON'T initialize with README/gitignore/license"
echo ""
echo "3. After creating the repository, run these commands:"
echo "   (Replace YOUR_USERNAME with your GitHub username)"
echo ""
echo "   git remote add origin https://github.com/YOUR_USERNAME/esp-loyalty-helper.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "4. For deployment options, see DEPLOYMENT.md"
echo ""
echo "🎉 Setup complete!"
