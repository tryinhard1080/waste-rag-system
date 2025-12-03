# Setup Daily Email Warehouse Sync in Task Scheduler
# Run as Administrator

param(
    [string]$RunTime = "08:00",  # Daily run time
    [switch]$RunOnWeekdaysOnly = $false
)

# Check if running as administrator
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (!$isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator" -ForegroundColor Red
    Write-Host "Please right-click PowerShell and select 'Run as Administrator'"
    exit 1
}

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Email Warehouse - Daily Sync Setup" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Get script path
$scriptPath = "$PSScriptRoot\Run-DailySync.ps1"

if (!(Test-Path $scriptPath)) {
    Write-Host "ERROR: Run-DailySync.ps1 not found at $scriptPath" -ForegroundColor Red
    exit 1
}

Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Task Name:        Email Warehouse Daily Sync"
Write-Host "  Run Time:         $RunTime daily"
Write-Host "  Weekdays Only:    $RunOnWeekdaysOnly"
Write-Host "  Script:           $scriptPath"
Write-Host ""

# Ask for confirmation
$confirm = Read-Host "Create scheduled task? (Y/N)"
if ($confirm -ne 'Y' -and $confirm -ne 'y') {
    Write-Host "Setup cancelled" -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "Creating scheduled task..." -ForegroundColor Green

try {
    # Create the task action
    $action = New-ScheduledTaskAction `
        -Execute 'PowerShell.exe' `
        -Argument "-ExecutionPolicy Bypass -File `"$scriptPath`""

    # Create the trigger
    $triggerParams = @{
        Daily = $true
        At = $RunTime
    }

    if ($RunOnWeekdaysOnly) {
        $triggerParams['DaysOfWeek'] = @('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday')
    }

    $trigger = New-ScheduledTaskTrigger @triggerParams

    # Create task settings
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RunOnlyIfNetworkAvailable:$false

    # Register the task
    $taskName = "Email Warehouse Daily Sync"

    # Remove existing task if it exists
    $existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($existingTask) {
        Write-Host "Removing existing task..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    }

    # Create new task
    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Description "Daily sync of emails to Gemini RAG system" `
        -RunLevel Highest

    Write-Host ""
    Write-Host "✓ Scheduled task created successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "The task will run daily at $RunTime" -ForegroundColor Green
    Write-Host "Logs will be written to: logs/daily-sync.log" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "To manage the task:" -ForegroundColor Yellow
    Write-Host "  1. Open Task Scheduler (taskschd.msc)"
    Write-Host "  2. Look for 'Email Warehouse Daily Sync'"
    Write-Host ""
    Write-Host "To test the task now:" -ForegroundColor Yellow
    Write-Host "  Run: .\Run-DailySync.ps1"
    Write-Host ""

} catch {
    Write-Host ""
    Write-Host "✗ ERROR: Failed to create scheduled task" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
