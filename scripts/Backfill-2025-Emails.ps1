<#
.SYNOPSIS
    Bulk export all emails from 2025 (or specified date range) in efficient chunks.

.DESCRIPTION
    Processes emails in date-based chunks to avoid memory issues. Uses the optimized
    Export-DailyEmails.ps1 with Restrict filtering for fast extraction. Supports
    resume capability by skipping already exported dates.

.PARAMETER StartDate
    Beginning of date range to backfill (default: 2025-01-01)

.PARAMETER EndDate
    End of date range to backfill (default: today)

.PARAMETER ChunkSize
    Number of days to process in each chunk (default: 7 for weekly batches)

.PARAMETER Folders
    Array of folder names to process (default: Inbox, Sent Items)

.PARAMETER SkipExisting
    Skip dates that already have JSON files exported (default: true)

.PARAMETER IncludeAttachments
    Whether to save attachment files to disk (default: false)

.EXAMPLE
    .\Backfill-2025-Emails.ps1
    Backfill all 2025 emails in weekly chunks

.EXAMPLE
    .\Backfill-2025-Emails.ps1 -StartDate "2025-01-01" -EndDate "2025-06-30" -ChunkSize 30
    Backfill first half of 2025 in monthly chunks

.EXAMPLE
    .\Backfill-2025-Emails.ps1 -SkipExisting:$false
    Re-export all dates even if files exist
#>

param(
    [Parameter(Mandatory=$false)]
    [DateTime]$StartDate = "2025-01-01",

    [Parameter(Mandatory=$false)]
    [DateTime]$EndDate = (Get-Date),

    [Parameter(Mandatory=$false)]
    [int]$ChunkSize = 7,

    [Parameter(Mandatory=$false)]
    [string[]]$Folders = @("Inbox", "Sent Items"),

    [Parameter(Mandatory=$false)]
    [bool]$SkipExisting = $true,

    [Parameter(Mandatory=$false)]
    [switch]$IncludeAttachments = $false
)

# Resolve paths relative to script location
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$OutputPath = Join-Path $ScriptDir "..\warehouse\daily\"
$LogPath = Join-Path $ScriptDir "..\logs\backfill.log"
$ExportScript = Join-Path $ScriptDir "Export-DailyEmails.ps1"

# Ensure output directory exists
New-Item -ItemType Directory -Force -Path $OutputPath | Out-Null

# Logging function
function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Write-Host $logMessage
    Add-Content -Path $LogPath -Value $logMessage
}

# Check if Export-DailyEmails.ps1 exists
if (-not (Test-Path $ExportScript)) {
    Write-Log "ERROR: Export-DailyEmails.ps1 not found at: $ExportScript"
    exit 1
}

Write-Log "========================================="
Write-Log "Starting Backfill Process"
Write-Log "========================================="
Write-Log "Date range: $($StartDate.ToString('yyyy-MM-dd')) to $($EndDate.ToString('yyyy-MM-dd'))"
Write-Log "Chunk size: $ChunkSize days"
Write-Log "Folders: $($Folders -join ', ')"
Write-Log "Skip existing: $SkipExisting"
Write-Log ""

# Calculate total days to process
$totalDays = ($EndDate - $StartDate).Days + 1
$totalChunks = [Math]::Ceiling($totalDays / $ChunkSize)
Write-Log "Total days to process: $totalDays"
Write-Log "Total chunks: $totalChunks"
Write-Log ""

# Process day-by-day (creates one JSON file per day for clean dashboard data)
$currentDate = $StartDate
$dayNumber = 0
$processedDays = 0
$skippedDays = 0
$errorDays = 0

$overallStartTime = Get-Date
$chunkStartTime = Get-Date
$daysInCurrentChunk = 0

while ($currentDate -le $EndDate) {
    $dayNumber++
    $daysInCurrentChunk++

    # Progress reporting - show chunk boundaries
    if ($daysInCurrentChunk -eq 1) {
        $chunkNumber = [Math]::Ceiling($dayNumber / $ChunkSize)
        Write-Log "========================================="
        Write-Log "Processing Chunk $chunkNumber of $totalChunks (Days $dayNumber-$([Math]::Min($dayNumber + $ChunkSize - 1, $totalDays)))"
        Write-Log "========================================="
        $chunkStartTime = Get-Date
    }

    $outputFile = Join-Path $OutputPath "$($currentDate.ToString('yyyy-MM-dd')).json"

    # Check if we should skip this day
    $shouldSkip = $false
    if ($SkipExisting -and (Test-Path $outputFile)) {
        Write-Log "[$($currentDate.ToString('yyyy-MM-dd'))] Skipping - file already exists"
        $skippedDays++
        $shouldSkip = $true
    }

    if (-not $shouldSkip) {
        Write-Log "[$($currentDate.ToString('yyyy-MM-dd'))] Exporting..."

        try {
            $exportParams = @{
                StartDate = $currentDate
                EndDate = $currentDate.Date.AddDays(1).AddSeconds(-1)  # End of day
                Folders = $Folders
            }

            if ($IncludeAttachments) {
                $exportParams.IncludeAttachments = $true
            }

            # Call the export script (runs in same process, shares logging)
            & $ExportScript @exportParams

            # Check if export was successful
            if (Test-Path $outputFile) {
                $fileInfo = Get-Item $outputFile
                $emailData = Get-Content $outputFile -Raw | ConvertFrom-Json
                Write-Log "[$($currentDate.ToString('yyyy-MM-dd'))] Success - $($emailData.total_emails) emails exported ($($fileInfo.Length) bytes)"
                $processedDays++
            } else {
                Write-Log "[$($currentDate.ToString('yyyy-MM-dd'))] Warning - export completed but no file created"
                $errorDays++
            }

        } catch {
            Write-Log "[$($currentDate.ToString('yyyy-MM-dd'))] ERROR: $_"
            $errorDays++
        }
    }

    # Move to next day
    $currentDate = $currentDate.AddDays(1)

    # Report chunk completion
    if ($daysInCurrentChunk -eq $ChunkSize -or $currentDate -gt $EndDate) {
        $chunkEndTime = Get-Date
        $chunkDuration = $chunkEndTime - $chunkStartTime
        Write-Log "Chunk completed in $($chunkDuration.TotalMinutes.ToString('F2')) minutes"
        Write-Log ""
        $daysInCurrentChunk = 0
    }

    # Progress update
    $percentComplete = [Math]::Round(($dayNumber / $totalDays) * 100, 1)
    if ($dayNumber % 10 -eq 0) {
        Write-Log "Overall Progress: $dayNumber / $totalDays days ($percentComplete%)"
        Write-Log ""
    }
}

# Final summary
$overallEndTime = Get-Date
$overallDuration = $overallEndTime - $overallStartTime

Write-Log "========================================="
Write-Log "Backfill Process Complete"
Write-Log "========================================="
Write-Log "Total days: $totalDays"
Write-Log "Processed: $processedDays"
Write-Log "Skipped: $skippedDays"
Write-Log "Errors: $errorDays"
Write-Log "Total time: $($overallDuration.TotalMinutes.ToString('F2')) minutes ($($overallDuration.TotalHours.ToString('F2')) hours)"
Write-Log ""

# Count total exported emails
Write-Log "Counting total exported emails..."
$totalEmailsExported = 0
$exportedFiles = Get-ChildItem -Path $OutputPath -Filter "*.json"

foreach ($file in $exportedFiles) {
    try {
        $content = Get-Content $file.FullName -Raw | ConvertFrom-Json
        $totalEmailsExported += $content.total_emails
    } catch {
        Write-Log "Warning: Could not read $($file.Name): $_"
    }
}

Write-Log "Total emails exported across all files: $totalEmailsExported"
Write-Log "Total JSON files: $($exportedFiles.Count)"
Write-Log ""
Write-Log "Backfill complete! Check logs at: $LogPath"

exit 0
