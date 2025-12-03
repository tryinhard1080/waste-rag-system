<#
.SYNOPSIS
    Find all email stores and folders in Outlook to locate where older emails are stored.
#>

# Connect to Outlook
Write-Host "Connecting to Outlook..."
try {
    $outlook = New-Object -ComObject Outlook.Application
    $namespace = $outlook.GetNamespace("MAPI")
    Write-Host "Successfully connected to Outlook"
} catch {
    Write-Host "ERROR: Failed to connect to Outlook: $_"
    exit 1
}

Write-Host "`n=== EMAIL STORES FOUND ===`n"

# Get all stores (mailboxes, archives, PST files)
$stores = $namespace.Stores
foreach ($store in $stores) {
    Write-Host "STORE: $($store.DisplayName)"
    Write-Host "  Type: $($store.Type)"
    Write-Host "  FilePath: $($store.FilePath)"
    Write-Host "  Root Folder: $($store.Root.FolderPath)"
    
    # Get folders in this store
    $folderTree = Get-FolderTree -Folder $store.Root -Indent "  "
    Write-Host $folderTree
    Write-Host ""
}

function Get-FolderTree {
    param(
        [object]$Folder,
        [string]$Indent
    )
    
    $output = ""
    $output += "$Indent- $($Folder.Name) ($($Folder.Items.Count) items)`n"
    
    try {
        foreach ($subFolder in $Folder.Folders) {
            $output += Get-FolderTree -Folder $subFolder -Indent "$Indent  "
        }
    } catch {
        # Might not have access to subfolders
    }
    
    return $output
}

Write-Host "`n=== TOTAL FOLDER COUNTS ===`n"

# Get common folders across all stores
$commonFolders = @("Inbox", "Sent Items", "Deleted Items", "Drafts")
$folderStats = @{}

foreach ($folderName in $commonFolders) {
    $totalItems = 0
    $locations = @()
    
    foreach ($store in $stores) {
        try {
            $folder = $store.GetRootFolder().Folders[$folderName]
            if ($folder) {
                $totalItems += $folder.Items.Count
                $locations += "  - $($store.DisplayName): $($folder.Items.Count) items"
            }
        } catch {
            # Folder not found in this store
        }
    }
    
    if ($totalItems -gt 0) {
        $folderStats[$folderName] = @{
            Total = $totalItems
            Locations = $locations
        }
    }
}

foreach ($folderName in $folderStats.Keys) {
    Write-Host "$folderName`: $($folderStats[$folderName].Total) total items"
    foreach ($location in $folderStats[$folderName].Locations) {
        Write-Host $location
    }
    Write-Host ""
}

# Cleanup
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($namespace) | Out-Null
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($outlook) | Out-Null
[System.GC]::Collect()
[System.GC]::WaitForPendingFinalizers()