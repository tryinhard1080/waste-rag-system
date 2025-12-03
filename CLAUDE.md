# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Local Windows-based email warehouse system that extracts emails from Outlook Desktop via COM interface, stores them as JSON, aggregates into conversation threads, generates actionable summaries, and provides an HTML dashboard for browsing. Built for managing high-volume email communications across multifamily properties, vendors, and projects.

**Key Constraint:** No external API dependencies - all processing is local.

## Essential Commands

### Email Export (PowerShell)

```powershell
# Basic daily export
cd scripts
.\Export-DailyEmails.ps1

# Historical backfill
.\Export-DailyEmails.ps1 -StartDate "2024-11-01" -EndDate "2024-11-30"

# Export with specific parameters
.\Export-DailyEmails.ps1 -Folders @("Inbox", "Sent Items", "Archive") -IncludeAttachments

# Date range with PowerShell date math
$startDate = (Get-Date).AddDays(-7)
.\Export-DailyEmails.ps1 -StartDate $startDate -EndDate (Get-Date)
```

### Thread Aggregation and Summary (Python)

```powershell
# Aggregate all daily exports into conversation threads
python aggregate_threads.py

# Generate today's summary with action items
python generate_summary.py

# Generate summary for specific date
python generate_summary.py 2024-12-01
```

### Dashboard

```powershell
cd dashboard
start index.html
# Or double-click index.html in File Explorer
```

### Automation Setup

```powershell
# Must run as Administrator
.\Setup-ScheduledTask.ps1

# Custom schedule options
.\Setup-ScheduledTask.ps1 -RunTime "08:00" -RunOnWeekdaysOnly
```

## Architecture

### Three-Stage Processing Pipeline

**Stage 1: Export (PowerShell → JSON)**
- `Export-DailyEmails.ps1` connects to Outlook via COM (`New-Object -ComObject Outlook.Application`)
- Iterates through specified folders (default: Inbox, Sent Items)
- Filters by date range and excluded categories from config
- Extracts metadata: from/to/cc, subject, body, conversation_id, conversation_topic, attachments
- Outputs to `warehouse/daily/YYYY-MM-DD.json` with structured format

**Stage 2: Aggregation (Python → Thread Analysis)**
- `aggregate_threads.py` reads all daily JSON files within retention period (config: `days_to_retain`)
- Groups emails by `conversation_id` (primary) or normalized `conversation_topic` (fallback)
- Topic normalization: strips RE:/FW: prefixes, trims whitespace
- Detects projects via pattern matching against `config/settings.json`:
  - `known_properties`: Property names in subject/body
  - `known_vendors`: Vendor names in subject/body
  - `known_contacts`: Email addresses or keywords
- Determines thread status based on last activity: active (<2 days), recent (<7 days), aging (<14 days), stale (>14 days)
- Outputs to `warehouse/threads/threads_current.json`

**Stage 3: Summarization (Python → Markdown)**
- `generate_summary.py` loads today's emails + thread context
- **Action item extraction** (regex patterns):
  - `can you`, `could you`, `please`, `need to`, `action required`, `send/provide`, `need by`, `follow up`
- **Question extraction**: Sentences ending in `?` from received emails
- **Commitment extraction**: `I will`, `I'll`, `going to`, `committed to` from sent emails
- **Priority assignment**: High priority if email importance = high or urgent indicators present
- **Project categorization**: Uses same detection logic as Stage 2
- Outputs to `warehouse/summaries/YYYY-MM-DD.md` in task-oriented format

### Key Data Structures

**Daily Export JSON Schema:**
```json
{
  "export_date": "2024-12-02",
  "emails": [{
    "id": "EntryID",
    "type": "received|sent",
    "from": {"name": "", "email": ""},
    "to": ["email1", "email2"],
    "conversation_id": "Outlook ConversationID",
    "conversation_topic": "Original subject without RE:/FW:",
    "categories": ["Category1"],
    "importance": "normal|high|low"
  }]
}
```

**Thread Aggregation Output:**
```json
{
  "threads": [{
    "thread_id": "conversation_id or generated",
    "topic": "normalized subject",
    "participants": ["email@domain.com"],
    "message_count": 5,
    "status": "active|recent|aging|stale",
    "projects_detected": ["Property: Name", "Vendor: Name"],
    "messages": [{"date": "", "from": "", "subject": ""}]
  }],
  "projects": {
    "Property: Columbia Square Living": ["thread_id1", "thread_id2"]
  }
}
```

### Configuration-Driven Project Detection

The system uses `config/settings.json` for smart categorization:

```json
{
  "projects": {
    "known_properties": ["Columbia Square Living", "Jardine"],
    "known_vendors": ["Waste Management", "Ally Waste"],
    "known_contacts": {
      "Keith Conrad": "keith.conrad@dsqtech.com",
      "Joe Peacock": "columbia square"
    }
  }
}
```

Detection logic (aggregate_threads.py:84, generate_summary.py:242):
1. Combine email subject + body_preview into searchable text
2. Case-insensitive matching against known_properties/known_vendors
3. Match sender email against known_contacts keys or values
4. Label detected items as "Property: X", "Vendor: Y", "Contact: Z"

### Dashboard Architecture (Client-Side Only)

`dashboard/app.js` implements a single-page application:
- **No server required** - uses `fetch()` to load local JSON files from `../warehouse/`
- **EmailDashboard class** manages state: emails, threads, projects, currentFilter, currentView
- **Five views**: Daily (default), Projects, Contacts, Threads, Search
- **Modal system** for email/thread details
- **Date selector** dynamically populated (last 30 days)
- **Search** performs client-side filtering across subject, body, sender

Important: Dashboard assumes relative paths (`../warehouse/daily/`, `../warehouse/threads/`) so it must be opened from the `dashboard/` folder.

### COM Interaction Patterns (PowerShell)

Key patterns in `Export-DailyEmails.ps1`:

**Connection and cleanup (lines 73-86, 324-330):**
```powershell
$outlook = New-Object -ComObject Outlook.Application
$namespace = $outlook.GetNamespace("MAPI")
# ... use COM objects ...
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($namespace)
[System.GC]::Collect()  # Critical for COM cleanup
```

**Folder navigation:**
- Default folders: `$namespace.GetDefaultFolder([Microsoft.Office.Interop.Outlook.OlDefaultFolders]::"olFolderName")`
- Custom folders: Search through `$namespace.Folders` collection

**Email filtering:**
- Items sorted by ReceivedTime: `$items.Sort("[ReceivedTime]", $true)`
- Date comparison on `$Item.ReceivedTime` (received) or `$Item.SentOn` (sent)
- Category exclusion checked against config's `exclude_categories`

## Development Workflow

### Adding New Project Detection

1. Edit `config/settings.json` → add to `known_properties`, `known_vendors`, or `known_contacts`
2. Detection happens automatically in both `aggregate_threads.py` and `generate_summary.py`
3. Re-run aggregation to update thread associations: `python aggregate_threads.py`

### Extending Summary Patterns

Edit `generate_summary.py`:
- Action items: Add patterns to `_extract_action_items()` regex list (line 106)
- Questions: Modify sentence splitting in `_extract_questions()` (line 134)
- Commitments: Update patterns in `_extract_commitments()` (line 157)

### Modifying Export Fields

Edit `Export-DailyEmails.ps1` → `Export-EmailItem` function (line 106):
- Add new properties to `$emailData` PSCustomObject
- Access Outlook item properties via `$Item.PropertyName`
- Update JSON schema documentation if adding required fields

### Dashboard View Customization

Edit `dashboard/app.js`:
- Add view: Create `render[ViewName]View()` method + HTML section in `index.html`
- Modify filters: Update `getFilteredEmails()` or `applyFilter()` switch statements
- Change UI: Edit `styles.css` (uses CSS Grid for responsive layout)

## Data Flow and Dependencies

**Sequential dependencies:**
1. `Export-DailyEmails.ps1` must run first (creates `warehouse/daily/*.json`)
2. `aggregate_threads.py` depends on daily exports (reads all JSON files)
3. `generate_summary.py` depends on both daily export + thread aggregation
4. Dashboard depends on all three (reads daily JSON + threads JSON + summaries MD)

**Configuration dependency:**
All components read `config/settings.json` at runtime:
- PowerShell: Checks `exclude_categories` and `days_to_retain`
- Python scripts: Use `projects` section for detection
- Important: Changes to config require re-running aggregation/summary

## Logging and Troubleshooting

- **Export logs:** `logs/export.log` (per-execution, created by Export-DailyEmails.ps1)
- **Scheduled task logs:** `logs/scheduled-export.log` (created by wrapper script)
- **PowerShell execution policy:** If scripts won't run, execute: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
- **Outlook COM issues:** Ensure Outlook Desktop is running before executing export
- **Python module errors:** Scripts use only stdlib (json, os, sys, datetime, pathlib, collections, re)

## Windows Task Scheduler Integration

`Setup-ScheduledTask.ps1` creates:
1. **Wrapper script:** `scripts/Run-DailyExport.ps1` (chains all three stages)
2. **Scheduled task:** Runs wrapper at configured time
3. **Task settings:** AllowStartIfOnBatteries, StartWhenAvailable, RunOnlyIfNetworkAvailable:$false

The wrapper script executes sequentially:
1. Export-DailyEmails.ps1
2. aggregate_threads.py (if Python available)
3. generate_summary.py (if Python available)

All stages log to `scheduled-export.log` with timestamps.
