# GitHub Repository Setup Script (PowerShell)
# Run this after creating the repository on GitHub

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "GitHub Repository Setup" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Check if git is initialized
if (-not (Test-Path .git)) {
    Write-Host "Error: Not a git repository" -ForegroundColor Red
    exit 1
}

# Instructions
Write-Host "First, create a repository on GitHub:" -ForegroundColor Yellow
Write-Host "  1. Go to https://github.com/new"
Write-Host "  2. Repository name: waste-rag-system"
Write-Host "  3. Description: Production-ready RAG system for waste management using Google Gemini File API"
Write-Host "  4. Choose Private or Public"
Write-Host "  5. DO NOT initialize with README, .gitignore, or license"
Write-Host "  6. Click 'Create repository'"
Write-Host ""

# Get repository URL
$repoUrl = Read-Host "Enter your GitHub repository URL (e.g., https://github.com/username/waste-rag-system.git)"

if ([string]::IsNullOrWhiteSpace($repoUrl)) {
    Write-Host "Error: Repository URL is required" -ForegroundColor Red
    exit 1
}

# Add remote
Write-Host ""
Write-Host "Adding remote origin..." -ForegroundColor Yellow
git remote add origin $repoUrl 2>$null
if ($LASTEXITCODE -ne 0) {
    git remote set-url origin $repoUrl
}

# Verify remote
Write-Host "Remote configured:" -ForegroundColor Green
git remote -v

# Check branch name
$currentBranch = git branch --show-current
Write-Host ""
Write-Host "Current branch: $currentBranch" -ForegroundColor Cyan

# Push to GitHub
Write-Host ""
Write-Host "Pushing to GitHub..." -ForegroundColor Yellow
git push -u origin $currentBranch

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Success! Repository pushed to GitHub" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    $repoWebUrl = $repoUrl -replace '\.git$', ''
    Write-Host "  1. Visit your repository: $repoWebUrl"
    Write-Host "  2. Review the README.md"
    Write-Host "  3. Check the GitHub Actions workflows"
    Write-Host "  4. Consider adding collaborators"
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "❌ Push failed. Common issues:" -ForegroundColor Red
    Write-Host "  - Check your GitHub credentials"
    Write-Host "  - Ensure you have repository access"
    Write-Host "  - Verify repository URL is correct"
    Write-Host "  - Run: git config credential.helper store"
    Write-Host ""
}

Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
