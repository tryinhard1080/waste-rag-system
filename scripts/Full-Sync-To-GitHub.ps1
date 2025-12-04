# Full Email Warehouse Sync to GitHub
# This script does EVERYTHING:
# 1. Converts all JSON files to Gemini markdown format
# 2. Uploads to Gemini RAG
# 3. Initializes GitHub data repository
# 4. Commits and pushes both JSON and markdown files to GitHub

param(
    [Parameter(Mandatory=$false)]
    [string]$GitHubRepoUrl = "",
    [switch]$SkipRAGUpload = $false
)

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "FULL Email Warehouse Sync to GitHub" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if we need GitHub repo URL
$warehousePath = "$PSScriptRoot\..\warehouse"
$needsInit = !(Test-Path "$warehousePath\.git")

if ($needsInit -and !$GitHubRepoUrl) {
    Write-Host "ERROR: GitHub repository URL required for first-time setup" -ForegroundColor Red
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "  .\Full-Sync-To-GitHub.ps1 -GitHubRepoUrl 'https://github.com/YOUR_USERNAME/email-warehouse-data.git'" -ForegroundColor White
    Write-Host ""
    Write-Host "Or create the repo first at: https://github.com/new" -ForegroundColor Yellow
    exit 1
}

# Count JSON files
$jsonFiles = Get-ChildItem "$warehousePath\daily\*.json"
$jsonCount = $jsonFiles.Count

Write-Host "Found $jsonCount JSON email files" -ForegroundColor Green
Write-Host "Date range: $($jsonFiles[0].BaseName) to $($jsonFiles[-1].BaseName)" -ForegroundColor Green
Write-Host ""

# Step 1: Convert all to Gemini format
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Step 1: Converting all emails to Gemini markdown format" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

try {
    Push-Location "$PSScriptRoot"

    # Get date range from files
    $startDate = $jsonFiles[0].BaseName
    $endDate = $jsonFiles[-1].BaseName

    Write-Host "Converting emails from $startDate to $endDate..." -ForegroundColor Yellow
    Write-Host ""

    $pythonCmd = "python convert_to_gemini_format.py --start-date $startDate --end-date $endDate --batch-by month"
    Write-Host "Running: $pythonCmd" -ForegroundColor Cyan
    Write-Host ""

    $output = cmd /c $pythonCmd 2>&1
    $output | ForEach-Object { Write-Host $_ }

    Write-Host ""
    Write-Host "✓ Conversion completed" -ForegroundColor Green

    Pop-Location
} catch {
    Write-Host "✗ Conversion failed: $_" -ForegroundColor Red
    Pop-Location
    exit 1
}

# Step 2: Upload to Gemini RAG (optional)
if (!$SkipRAGUpload) {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "Step 2: Uploading to Gemini RAG" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host ""

    if (-not $env:GOOGLE_API_KEY) {
        Write-Host "WARNING: GOOGLE_API_KEY not set. Skipping RAG upload." -ForegroundColor Yellow
        Write-Host "Set it with: set GOOGLE_API_KEY=your_key" -ForegroundColor Yellow
        Write-Host ""
    } else {
        try {
            Push-Location "$PSScriptRoot"

            Write-Host "Uploading all batches to Gemini..." -ForegroundColor Yellow
            Write-Host ""

            $pythonCmd = "python setup_gemini_rag.py --upload-all"
            Write-Host "Running: $pythonCmd" -ForegroundColor Cyan
            Write-Host ""

            $output = cmd /c $pythonCmd 2>&1
            $output | ForEach-Object { Write-Host $_ }

            Write-Host ""
            Write-Host "✓ RAG upload completed" -ForegroundColor Green

            Pop-Location
        } catch {
            Write-Host "✗ RAG upload failed: $_" -ForegroundColor Red
            Write-Host "Continuing with GitHub sync..." -ForegroundColor Yellow
            Pop-Location
        }
    }
}

# Step 3: Initialize GitHub repo (if needed)
if ($needsInit) {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "Step 3: Initializing GitHub Data Repository" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host ""

    try {
        & "$PSScriptRoot\Initialize-DataRepo.ps1" -GitHubRepoUrl $GitHubRepoUrl

        if ($LASTEXITCODE -ne 0) {
            Write-Host "✗ GitHub initialization failed" -ForegroundColor Red
            exit 1
        }
    } catch {
        Write-Host "✗ GitHub initialization failed: $_" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "Step 3: Syncing to GitHub (repo already initialized)" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host ""

    try {
        & "$PSScriptRoot\Sync-DataToGitHub.ps1" -CommitMessage "Full sync: All 2025 emails (JSON + Markdown)"

        if ($LASTEXITCODE -ne 0) {
            Write-Host "✗ GitHub sync failed" -ForegroundColor Red
            exit 1
        }
    } catch {
        Write-Host "✗ GitHub sync failed: $_" -ForegroundColor Red
        exit 1
    }
}

# Summary
Write-Host ""
Write-Host "================================================================================" -ForegroundColor Green
Write-Host "✓ FULL SYNC COMPLETED!" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  • JSON files:      $jsonCount files ($('{0:N2}' -f (($jsonFiles | Measure-Object -Property Length -Sum).Sum / 1MB)) MB)" -ForegroundColor White
Write-Host "  • Date range:      $startDate to $endDate" -ForegroundColor White
Write-Host "  • Markdown batches: $(Get-ChildItem "$warehousePath\gemini\*.md" | Measure-Object).Count files" -ForegroundColor White
Write-Host "  • RAG upload:      $(if ($SkipRAGUpload -or !$env:GOOGLE_API_KEY) { 'Skipped' } else { 'Completed' })" -ForegroundColor White
Write-Host "  • GitHub sync:     Completed" -ForegroundColor White
Write-Host ""
Write-Host "Your data is now available:" -ForegroundColor Yellow
Write-Host "  • GitHub:     $(if ($GitHubRepoUrl) { $GitHubRepoUrl } else { 'Already configured' })" -ForegroundColor White
Write-Host "  • Local JSON: $warehousePath\daily\" -ForegroundColor White
Write-Host "  • Local MD:   $warehousePath\gemini\" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Verify data on GitHub" -ForegroundColor White
Write-Host "  2. Test access from your apps (see ACCESS_DATA_FROM_APPS.md)" -ForegroundColor White
Write-Host "  3. Set up automated daily sync (Setup-DailySync.ps1)" -ForegroundColor White
Write-Host ""
