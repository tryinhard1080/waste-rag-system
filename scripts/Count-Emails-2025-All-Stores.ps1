<#
.SYNOPSIS
    Count all emails from all Outlook stores since January 1, 2025 without any exclusions.

.DESCRIPTION
    Connects to Outlook via COM interface and counts all emails from all mail stores
    (including archives) since January 1, 2025. This counts all emails regardless of category.
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

Write-Log "Starting email count for 2025 across ALL stores..."
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

# Get all stores
$stores = $namespace.Stores
Write-Log "Found $($stores.Count) email stores"

# Process emails
$totalEmailCount = 0
$storeFolderCounts = @{}

foreach ($store in $stores) {
    $storeName = $store.DisplayName
    Write-Log "Processing store: $storeName"
    
    if (-not $storeFolderCounts.ContainsKey($storeName)) {
        $storeFolderCounts[$storeName] = @{}
    }
    
    foreach ($folderName in $Folders) {
        try {
            $folder = $store.GetRootFolder().Folders[$folderName]
            if ($folder) {
                Write-Log "  Counting in ${storeName}\${folderName}..."
                
                $items = $folder.Items
                $totalItems = $items.Count
                Write-Log "    Found $totalItems items in ${storeName}\${folderName}"

                # Initialize folder count
                $storeFolderCounts[$storeName][$folderName] = 0

                # Sort by received time (most recent first)
                $items.Sort("[ReceivedTime]", $true)

                $itemCount = 0
                for ($i = 1; $i -le $totalItems; $i++) {
                    $itemCount++
                    if ($itemCount % 1000 -eq 0) {
                        Write-Log "    Progress: $itemCount / $totalItems items processed in ${storeName}\${folderName}"
                    }

                    try {
                        $item = $items.Item($i)
                        
                        # Skip non-mail items
                        if ($item.Class -ne 43) { # 43 = olMail
                            continue
                        }

                        # Check if email is within date range
                        $itemDate = $item.ReceivedTime
                        if ($folderName -eq "Sent Items") {
                            $itemDate = $item.SentOn
                        }

                        if ($itemDate -ge $StartDate -and $itemDate -le $EndDate) {
                            $storeFolderCounts[$storeName][$folderName]++
                            $totalEmailCount++
                        }
                    } catch {
                        # Skip items that can't be accessed
                        continue
                    }
                }

                Write-Log "  Completed ${storeName}\${folderName} - $($storeFolderCounts[$storeName][$folderName]) emails found"
            }
        } catch {
            Write-Log "  Warning: Could not access folder $folderName in store ${storeName}: $($_)"
            continue
        }
    }
}

Write-Log ""
Write-Log "=== EMAIL COUNT SUMMARY BY STORE ==="
Write-Log "Date Range: $($StartDate.ToString('yyyy-MM-dd')) to $($EndDate.ToString('yyyy-MM-dd'))"
Write-Log ""

foreach ($storeName in $storeFolderCounts.Keys) {
    Write-Log "STORE: $storeName"
    $storeTotal = 0
    
    foreach ($folderName in $Folders) {
        $count = if ($storeFolderCounts[$storeName].ContainsKey($folderName)) { $storeFolderCounts[$storeName][$folderName] } else { 0 }
        Write-Log "  $folderName`: $count emails"
        $storeTotal += $count
    }
    
    Write-Log "  Store Total: $storeTotal emails"
    Write-Log ""
}

Write-Log "=== TOTAL COUNT BY FOLDER TYPE ==="
$folderTypeTotals = @{}
foreach ($storeName in $storeFolderCounts.Keys) {
    foreach ($folderName in $storeFolderCounts[$storeName].Keys) {
        if (-not $folderTypeTotals.ContainsKey($folderName)) {
            $folderTypeTotals[$folderName] = 0
        }
        $folderTypeTotals[$folderName] += $storeFolderCounts[$storeName][$folderName]
    }
}

foreach ($folderName in $folderTypeTotals.Keys) {
    Write-Log "$folderName (all stores): $($folderTypeTotals[$folderName]) emails"
}

Write-Log ""
Write-Log "================================================"
Write-Log "TOTAL EMAILS SINCE $((Get-Date $StartDate).ToString('MMMM dd, yyyy'))`S ACROSS ALL STORES`: $totalEmailCount"
Write-Log "================================================"
Write-Log ""

# Cleanup
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($namespace) | Out-Null
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($outlook) | Out-Null
[System.GC]::Collect()
[System.GC]::WaitForPendingFinalizers()

Write-Log "Email count process completed"
exit 0