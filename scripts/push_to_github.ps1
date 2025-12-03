<#
.SYNOPSIS
    Push email warehouse updates to GitHub repository.

.DESCRIPTION
    Automates git add, commit, and push for warehouse updates. Designed to run
    after email exports and Gemini markdown generation. Only commits Gemini batches
    and dashboard files (not raw JSON emails for privacy).

.PARAMETER Message
    Custom commit message (default: auto-generated with date)

.PARAMETER CreateRepo
    If true, creates the GitHub repo and sets up remote

.PARAMETER RepoName
    GitHub repository name (default: waste-rag-system)

.PARAMETER Username
    GitHub username (required for first-time setup)

.EXAMPLE
    .\push_to_github.ps1
    Push with auto-generated commit message

.EXAMPLE
    .\push_to_github.ps1 -Message "Added November 2025 emails"
    Push with custom message

.EXAMPLE
    .\push_to_github.ps1 -CreateRepo -Username "tryinhard1080"
    First-time setup: create repo and configure remote
#>

param(
    [Parameter(Mandatory=$false)]
    [string]$Message = "",

    [Parameter(Mandatory=$false)]
    [switch]$CreateRepo = $false,

    [Parameter(Mandatory=$false)]
    [string]$RepoName = "waste-rag-system",

    [Parameter(Mandatory=$false)]
    [string]$Username = ""
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir
$LogPath = Join-Path $RootDir "logs\github-sync.log"

function Write-Log {
    param([string]$Msg)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Msg"
    Write-Host $logMessage
    Add-Content -Path $LogPath -Value $logMessage
}

Set-Location $RootDir

Write-Log "========================================="
Write-Log "GitHub Push Automation"
Write-Log "========================================="

# Check if git is installed
try {
    $gitVersion = git --version
    Write-Log "Git detected: $gitVersion"
} catch {
    Write-Log "ERROR: Git not found. Please install Git for Windows."
    exit 1
}

# First-time setup: Create repo and configure remote
if ($CreateRepo) {
    if (-not $Username) {
        Write-Log "ERROR: Username required for repo creation. Use -Username parameter."
        exit 1
    }

    Write-Log "Creating GitHub repository: $Username/$RepoName"

    # Check if gh CLI is installed
    try {
        $ghVersion = gh --version
        Write-Log "GitHub CLI detected: $ghVersion"

        # Create repo using GitHub CLI
        Write-Log "Creating repository on GitHub..."
        gh repo create "$Username/$RepoName" --public --description "Email RAG System for Waste Management Operations" --confirm

        # Add remote
        git remote add origin "https://github.com/$Username/$RepoName.git"
        Write-Log "Remote added: origin -> https://github.com/$Username/$RepoName.git"

    } catch {
        Write-Log "WARNING: GitHub CLI (gh) not found. Creating remote URL manually."
        Write-Log "You'll need to create the repo manually at: https://github.com/new"
        Write-Log "Then run: git remote add origin https://github.com/$Username/$RepoName.git"

        # Add remote anyway
        try {
            git remote add origin "https://github.com/$Username/$RepoName.git"
            Write-Log "Remote configured (you still need to create the repo on GitHub)"
        } catch {
            Write-Log "Remote may already exist"
        }
    }

    Write-Log "First-time setup complete!"
    Write-Log ""
}

# Check for changes
$status = git status --porcelain
if (-not $status) {
    Write-Log "No changes to commit"
    exit 0
}

Write-Log "Changes detected:"
Write-Log $status
Write-Log ""

# Generate commit message if not provided
if (-not $Message) {
    $date = Get-Date -Format "yyyy-MM-dd"
    $geminiFiles = (Get-ChildItem -Path "warehouse\gemini" -Filter "*.md" -ErrorAction SilentlyContinue).Count
    $Message = "Update email warehouse - $date ($geminiFiles Gemini batches)"
}

Write-Log "Commit message: $Message"

# Stage files (only safe files, not raw JSON or logs)
Write-Log "Staging files..."

# Add Gemini batches (safe to commit)
git add warehouse/gemini/*.md 2>$null
Write-Log "  Added: Gemini markdown batches"

# Add dashboard files
git add dashboard/* 2>$null
Write-Log "  Added: Dashboard files"

# Add scripts and config (but not settings.json with sensitive data)
git add scripts/*.ps1 2>$null
git add scripts/*.py 2>$null
Write-Log "  Added: Scripts"

git add CLAUDE.md README.md .gitignore 2>$null
Write-Log "  Added: Documentation"

# Commit
Write-Log "Committing..."
try {
    git commit -m "$Message"
    Write-Log "Commit successful"
} catch {
    Write-Log "ERROR: Commit failed: $_"
    exit 1
}

# Push
Write-Log "Pushing to GitHub..."
try {
    git push -u origin main 2>&1 | ForEach-Object { Write-Log $_ }
    Write-Log "Push successful!"
} catch {
    Write-Log "ERROR: Push failed. You may need to:"
    Write-Log "  1. Set up GitHub authentication (gh auth login)"
    Write-Log "  2. Or use: git push -u origin main"
    exit 1
}

Write-Log ""
Write-Log "========================================="
Write-Log "GitHub sync complete!"
Write-Log "View at: https://github.com/$Username/$RepoName"
Write-Log "========================================="

exit 0
