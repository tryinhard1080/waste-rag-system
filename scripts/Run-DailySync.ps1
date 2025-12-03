# Daily Email Warehouse Sync Script
# This script runs daily to:
# 1. Export today's emails from Outlook
# 2. Convert to Gemini format
# 3. Upload to Gemini RAG

param(
    [string]$LogFile = "$PSScriptRoot\..\logs\daily-sync.log"
)

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Write-Host $logMessage
    Add-Content -Path $LogFile -Value $logMessage
}

# Create log directory if it doesn't exist
$logDir = Split-Path -Parent $LogFile
if (!(Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

Write-Log "================================================================================  "
Write-Log "Starting Daily Email Warehouse Sync"
Write-Log "================================================================================"

# Step 1: Export today's emails
Write-Log "Step 1: Exporting today's emails from Outlook..."
try {
    & "$PSScriptRoot\Export-DailyEmails.ps1" 2>&1 | ForEach-Object {
        Write-Log $_
    }
    Write-Log "✓ Email export completed"
} catch {
    Write-Log "✗ Email export failed: $_"
    exit 1
}

# Step 2: Convert to Gemini format
Write-Log ""
Write-Log "Step 2: Converting emails to Gemini markdown format..."
try {
    $today = Get-Date -Format "yyyy-MM-dd"
    $pythonCmd = "python `"$PSScriptRoot\convert_to_gemini_format.py`" --start-date $today --end-date $today --batch-by month"
    $output = cmd /c $pythonCmd 2>&1
    $output | ForEach-Object { Write-Log $_ }
    Write-Log "✓ Conversion completed"
} catch {
    Write-Log "✗ Conversion failed: $_"
    exit 1
}

# Step 3: Upload to Gemini RAG
Write-Log ""
Write-Log "Step 3: Uploading to Gemini RAG..."
try {
    # Check if API key is set in environment
    if (-not $env:GOOGLE_API_KEY) {
        Write-Log "✗ ERROR: GOOGLE_API_KEY environment variable not set"
        Write-Log "Please set it with: set GOOGLE_API_KEY=your_key"
        exit 1
    }

    $pythonCmd = "python `"$PSScriptRoot\setup_gemini_rag.py`" --upload-all"
    $output = cmd /c $pythonCmd 2>&1
    $output | ForEach-Object { Write-Log $_ }
    Write-Log "✓ Upload completed"
} catch {
    Write-Log "✗ Upload failed: $_"
    exit 1
}

Write-Log ""
Write-Log "================================================================================"
Write-Log "Daily Sync Completed Successfully"
Write-Log "================================================================================"
