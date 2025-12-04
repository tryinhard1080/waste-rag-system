# Sync Email Warehouse Data to GitHub
# This script commits and pushes email data to a private GitHub repository
# Run this after Run-DailySync.ps1 to make data available to all your apps

param(
    [string]$DataRepoPath = "$PSScriptRoot\..\warehouse",
    [string]$CommitMessage = "Auto-sync: $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
)

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Email Warehouse - Data Sync to GitHub" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if git is initialized
if (!(Test-Path "$DataRepoPath\.git")) {
    Write-Host "ERROR: Git not initialized in $DataRepoPath" -ForegroundColor Red
    Write-Host ""
    Write-Host "Initialize with:" -ForegroundColor Yellow
    Write-Host "  cd warehouse" -ForegroundColor Yellow
    Write-Host "  git init" -ForegroundColor Yellow
    Write-Host "  git remote add origin https://github.com/YOUR_USERNAME/email-warehouse-data.git" -ForegroundColor Yellow
    exit 1
}

# Navigate to data directory
Push-Location $DataRepoPath

try {
    # Check for changes
    $status = git status --porcelain

    if (!$status) {
        Write-Host "No changes to sync" -ForegroundColor Green
        Pop-Location
        exit 0
    }

    Write-Host "Changes detected. Syncing to GitHub..." -ForegroundColor Green
    Write-Host ""

    # Add all data files
    Write-Host "Adding files..." -ForegroundColor Cyan
    git add daily/*.json
    git add gemini/*.md
    git add threads/*.json 2>$null  # Optional
    git add summaries/*.md 2>$null  # Optional

    # Commit
    Write-Host "Creating commit..." -ForegroundColor Cyan
    git commit -m "$CommitMessage"

    # Push
    Write-Host "Pushing to GitHub..." -ForegroundColor Cyan
    git push origin master 2>&1

    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✓ Data successfully synced to GitHub!" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "✗ Push failed. Check your credentials and remote URL" -ForegroundColor Red
        exit 1
    }

} catch {
    Write-Host ""
    Write-Host "✗ Error: $_" -ForegroundColor Red
    exit 1
} finally {
    Pop-Location
}

Write-Host ""
Write-Host "Data is now available at:" -ForegroundColor Cyan
Write-Host "  https://github.com/YOUR_USERNAME/email-warehouse-data" -ForegroundColor Yellow
Write-Host ""
