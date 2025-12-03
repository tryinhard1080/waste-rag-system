<#
.SYNOPSIS
    Count all emails from Outlook Desktop since January 1, 2025 without any exclusions.

.DESCRIPTION
    Connects to Outlook via COM interface and counts all emails from specified folders
    since January 1, 2025. This counts all emails regardless of category.
#>

param(
    [Parameter(Mandatory=$false)]
    [DateTime]$StartDate = "2025-01-01",
    
    [Parameter(Mandatory=$false)]
    [DateTime]$EndDate = (Get-Date).Date.AddDays(1).AddSeconds(-1),
    
    [Parameter(Mandatory=$false)]
    [string[]]$Folders = @("Inbox", "Sent Items")
)

# Resolve paths relative to script location
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$LogPath = Join-Path $ScriptDir "..\logs\export.log"

# Logging function
function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Write-Host $logMessage
    Add-Content -Path $LogPath -Value $logMessage
}

Write-Log "Starting email count for 2025..."
Write-Log "Date range: $($StartDate.ToString('yyyy-MM-dd')) to $($EndDate.ToString('yyyy-MM-dd'))"
Write-Log "Folders: $($Folders -join ', ')"

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

# Process emails
$totalEmailCount = 0
$folderCounts = @{}

foreach ($folderName in $Folders) {
    Write-Log "Counting emails in folder: $folderName"

    $folder = Get-OutlookFolder -FolderName $folderName -Namespace $namespace

    if (-not $folder) {
        Write-Log "Warning: Folder '$folderName' not found"
        continue
    }

    $items = $folder.Items
    $totalItems = $items.Count
    Write-Log "Found $totalItems items in $folderName"

    # Initialize folder count
    $folderCounts[$folderName] = 0

    # Sort by received time (most recent first)
    $items.Sort("[ReceivedTime]", $true)

    $itemCount = 0
    foreach ($item in $items) {
        $itemCount++
        if ($itemCount % 100 -eq 0) {
            Write-Log "Progress: $itemCount / $totalItems items processed in $folderName"
        }

        # Skip non-mail items
        if ($item.Class -ne 43) { # 43 = olMail
            continue
        }

        # Check if email is within date range (no category exclusions here)
        $itemDate = $item.ReceivedTime
        if ($folderName -eq "Sent Items") {
            $itemDate = $item.SentOn
        }

        if ($itemDate -ge $StartDate -and $itemDate -le $EndDate) {
            $folderCounts[$folderName]++
            $totalEmailCount++
        }
    }

    Write-Log "Completed folder: $folderName - $($folderCounts[$folderName]) emails found"
}

Write-Log ""
Write-Log "=== EMAIL COUNT SUMMARY ==="
Write-Log "Date Range: $($StartDate.ToString('yyyy-MM-dd')) to $($EndDate.ToString('yyyy-MM-dd'))"
Write-Log ""

foreach ($folderName in $Folders) {
    $count = if ($folderCounts.ContainsKey($folderName)) { $folderCounts[$folderName] } else { 0 }
    Write-Log "$folderName`: $count emails"
}

Write-Log ""
Write-Log "TOTAL EMAILS SINCE $((Get-Date $StartDate).ToString('MMMM dd, yyyy'))`: $totalEmailCount"
Write-Log ""

# Cleanup
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($namespace) | Out-Null
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($outlook) | Out-Null
[System.GC]::Collect()
[System.GC]::WaitForPendingFinalizers()

Write-Log "Email count process completed"
exit 0