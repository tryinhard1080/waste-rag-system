<#
.SYNOPSIS
    Export emails from Outlook Desktop to JSON format for warehousing.

.DESCRIPTION
    Connects to Outlook via COM interface and exports emails from specified folders
    to structured JSON files. Supports date range filtering and historical backfill.

.PARAMETER StartDate
    Beginning of date range to export (default: today)

.PARAMETER EndDate
    End of date range to export (default: today)

.PARAMETER Folders
    Array of folder names to process (default: Inbox, Sent Items)

.PARAMETER OutputPath
    Where to save JSON files (default: ../warehouse/daily/)

.PARAMETER IncludeAttachments
    Whether to save attachment files to disk (default: false)

.PARAMETER AttachmentPath
    Where to save attachment files (default: ../warehouse/attachments/)

.EXAMPLE
    .\Export-DailyEmails.ps1
    Exports today's emails from Inbox and Sent Items

.EXAMPLE
    .\Export-DailyEmails.ps1 -StartDate "2024-11-01" -EndDate "2024-11-30"
    Backfill emails from November 2024

.EXAMPLE
    .\Export-DailyEmails.ps1 -Folders @("Inbox", "Sent Items", "Archive") -IncludeAttachments
    Export from multiple folders and save attachment files
#>

param(
    [Parameter(Mandatory=$false)]
    [DateTime]$StartDate = (Get-Date).Date,

    [Parameter(Mandatory=$false)]
    [DateTime]$EndDate = (Get-Date).Date.AddDays(1).AddSeconds(-1),

    [Parameter(Mandatory=$false)]
    [string[]]$Folders = @("Inbox", "Sent Items"),

    [Parameter(Mandatory=$false)]
    [string]$OutputPath = "..\warehouse\daily\",

    [Parameter(Mandatory=$false)]
    [switch]$IncludeAttachments = $false,

    [Parameter(Mandatory=$false)]
    [string]$AttachmentPath = "..\warehouse\attachments\"
)

# Resolve paths relative to script location
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$OutputPath = Join-Path $ScriptDir $OutputPath
$AttachmentPath = Join-Path $ScriptDir $AttachmentPath
$ConfigPath = Join-Path $ScriptDir "..\config\settings.json"
$LogPath = Join-Path $ScriptDir "..\logs\export.log"

# Create directories if they don't exist
New-Item -ItemType Directory -Force -Path $OutputPath | Out-Null
if ($IncludeAttachments) {
    New-Item -ItemType Directory -Force -Path $AttachmentPath | Out-Null
}

# Logging function
function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Write-Host $logMessage
    Add-Content -Path $LogPath -Value $logMessage
}

Write-Log "Starting email export..."
Write-Log "Date range: $($StartDate.ToString('yyyy-MM-dd')) to $($EndDate.ToString('yyyy-MM-dd'))"
Write-Log "Folders: $($Folders -join ', ')"

# Load configuration
$config = $null
if (Test-Path $ConfigPath) {
    try {
        $config = Get-Content $ConfigPath -Raw | ConvertFrom-Json
        Write-Log "Configuration loaded from $ConfigPath"
    } catch {
        Write-Log "Warning: Could not load configuration: $_"
    }
}

# Connect to Outlook
Write-Log "Connecting to Outlook..."
try {
    $outlook = New-Object -ComObject Outlook.Application
    $namespace = $outlook.GetNamespace("MAPI")
    Write-Log "Successfully connected to Outlook"
} catch {
    Write-Log "ERROR: Failed to connect to Outlook: $_"
    exit 1
}

# Function to get folder by name
function Get-OutlookFolder {
    param(
        [string]$FolderName,
        [object]$Namespace
    )

    try {
        # Try to find folder in default store
        $folder = $Namespace.GetDefaultFolder([Microsoft.Office.Interop.Outlook.OlDefaultFolders]::"ol$FolderName")
        return $folder
    } catch {
        # If not a default folder, search by name
        $folders = $Namespace.Folders
        foreach ($store in $folders) {
            $folder = $store.Folders | Where-Object { $_.Name -eq $FolderName }
            if ($folder) {
                return $folder
            }
        }
    }
    return $null
}

# Function to determine if email is sent or received
function Get-EmailType {
    param([object]$Item, [string]$FolderName)

    if ($FolderName -eq "Sent Items") {
        return "sent"
    } else {
        return "received"
    }
}

# Function to extract email data
function Export-EmailItem {
    param(
        [object]$Item,
        [string]$FolderName
    )

    try {
        # Skip non-mail items
        if ($Item.Class -ne 43) { # 43 = olMail
            return $null
        }

        # Get item date for metadata (Restrict already filtered by date)
        $itemDate = $Item.ReceivedTime
        if ($FolderName -eq "Sent Items") {
            $itemDate = $Item.SentOn
        }

        # Check if excluded by category
        if ($config -and $config.outlook.exclude_categories) {
            foreach ($category in $Item.Categories -split ',') {
                $trimmedCategory = $category.Trim()
                if ($config.outlook.exclude_categories -contains $trimmedCategory) {
                    Write-Log "Skipping email (excluded category '$trimmedCategory'): $($Item.Subject)"
                    return $null
                }
            }
        }

        # Extract basic information
        $emailData = [PSCustomObject]@{
            id = $Item.EntryID
            type = Get-EmailType -Item $Item -FolderName $FolderName
            date = $itemDate.ToString("yyyy-MM-ddTHH:mm:ss")
            from = @{
                name = $Item.SenderName
                email = $Item.SenderEmailAddress
            }
            to = @()
            cc = @()
            subject = $Item.Subject
            body_text = $Item.Body
            body_preview = $Item.Body.Substring(0, [Math]::Min(500, $Item.Body.Length))
            conversation_topic = $Item.ConversationTopic
            conversation_id = $Item.ConversationID
            categories = @($Item.Categories -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ })
            importance = switch ($Item.Importance) {
                0 { "low" }
                1 { "normal" }
                2 { "high" }
                default { "normal" }
            }
            has_attachments = $Item.Attachments.Count -gt 0
            attachments = @()
            is_reply = $Item.Subject -match '^(RE:|Re:)'
            is_forwarded = $Item.Subject -match '^(FW:|Fw:|FWD:)'
        }

        # Extract recipients
        foreach ($recipient in $Item.Recipients) {
            $recipientEmail = $recipient.Address
            if ($recipient.Type -eq 1) { # To
                $emailData.to += $recipientEmail
            } elseif ($recipient.Type -eq 2) { # CC
                $emailData.cc += $recipientEmail
            }
        }

        # Extract attachments
        if ($Item.Attachments.Count -gt 0) {
            foreach ($attachment in $Item.Attachments) {
                $attachmentData = @{
                    filename = $attachment.FileName
                    size_bytes = $attachment.Size
                }

                # Save attachment file if requested
                if ($IncludeAttachments) {
                    $datePath = $itemDate.ToString("yyyy-MM-dd")
                    $attachmentDir = Join-Path $AttachmentPath $datePath
                    New-Item -ItemType Directory -Force -Path $attachmentDir | Out-Null

                    $attachmentFile = Join-Path $attachmentDir $attachment.FileName
                    try {
                        $attachment.SaveAsFile($attachmentFile)
                        $attachmentData.saved_path = $attachmentFile
                        Write-Log "Saved attachment: $attachmentFile"
                    } catch {
                        Write-Log "Warning: Could not save attachment $($attachment.FileName): $_"
                    }
                }

                $emailData.attachments += $attachmentData
            }
        }

        return $emailData

    } catch {
        Write-Log "Warning: Error processing email: $_"
        return $null
    }
}

# Process emails
$allEmails = @()
$processedCount = 0
$skippedCount = 0

foreach ($folderName in $Folders) {
    Write-Log "Processing folder: $folderName"

    $folder = Get-OutlookFolder -FolderName $folderName -Namespace $namespace

    if (-not $folder) {
        Write-Log "Warning: Folder '$folderName' not found"
        continue
    }

    $items = $folder.Items
    $totalItems = $items.Count
    Write-Log "Found $totalItems total items in $folderName"

    # Build date filter for Outlook Restrict (much faster than iterating all items)
    # Format dates for DASL query
    $startDateStr = $StartDate.ToString("MM/dd/yyyy HH:mm")
    $endDateStr = $EndDate.ToString("MM/dd/yyyy HH:mm")

    # Use ReceivedTime for received emails, SentOn for sent items
    $dateField = if ($folderName -eq "Sent Items") { "SentOn" } else { "ReceivedTime" }
    $filter = "[$dateField] >= '$startDateStr' AND [$dateField] <= '$endDateStr'"

    Write-Log "Applying date filter: $filter"

    try {
        $filteredItems = $items.Restrict($filter)
        $filteredCount = $filteredItems.Count
        Write-Log "Found $filteredCount items matching date range in $folderName"

        # Sort by date (most recent first)
        $filteredItems.Sort("[$dateField]", $true)

        $itemCount = 0
        foreach ($item in $filteredItems) {
            $itemCount++
            if ($itemCount % 100 -eq 0) {
                Write-Log "Progress: $itemCount / $filteredCount items processed in $folderName"
            }

            $emailData = Export-EmailItem -Item $item -FolderName $folderName

            if ($emailData) {
                $allEmails += $emailData
                $processedCount++
            } else {
                $skippedCount++
            }
        }
    } catch {
        Write-Log "Warning: Could not apply date filter, falling back to full iteration: $_"

        # Fallback to old method if Restrict fails
        $items.Sort("[ReceivedTime]", $true)

        $itemCount = 0
        foreach ($item in $items) {
            $itemCount++
            if ($itemCount % 100 -eq 0) {
                Write-Log "Progress: $itemCount / $totalItems items processed in $folderName (fallback mode)"
            }

            $emailData = Export-EmailItem -Item $item -FolderName $folderName

            if ($emailData) {
                $allEmails += $emailData
                $processedCount++
            } else {
                $skippedCount++
            }
        }
    }

    Write-Log "Completed folder: $folderName ($processedCount processed, $skippedCount skipped)"
}

# Create export object
$export = [PSCustomObject]@{
    export_date = $StartDate.ToString("yyyy-MM-dd")
    export_timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss")
    date_range = @{
        start = $StartDate.ToString("yyyy-MM-dd")
        end = $EndDate.ToString("yyyy-MM-dd")
    }
    folders_processed = $Folders
    total_emails = $allEmails.Count
    emails = $allEmails
}

# Save to JSON
$outputFile = Join-Path $OutputPath "$($StartDate.ToString('yyyy-MM-dd')).json"
try {
    $export | ConvertTo-Json -Depth 10 | Set-Content -Path $outputFile -Encoding UTF8
    Write-Log "Export completed successfully: $outputFile"
    Write-Log "Total emails exported: $($allEmails.Count)"
} catch {
    Write-Log "ERROR: Failed to save JSON file: $_"
    exit 1
}

# Cleanup
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($namespace) | Out-Null
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($outlook) | Out-Null
[System.GC]::Collect()
[System.GC]::WaitForPendingFinalizers()

Write-Log "Export process completed"
exit 0
