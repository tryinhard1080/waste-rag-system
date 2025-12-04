# Initialize Data Repository for GitHub
# This script sets up a separate git repository in the warehouse folder
# for syncing email data to GitHub

param(
    [Parameter(Mandatory=$true)]
    [string]$GitHubRepoUrl  # e.g., https://github.com/tryinhard1080/email-warehouse-data.git
)

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Initialize Email Warehouse Data Repository" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

$warehousePath = "$PSScriptRoot\..\warehouse"

# Check if warehouse directory exists
if (!(Test-Path $warehousePath)) {
    Write-Host "ERROR: Warehouse directory not found at $warehousePath" -ForegroundColor Red
    exit 1
}

# Navigate to warehouse directory
Push-Location $warehousePath

try {
    # Check if already initialized
    if (Test-Path ".git") {
        Write-Host "Git already initialized in warehouse directory" -ForegroundColor Yellow
        Write-Host "Remote URL: $(git remote get-url origin 2>$null)" -ForegroundColor Yellow
        Write-Host ""
        $confirm = Read-Host "Reinitialize? This will remove existing git history (y/N)"
        if ($confirm -ne 'y' -and $confirm -ne 'Y') {
            Write-Host "Cancelled" -ForegroundColor Yellow
            Pop-Location
            exit 0
        }
        Remove-Item -Recurse -Force .git
    }

    # Initialize git
    Write-Host "Initializing git repository..." -ForegroundColor Green
    git init

    # Create .gitignore for the data repo
    Write-Host "Creating .gitignore..." -ForegroundColor Green
    @"
# Keep all email data
!daily/*.json
!gemini/*.md
!threads/*.json
!summaries/*.md

# Ignore OS files
.DS_Store
Thumbs.db
desktop.ini

# Keep structure
!.gitkeep
"@ | Out-File -FilePath ".gitignore" -Encoding UTF8

    # Create .gitkeep files to preserve directory structure
    Write-Host "Creating directory structure..." -ForegroundColor Green
    $directories = @('daily', 'gemini', 'threads', 'summaries')
    foreach ($dir in $directories) {
        if (!(Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
        New-Item -ItemType File -Path "$dir\.gitkeep" -Force | Out-Null
    }

    # Add remote
    Write-Host "Adding remote repository..." -ForegroundColor Green
    git remote add origin $GitHubRepoUrl

    # Initial commit
    Write-Host "Creating initial commit..." -ForegroundColor Green
    git add .
    git commit -m "Initial commit: Email warehouse data repository

This repository contains email data extracted from Outlook Desktop.
Structure:
- daily/: Daily email exports (JSON)
- gemini/: Gemini RAG markdown batches
- threads/: Email thread aggregations
- summaries/: Daily email summaries

Generated with Email Warehouse RAG System"

    # Try to push
    Write-Host ""
    Write-Host "Pushing to GitHub..." -ForegroundColor Green
    Write-Host "You may be prompted for credentials..." -ForegroundColor Yellow
    Write-Host ""

    git branch -M master
    git push -u origin master

    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "================================================================================" -ForegroundColor Green
        Write-Host "✓ Data repository initialized successfully!" -ForegroundColor Green
        Write-Host "================================================================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "Repository URL: $GitHubRepoUrl" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor Yellow
        Write-Host "  1. Verify data is on GitHub: ${GitHubRepoUrl}" -ForegroundColor White
        Write-Host "  2. Set up automated sync in Task Scheduler" -ForegroundColor White
        Write-Host "  3. Access data from your apps (see ACCESS_DATA_FROM_APPS.md)" -ForegroundColor White
        Write-Host ""
    } else {
        Write-Host ""
        Write-Host "✗ Push failed" -ForegroundColor Red
        Write-Host ""
        Write-Host "Common issues:" -ForegroundColor Yellow
        Write-Host "  1. Repository doesn't exist on GitHub - create it first at https://github.com/new" -ForegroundColor White
        Write-Host "  2. Authentication failed - you may need to set up a personal access token" -ForegroundColor White
        Write-Host "     See: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token" -ForegroundColor White
        Write-Host ""
    }

} catch {
    Write-Host ""
    Write-Host "✗ Error: $_" -ForegroundColor Red
    exit 1
} finally {
    Pop-Location
}
