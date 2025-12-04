# Full 2025 Email Sync to GitHub - Quick Guide

## 🎯 What This Does

Syncs ALL your 2025 emails to GitHub in **both formats**:
- ✅ **JSON files** (raw data - backup/app access)
- ✅ **Markdown files** (RAG optimized - AI queries)

This gives you redundancy: If RAG fails, you still have raw JSON data!

---

## 📊 Current Status

**Already Extracted:**
- **337 JSON files** (Jan 1 - Dec 3, 2025)
- Date range: 2025-01-01 to 2025-12-03
- Location: `warehouse/daily/*.json`

**Next Steps:**
1. Convert to Gemini markdown
2. Upload to RAG
3. Push both JSON + markdown to GitHub

---

## 🚀 One-Command Full Sync

### Prerequisites

1. **Create GitHub repository** (one-time):
   - Go to: https://github.com/new
   - Name: `email-warehouse-data`
   - Visibility: **Private**
   - Don't initialize with anything
   - Click "Create"

2. **Get your GitHub token** (if not already):
   - Go to: https://github.com/settings/tokens
   - Generate new token (classic)
   - Scope: `repo`
   - Copy the token (ghp_...)

3. **Set Gemini API key** (optional, for RAG):
   ```powershell
   set GOOGLE_API_KEY=your_key_here
   ```

### Run Full Sync

```powershell
cd C:\Users\richard.bates\Documents\email-warehouse\scripts

# Full sync (convert + RAG + GitHub)
.\Full-Sync-To-GitHub.ps1 -GitHubRepoUrl "https://github.com/tryinhard1080/email-warehouse-data.git"
```

**What it does:**
1. ✅ Converts 337 JSON files → Gemini markdown
2. ✅ Uploads markdown to Gemini RAG
3. ✅ Initializes Git in warehouse/ folder
4. ✅ Commits **both** JSON and markdown files
5. ✅ Pushes to GitHub

**Duration:** ~5-10 minutes

---

## 📦 What Gets Uploaded to GitHub

### File Structure

```
email-warehouse-data/
├── daily/                    # 337 JSON files (RAW DATA - BACKUP)
│   ├── 2025-01-01.json
│   ├── 2025-01-02.json
│   ├── ...
│   └── 2025-12-03.json
│
├── gemini/                   # Markdown batches (RAG OPTIMIZED)
│   ├── batch_2025-01_001.md
│   ├── batch_2025-02_001.md
│   ├── ...
│   └── batch_2025-12_001.md
│
├── threads/                  # Thread aggregations (optional)
│   └── threads_current.json
│
└── summaries/                # Daily summaries (optional)
    └── *.md
```

### File Sizes

**JSON files:**
- ~337 files × ~50KB average = ~17MB
- Contains: Full email metadata, subjects, body previews

**Markdown files:**
- ~12 monthly batches
- Total: ~25MB
- Contains: Formatted for RAG, optimized for AI search

**Total repository size:** ~40-50MB (well within GitHub limits)

---

## 🔄 Future Updates

### Daily Automated Sync

After initial setup, use:

```powershell
# Option 1: Manual daily sync
cd scripts
.\Run-DailySync-WithGitHub.ps1

# Option 2: Scheduled task (automated)
.\Setup-DailySync.ps1
# Point to Run-DailySync-WithGitHub.ps1
```

This will:
1. Export today's emails → JSON
2. Convert to markdown
3. Upload to RAG
4. **Push to GitHub** (both JSON + markdown)

---

## 📱 Accessing the Data

### From Any App (Python)

```python
from email_data_access import EmailDataAccess

# Access via GitHub API
data = EmailDataAccess(github_token="ghp_your_token")

# Get any date's emails
emails = data.get_daily_emails("2025-11-15")

# Get specific month
batch = data.get_gemini_batch("batch_2025-11_001")
```

### From bolt.new (JavaScript)

```javascript
// Set in environment
const GITHUB_TOKEN = process.env.GITHUB_TOKEN;

// Fetch any date
const response = await fetch(
  `https://api.github.com/repos/tryinhard1080/email-warehouse-data/contents/daily/2025-11-15.json`,
  {
    headers: {
      'Authorization': `token ${GITHUB_TOKEN}`,
      'Accept': 'application/vnd.github.v3+json'
    }
  }
);

const data = await response.json();
const content = JSON.parse(atob(data.content));
```

### Git Clone Method (Local Apps)

```bash
# One-time: Clone the repository
git clone https://github.com/tryinhard1080/email-warehouse-data.git

# In your app: Read files directly
import json
with open('email-warehouse-data/daily/2025-11-15.json') as f:
    emails = json.load(f)
```

---

## 🔐 Redundancy & Backup

### Why Both JSON and Markdown?

**JSON (Raw Data):**
- ✅ Original format from Outlook
- ✅ Can be used by any app
- ✅ Backup if RAG system fails
- ✅ Can reprocess/convert later
- ✅ Full flexibility

**Markdown (RAG Optimized):**
- ✅ Optimized for AI search
- ✅ Better for Gemini queries
- ✅ Batched efficiently
- ✅ Faster RAG queries

**Best of both worlds:** Use RAG for queries, fall back to JSON if needed!

---

## 🛠️ Troubleshooting

### "Permission denied" when pushing

**Solution:** Use your GitHub token as password:
```
Username: your-github-username
Password: ghp_your_token_here (NOT your GitHub password!)
```

### "Repository not found"

**Solution:** Create the repository first at https://github.com/new

### Skip RAG upload (if Gemini key not set)

```powershell
.\Full-Sync-To-GitHub.ps1 `
  -GitHubRepoUrl "https://github.com/tryinhard1080/email-warehouse-data.git" `
  -SkipRAGUpload
```

### Already have Git initialized in warehouse/

```powershell
# Just sync (don't reinitialize)
.\Sync-DataToGitHub.ps1 -CommitMessage "Full sync: All 2025 emails"
```

---

## 📊 Verification

After sync completes, verify:

1. **GitHub repository:**
   - Go to: https://github.com/tryinhard1080/email-warehouse-data
   - Check `daily/` folder has 337 JSON files
   - Check `gemini/` folder has ~12 markdown files

2. **Local files:**
   ```powershell
   ls warehouse/daily/*.json | measure
   # Should show: Count: 337

   ls warehouse/gemini/*.md | measure
   # Should show: Count: ~12
   ```

3. **RAG system:**
   ```powershell
   cd scripts
   python setup_gemini_rag.py --list-files
   # Should show all uploaded batches
   ```

4. **Test access:**
   ```python
   from email_data_access import EmailDataAccess
   data = EmailDataAccess(token)
   emails = data.get_daily_emails("2025-11-15")
   print(len(emails['emails']))  # Should show email count
   ```

---

## 🎯 Success Checklist

- [ ] GitHub repository created (private)
- [ ] Personal access token obtained
- [ ] Gemini API key set (optional)
- [ ] Full-Sync-To-GitHub.ps1 executed
- [ ] All files pushed to GitHub
- [ ] RAG upload completed (if API key set)
- [ ] Verified files on GitHub
- [ ] Tested access from Python/JavaScript
- [ ] Set up automated daily sync

---

## 💡 What's Next?

1. **bolt.new app:** Create web interface using GitHub data
2. **WasteWise integration:** Access email history in invoice processing
3. **Analytics dashboard:** Build reports from email data
4. **Mobile access:** Query from phone via GitHub API
5. **Scheduled reports:** Daily email summaries via email

---

**Ready to sync? Run the command above!** 🚀

Full documentation: `ACCESS_DATA_FROM_APPS.md` and `GITHUB_DATA_SETUP.md`
