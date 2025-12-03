<#
.SYNOPSIS
    Set up Windows scheduled task for automated daily email export.

.DESCRIPTION
    Creates a Windows Task Scheduler task that runs daily to:
    1. Export emails from Outlook
    2. Aggregate threads
    3. Generate daily summary

.PARAMETER TaskName
    Name of the scheduled task (default: EmailWarehouseExport)

.PARAMETER RunTime
    Time to run the task daily in 24-hour format HH:MM (default: 18:00)

.PARAMETER RunOnWeekdaysOnly
    If specified, only run on weekdays (Monday-Friday)

.EXAMPLE
    .\Setup-ScheduledTask.ps1
    Creates task with default settings (runs daily at 6 PM)

.EXAMPLE
    .\Setup-ScheduledTask.ps1 -RunTime "08:00" -RunOnWeekdaysOnly
    Creates task that runs at 8 AM on weekdays only
#>

param(
    [Parameter(Mandatory=$false)]
    [string]$TaskName = "EmailWarehouseExport",

    [Parameter(Mandatory=$false)]
    [string]$RunTime = "18:00",

    [Parameter(Mandatory=$false)]
    [switch]$RunOnWeekdaysOnly = $false
)

# Ensure running as Administrator
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator" -ForegroundColor Red
    Write-Host "Please right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

Write-Host "Email Warehouse - Scheduled Task Setup" -ForegroundColor Cyan
Write-Host "=" * 60

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Write-Host "`nProject Root: $ProjectRoot"
Write-Host "Task Name: $TaskName"
Write-Host "Run Time: $RunTime"
Write-Host "Weekdays Only: $RunOnWeekdaysOnly"

# Load configuration for timezone
$ConfigPath = Join-Path $ProjectRoot "config\settings.json"
$timezone = "Central Standard Time"  # Default

if (Test-Path $ConfigPath) {
    try {
        $config = Get-Content $ConfigPath -Raw | ConvertFrom-Json
        if ($config.schedule.timezone) {
            # Convert timezone name (e.g., America/Chicago to Central Standard Time)
            $timezoneMap = @{
                "America/Chicago" = "Central Standard Time"
                "America/New_York" = "Eastern Standard Time"
                "America/Los_Angeles" = "Pacific Standard Time"
                "America/Denver" = "Mountain Standard Time"
            }
            if ($timezoneMap.ContainsKey($config.schedule.timezone)) {
                $timezone = $timezoneMap[$config.schedule.timezone]
            }
        }
    } catch {
        Write-Host "Warning: Could not read timezone from config" -ForegroundColor Yellow
    }
}

# Create wrapper script that runs all three components
$WrapperScriptPath = Join-Path $ScriptDir "Run-DailyExport.ps1"

$WrapperScript = @"
<#
.SYNOPSIS
    Automated daily email export, aggregation, and summarization.
    This script is executed by Windows Task Scheduler.
#>

`$ErrorActionPreference = "Continue"
`$ScriptDir = Split-Path -Parent `$MyInvocation.MyCommand.Path
`$LogPath = Join-Path (Split-Path -Parent `$ScriptDir) "logs\scheduled-export.log"

# Logging function
function Write-Log {
    param([string]`$Message)
    `$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    `$logMessage = "[`$timestamp] `$Message"
    Write-Host `$logMessage
    Add-Content -Path `$LogPath -Value `$logMessage
}

Write-Log "=========================================="
Write-Log "Starting automated email warehouse export"
Write-Log "=========================================="

# Step 1: Export emails from Outlook
Write-Log "Step 1: Exporting emails from Outlook..."
try {
    `$exportScript = Join-Path `$ScriptDir "Export-DailyEmails.ps1"
    & `$exportScript
    Write-Log "Email export completed successfully"
} catch {
    Write-Log "ERROR in email export: `$_"
}

# Step 2: Aggregate threads
Write-Log "`nStep 2: Aggregating threads..."
try {
    `$pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
    if (`$pythonPath) {
        `$aggregateScript = Join-Path `$ScriptDir "aggregate_threads.py"
        & python `$aggregateScript
        Write-Log "Thread aggregation completed successfully"
    } else {
        Write-Log "WARNING: Python not found. Skipping thread aggregation."
    }
} catch {
    Write-Log "ERROR in thread aggregation: `$_"
}

# Step 3: Generate summary
Write-Log "`nStep 3: Generating daily summary..."
try {
    `$pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
    if (`$pythonPath) {
        `$summaryScript = Join-Path `$ScriptDir "generate_summary.py"
        & python `$summaryScript
        Write-Log "Summary generation completed successfully"
    } else {
        Write-Log "WARNING: Python not found. Skipping summary generation."
    }
} catch {
    Write-Log "ERROR in summary generation: `$_"
}

Write-Log "`n=========================================="
Write-Log "Automated export completed"
Write-Log "=========================================="
"@

# Save wrapper script
Set-Content -Path $WrapperScriptPath -Value $WrapperScript
Write-Host "`nWrapper script created: $WrapperScriptPath" -ForegroundColor Green

# Remove existing task if it exists
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "`nRemoving existing task '$TaskName'..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Parse run time
$timeParts = $RunTime -split ':'
$hour = [int]$timeParts[0]
$minute = [int]$timeParts[1]

# Create scheduled task action
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$WrapperScriptPath`"" `
    -WorkingDirectory $ScriptDir

# Create trigger
if ($RunOnWeekdaysOnly) {
    # Create triggers for Monday through Friday
    $triggers = @()
    foreach ($day in @('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday')) {
        $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek $day -At ([DateTime]::Today.AddHours($hour).AddMinutes($minute))
        $triggers += $trigger
    }
    $trigger = $triggers  # Use first trigger for registration, then add others
} else {
    # Daily trigger
    $trigger = New-ScheduledTaskTrigger -Daily -At ([DateTime]::Today.AddHours($hour).AddMinutes($minute))
}

# Create settings
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable:$false

# Create principal (run as current user)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

# Register scheduled task
Write-Host "`nCreating scheduled task..." -ForegroundColor Cyan

try {
    if ($RunOnWeekdaysOnly -and $triggers.Count -gt 1) {
        # Register with first trigger
        $task = Register-ScheduledTask -TaskName $TaskName `
            -Action $action `
            -Trigger $triggers[0] `
            -Settings $settings `
            -Principal $principal `
            -Description "Automated email export from Outlook to email warehouse"

        # Add additional triggers
        for ($i = 1; $i -lt $triggers.Count; $i++) {
            $task.Triggers += $triggers[$i]
        }
        $task | Set-ScheduledTask
    } else {
        $task = Register-ScheduledTask -TaskName $TaskName `
            -Action $action `
            -Trigger $trigger `
            -Settings $settings `
            -Principal $principal `
            -Description "Automated email export from Outlook to email warehouse"
    }

    Write-Host "`nScheduled task created successfully!" -ForegroundColor Green
    Write-Host "`nTask Details:" -ForegroundColor Cyan
    Write-Host "  Name: $TaskName"
    Write-Host "  Run Time: $RunTime (daily)"
    if ($RunOnWeekdaysOnly) {
        Write-Host "  Days: Monday through Friday only"
    } else {
        Write-Host "  Days: Every day"
    }
    Write-Host "  Script: $WrapperScriptPath"
    Write-Host "  Logs: $ProjectRoot\logs\scheduled-export.log"

    Write-Host "`nNext Steps:" -ForegroundColor Yellow
    Write-Host "1. The task will run automatically at the scheduled time"
    Write-Host "2. You can test it now by running: Start-ScheduledTask -TaskName '$TaskName'"
    Write-Host "3. View task in Task Scheduler: taskschd.msc"
    Write-Host "4. Check logs in: $ProjectRoot\logs\"

} catch {
    Write-Host "`nERROR: Failed to create scheduled task" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

# Offer to run test
Write-Host "`n" + ("=" * 60)
$runTest = Read-Host "Would you like to test the task now? (Y/N)"

if ($runTest -eq 'Y' -or $runTest -eq 'y') {
    Write-Host "`nStarting test run..." -ForegroundColor Cyan
    Start-ScheduledTask -TaskName $TaskName
    Write-Host "Task started. Check the logs folder for results." -ForegroundColor Green
    Write-Host "Log file: $ProjectRoot\logs\scheduled-export.log"
}

Write-Host "`nSetup completed successfully!" -ForegroundColor Green
Write-Host "=" * 60
