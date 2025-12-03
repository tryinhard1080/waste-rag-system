# Email Warehouse - Quick Start Guide

Get your email warehouse up and running in 5 minutes!

## Prerequisites

- ✅ Windows 10/11
- ✅ Outlook Desktop installed and configured
- ✅ Python 3.8+ (optional, for thread aggregation and summaries)
  - Check: Open PowerShell and run `python --version`
  - If not installed: Download from [python.org](https://python.org)

## Step 1: First Email Export (2 minutes)

Open PowerShell and run:

```powershell
cd C:\Users\richard.bates\Documents\email-warehouse\scripts
.\Export-DailyEmails.ps1
```

This will:
- Connect to your Outlook
- Export today's emails to JSON
- Save to `warehouse/daily/YYYY-MM-DD.json`
- Log activity to `logs/export.log`

**What to expect:**
- You'll see progress messages as emails are processed
- Export typically takes 30 seconds to 2 minutes depending on email volume
- Check the log file if you encounter any issues

## Step 2: Process and Summarize (1 minute)

If you have Python installed:

```powershell
# Aggregate emails into threads
python aggregate_threads.py

# Generate today's summary
python generate_summary.py
```

This creates:
- `warehouse/threads/threads_current.json` - Conversation threads
- `warehouse/summaries/YYYY-MM-DD.md` - Daily summary with action items

**View your summary:**
```powershell
notepad ..\warehouse\summaries\$(Get-Date -Format 'yyyy-MM-dd').md
```

## Step 3: View Dashboard (30 seconds)

Open the dashboard in your browser:

```powershell
cd ..\dashboard
start index.html
```

Or simply double-click `dashboard/index.html` in File Explorer.

**Dashboard Features:**
- 📊 Daily stats and email list
- 📁 Projects view (auto-detected from your config)
- 👥 Contacts view
- 💬 Thread conversations
- 🔍 Search across all emails

## Step 4: Customize Configuration (Optional)

Edit `config/settings.json` to add your projects and contacts:

```powershell
notepad ..\config\settings.json
```

Add your:
- Property names (Columbia Square Living, etc.)
- Vendor names (Waste Management, etc.)
- Key contacts

This improves project detection and categorization.

## Step 5: Set Up Daily Automation (2 minutes)

Run as Administrator:

```powershell
# Right-click PowerShell → "Run as Administrator"
cd C:\Users\richard.bates\Documents\email-warehouse\scripts
.\Setup-ScheduledTask.ps1
```

This creates a Windows scheduled task that:
- Runs daily at 6 PM (configurable)
- Exports emails automatically
- Generates summaries
- Logs everything

**Options:**
```powershell
# Run at 8 AM instead
.\Setup-ScheduledTask.ps1 -RunTime "08:00"

# Run on weekdays only
.\Setup-ScheduledTask.ps1 -RunOnWeekdaysOnly

# Custom schedule
.\Setup-ScheduledTask.ps1 -RunTime "17:30" -RunOnWeekdaysOnly
```

## Common Tasks

### Export Older Emails (Backfill)

```powershell
# Export last 7 days
.\Export-DailyEmails.ps1 -StartDate (Get-Date).AddDays(-7) -EndDate (Get-Date)

# Export specific date range
.\Export-DailyEmails.ps1 -StartDate "2024-11-01" -EndDate "2024-11-30"
```

### Generate Summary for Specific Date

```powershell
python generate_summary.py 2024-12-01
```

### Export with Attachments

```powershell
.\Export-DailyEmails.ps1 -IncludeAttachments
```

## Troubleshooting

### PowerShell Execution Policy Error

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Outlook Connection Fails

1. Make sure Outlook Desktop is open and running
2. Try closing and reopening Outlook
3. Check that you have the necessary permissions

### Python Not Found

Download and install from [python.org](https://python.org), then:
- Make sure to check "Add Python to PATH" during installation
- Restart PowerShell after installation

### No Emails Exported

- Check date range matches when you have emails
- Review `logs/export.log` for details
- Verify folders exist in Outlook (Inbox, Sent Items)

## What's Next?

1. **Daily Routine**: Check your dashboard each morning for action items
2. **Weekly Review**: Use the Projects view to track ongoing initiatives
3. **Search**: Find old emails and conversations quickly
4. **Customize**: Update your config as you identify new projects/contacts

## File Locations

```
C:\Users\richard.bates\Documents\email-warehouse\
├── dashboard/index.html          ← Open this in browser
├── warehouse/
│   ├── daily/                    ← Your email exports
│   ├── summaries/                ← Daily summaries
│   └── threads/                  ← Conversation threads
├── logs/                         ← Check for errors
└── config/settings.json          ← Customize this
```

## Support

- Full documentation: `README.md`
- Check logs: `logs/export.log` and `logs/scheduled-export.log`
- Configuration help: See `config/settings.json` comments

---

**You're all set!** Your emails are being warehoused locally, organized, and summarized. 🎉
