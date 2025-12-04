# GitHub Data Repository Setup Guide

Complete guide to setting up GitHub as your central email data repository for multi-app access.

---

## 🎯 What This Achieves

```
┌─────────────────┐         ┌──────────────────────┐         ┌─────────────────┐
│ Local Windows   │         │ GitHub Private Repo  │         │  Your Apps      │
│                 │         │                      │         │                 │
│ Outlook Desktop │ sync    │ email-warehouse-data │ access  │ • bolt.new      │
│ Export Scripts  ├────────▶│                      ├────────▶│ • WasteWise     │
│ Scheduled Tasks │         │ • daily/*.json       │         │ • Future Apps   │
│                 │         │ • gemini/*.md        │         │                 │
└─────────────────┘         └──────────────────────┘         └─────────────────┘

   Extract locally          Store centrally          Access anywhere
```

**Benefits:**
- ✅ Access email data from any application (bolt.new, WasteWise, etc.)
- ✅ Single source of truth for all your apps
- ✅ Automatic version control and history
- ✅ No need to run extraction locally for each app
- ✅ Built-in backup and disaster recovery

---

## 📋 Step-by-Step Setup

### Step 1: Create GitHub Personal Access Token

1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Settings:
   - **Note**: `email-warehouse-data-access`
   - **Expiration**: No expiration (or 1 year)
   - **Scopes**: Check `repo` (Full control of private repositories)
4. Click "Generate token"
5. **IMPORTANT**: Copy the token (starts with `ghp_...`) - you won't see it again!
6. Save it securely (password manager recommended)

### Step 2: Create Private GitHub Repository

1. Go to: https://github.com/new
2. Settings:
   - **Repository name**: `email-warehouse-data`
   - **Description**: `Private email data repository for multi-app access`
   - **Visibility**: **Private** ⚠️ (IMPORTANT!)
   - **Initialize**: Leave all unchecked
3. Click "Create repository"
4. Copy the repository URL (e.g., `https://github.com/tryinhard1080/email-warehouse-data.git`)

### Step 3: Initialize Local Data Repository

Open PowerShell and run:

```powershell
cd C:\Users\richard.bates\Documents\email-warehouse\scripts

# Replace with your actual repo URL
.\Initialize-DataRepo.ps1 -GitHubRepoUrl "https://github.com/tryinhard1080/email-warehouse-data.git"
```

When prompted for credentials:
- **Username**: Your GitHub username
- **Password**: Use the Personal Access Token from Step 1 (NOT your GitHub password)

### Step 4: Verify Data Upload

1. Go to your repository: `https://github.com/tryinhard1080/email-warehouse-data`
2. You should see folders:
   - `daily/` - JSON email files
   - `gemini/` - Markdown batches
   - `threads/` - Thread aggregations
   - `summaries/` - Daily summaries

### Step 5: Set Up Automated Sync

#### Option A: Update Existing Scheduled Task

```powershell
# Update your scheduled task to use the new script
cd scripts
.\Setup-DailySync.ps1

# When creating the task, use Run-DailySync-WithGitHub.ps1 instead
```

#### Option B: Manual Sync After Each Export

```powershell
# Run this after your daily export
.\Sync-DataToGitHub.ps1
```

---

## 🔧 Configuration

### Configure Git Credentials (One-Time)

To avoid entering credentials every time:

```powershell
# Navigate to warehouse directory
cd ..\warehouse

# Store credentials
git config credential.helper store

# Next push will ask for credentials one last time, then remember them
```

### Environment Variables

For apps accessing the data, set:

```bash
# Windows
set GITHUB_TOKEN=ghp_your_token_here

# Linux/Mac
export GITHUB_TOKEN=ghp_your_token_here

# .env file (recommended)
echo "GITHUB_TOKEN=ghp_your_token_here" >> .env
```

---

## 📱 Accessing Data from Apps

### Python Example (WasteWise, Scripts, etc.)

```python
# Install requests if not already installed
# pip install requests

from email_data_access import EmailDataAccess

# Initialize with your token
data = EmailDataAccess(github_token="ghp_your_token_here")

# Get today's emails
emails = data.get_daily_emails()
print(f"Found {len(emails['emails'])} emails")

# Get specific date
emails_nov = data.get_daily_emails("2025-11-15")

# List all available dates
dates = data.list_all_dates()
```

### JavaScript Example (bolt.new, Web Apps)

```javascript
import { EmailDataAccess } from './emailData';

// Initialize
const data = new EmailDataAccess(process.env.GITHUB_TOKEN);

// Get emails
const emails = await data.getDailyEmails('2025-12-03');
console.log(`Found ${emails.emails.length} emails`);
```

**Full examples in:** `ACCESS_DATA_FROM_APPS.md`

---

## 🚀 Using with bolt.new

### 1. Create bolt.new Project

1. Go to: https://bolt.new
2. Create new project
3. Upload your dashboard files or start fresh

### 2. Set Environment Variables

In bolt.new project settings:
```
GITHUB_TOKEN=ghp_your_token_here
GITHUB_REPO=tryinhard1080/email-warehouse-data
```

### 3. Install Dependencies

```bash
npm install @octokit/rest
```

### 4. Access Data

```javascript
import { Octokit } from '@octokit/rest';

const octokit = new Octokit({
  auth: process.env.GITHUB_TOKEN
});

// Get file content
const { data } = await octokit.repos.getContent({
  owner: 'tryinhard1080',
  repo: 'email-warehouse-data',
  path: 'daily/2025-12-03.json'
});

// Decode content
const content = Buffer.from(data.content, 'base64').toString();
const emails = JSON.parse(content);
```

---

## 🔐 Security Checklist

- ✅ Repository is **Private**
- ✅ Personal Access Token stored securely (not in code)
- ✅ Token has **minimal permissions** (only `repo`)
- ✅ Token stored in environment variables or .env file
- ✅ .env file added to .gitignore
- ✅ Different tokens for different apps (recommended)
- ✅ Regular token rotation (every 90 days recommended)

---

## 📊 Monitoring & Maintenance

### Check Sync Status

```powershell
cd warehouse
git status
git log --oneline -5
```

### Manual Sync

```powershell
cd scripts
.\Sync-DataToGitHub.ps1
```

### View Commit History

```powershell
cd warehouse
git log --stat --oneline
```

### Check Repository Size

```powershell
cd warehouse
git count-objects -vH
```

---

## 🐛 Troubleshooting

### "Authentication failed"

**Solution:** Use Personal Access Token as password, not your GitHub password

```powershell
# Username: your-github-username
# Password: ghp_your_token_here (NOT your GitHub password)
```

### "Repository not found"

**Solutions:**
1. Verify repository exists: https://github.com/tryinhard1080/email-warehouse-data
2. Check repository URL is correct
3. Ensure repository is accessible with your token

### "Permission denied"

**Solution:** Regenerate token with `repo` scope:
1. Go to: https://github.com/settings/tokens
2. Delete old token
3. Create new token with `repo` scope

### Large repository warnings

GitHub has size limits:
- **Soft limit**: 1 GB (warning)
- **Hard limit**: 5 GB (blocked)

**Solutions:**
1. Rotate old data to archive repo
2. Use Git LFS for large files
3. Compress old JSON files

---

## 📈 Next Steps

1. ✅ Complete setup (Steps 1-5 above)
2. ✅ Test data access from Python
3. ✅ Set up bolt.new project
4. ✅ Integrate with WasteWise
5. ✅ Set up monitoring/alerts
6. ✅ Document your app-specific integration

---

## 🎓 Learning Resources

- **GitHub API**: https://docs.github.com/en/rest
- **Personal Access Tokens**: https://docs.github.com/en/authentication
- **Git Basics**: https://git-scm.com/book/en/v2/Getting-Started-Git-Basics
- **Octokit (JS)**: https://github.com/octokit/octokit.js

---

## 💡 Advanced Usage

### Multiple Apps Example

```python
# App 1: WasteWise Invoice Processor
from email_data_access import EmailDataAccess
invoice_data = EmailDataAccess(WASTEWISE_TOKEN)

# App 2: Property Management Dashboard
property_data = EmailDataAccess(PROPERTY_TOKEN)

# App 3: Analytics Service
analytics_data = EmailDataAccess(ANALYTICS_TOKEN)

# Each app uses separate token for security and monitoring
```

### Webhook Integration (Advanced)

Set up GitHub webhooks to notify apps when data changes:

1. Go to: `https://github.com/tryinhard1080/email-warehouse-data/settings/hooks`
2. Add webhook with your app's endpoint
3. Your app receives notifications on data updates

---

**Questions? Issues? Check CLAUDE.md or ACCESS_DATA_FROM_APPS.md**
