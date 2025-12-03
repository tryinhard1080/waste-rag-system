#!/bin/bash
#
# GitHub Repository Setup Script
# Run this after creating the repository on GitHub
#

echo "=================================="
echo "GitHub Repository Setup"
echo "=================================="
echo ""

# Check if git is initialized
if [ ! -d .git ]; then
    echo "Error: Not a git repository"
    exit 1
fi

# Get repository URL from user
echo "First, create a repository on GitHub:"
echo "  1. Go to https://github.com/new"
echo "  2. Repository name: waste-rag-system"
echo "  3. Description: Production-ready RAG system for waste management using Google Gemini File API"
echo "  4. Choose Private or Public"
echo "  5. DO NOT initialize with README, .gitignore, or license"
echo "  6. Click 'Create repository'"
echo ""
read -p "Enter your GitHub repository URL (e.g., https://github.com/username/waste-rag-system.git): " repo_url

if [ -z "$repo_url" ]; then
    echo "Error: Repository URL is required"
    exit 1
fi

# Add remote
echo ""
echo "Adding remote origin..."
git remote add origin "$repo_url" 2>/dev/null || git remote set-url origin "$repo_url"

# Verify remote
echo "Remote configured:"
git remote -v

# Push to GitHub
echo ""
echo "Pushing to GitHub..."
git push -u origin master

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Success! Repository pushed to GitHub"
    echo ""
    echo "Next steps:"
    echo "  1. Visit your repository: ${repo_url%.git}"
    echo "  2. Review the README.md"
    echo "  3. Check the GitHub Actions workflows"
    echo "  4. Consider adding collaborators"
    echo ""
else
    echo ""
    echo "❌ Push failed. Common issues:"
    echo "  - Check your GitHub credentials"
    echo "  - Ensure you have repository access"
    echo "  - Verify repository URL is correct"
    echo ""
fi
