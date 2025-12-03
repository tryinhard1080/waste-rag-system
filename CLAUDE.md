# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Local Windows-based email warehouse system that extracts emails from Outlook Desktop via COM interface, stores them as JSON, aggregates into conversation threads, generates actionable summaries, and provides **Gemini RAG-powered semantic search** through both an interactive dashboard and Python API. Built for managing high-volume email communications across multifamily properties, vendors, and projects.

**Key Capabilities:**
- Fast Outlook extraction (10-100x faster than traditional methods)
- AI-powered semantic search over 1,000+ emails using Google Gemini
- Clean Python API for integration with existing systems (e.g., WasteWise)
- Interactive dashboard v2 with analytics and real-time RAG queries

## Essential Commands

### Email Export (PowerShell)

```powershell
# Basic daily export
cd scripts
.\Export-DailyEmails.ps1

# Historical backfill (fast, resumable)
.\Backfill-2025-Emails.ps1 -StartDate "2025-01-01"
.\Backfill-2025-Emails.ps1 -StartDate "2025-01-01" -SkipExisting  # Resume after interruption

# Export with specific parameters
.\Export-DailyEmails.ps1 -Folders @("Inbox", "Sent Items", "Archive") -IncludeAttachments

# Date range with PowerShell date math
$startDate = (Get-Date).AddDays(-7)
.\Export-DailyEmails.ps1 -StartDate $startDate -EndDate (Get-Date)

# Investigate email availability
.\Find-All-Email-Stores.ps1
.\Count-Emails-2025.ps1
.\Count-Emails-2025-All-Stores.ps1
```

### Gemini RAG (Python)

```bash
# Convert JSON exports to Gemini-optimized markdown
python convert_to_gemini_format.py --batch-by month

# Upload all batches to Gemini RAG
python setup_gemini_rag.py --upload-all

# Query your email knowledge base
python setup_gemini_rag.py --query "What contamination issues have we dealt with?"

# List uploaded files
python setup_gemini_rag.py --list-files
```

### API Integration (Python)

```python
# Use in your applications (e.g., WasteWise)
from api.email_knowledge_api import EmailKnowledgeAPI

kb = EmailKnowledgeAPI(gemini_api_key="YOUR_KEY")
insights = kb.get_vendor_insights("Waste Management")
similar = kb.get_similar_invoices({'vendor': 'WM', 'property': 'Avana'})
```

### Thread Aggregation and Summary (Python - Optional)

```powershell
# Aggregate all daily exports into conversation threads
python aggregate_threads.py

# Generate today's summary with action items
python generate_summary.py

# Generate summary for specific date
python generate_summary.py 2024-12-01
```

### Dashboard & RAG API

```powershell
# One-click startup (RECOMMENDED - starts both API and dashboard)
.\start-email-warehouse.bat

# Manual: Start RAG API server (required for live AI queries in dashboard)
cd api
.\start_rag_api.bat
# API runs at http://localhost:5000

# Manual: Start dashboard server (in separate terminal)
cd dashboard-v2
python -m http.server 8000
# Then open http://localhost:8000/dashboard-v2/index.html

# Legacy: Dashboard v1 (basic views, no live RAG)
cd dashboard
start index.html
```

### Automation Setup

```powershell
# RECOMMENDED: Daily sync (export → convert → upload to RAG)
# Must run as Administrator
cd scripts
.\Setup-DailySync.ps1

# Custom schedule options
.\Setup-DailySync.ps1 -RunTime "07:00"

# Manual daily sync (test the scheduled task)
.\Run-DailySync.ps1

# LEGACY: Old scheduled task setup (includes thread aggregation)
.\Setup-ScheduledTask.ps1 -RunTime "08:00" -RunOnWeekdaysOnly
```

## Architecture

### Four-Stage Processing Pipeline

**Stage 1: Export (PowerShell → JSON)**
- `Export-DailyEmails.ps1` connects to Outlook via COM (`New-Object -ComObject Outlook.Application`)
- Uses Outlook Restrict filtering for 10-100x speed improvement
- Iterates through specified folders (default: Inbox, Sent Items)
- Filters by date range and excluded categories from config
- Extracts metadata: from/to/cc, subject, body, conversation_id, conversation_topic, attachments
- Outputs to `warehouse/daily/YYYY-MM-DD.json` with structured format
- **Performance**: ~3 seconds per day, 17 minutes for 337 days (full 2025 backfill)

**Stage 2: Conversion (Python → Gemini-Optimized Markdown)**
- `convert_to_gemini_format.py` reads all daily JSON files
- Converts to clean markdown format optimized for RAG
- Batches by month to stay under Gemini's 100MB file limit
- Adds metadata headers for better semantic search
- Outputs to `warehouse/gemini/batch_YYYY-MM_001.md`
- **Performance**: ~1-2 seconds per batch

**Stage 3: Gemini RAG (Python → AI Knowledge Base)**
- `setup_gemini_rag.py` manages Gemini File Search RAG system
- Uploads markdown batches to Gemini API
- Tracks uploaded files in `config/gemini_config.json`
- Provides query interface for semantic search
- Returns AI-generated answers with context from your emails
- **Performance**: 3-6 seconds per query

**Stage 4 (Optional): Aggregation & Summarization (Python → Thread Analysis)**
- `aggregate_threads.py` reads all daily JSON files within retention period (config: `days_to_retain`)
- Groups emails by `conversation_id` (primary) or normalized `conversation_topic` (fallback)
- Topic normalization: strips RE:/FW: prefixes, trims whitespace
- Detects projects via pattern matching against `config/settings.json`:
  - `known_properties`: Property names in subject/body
  - `known_vendors`: Vendor names in subject/body
  - `known_contacts`: Email addresses or keywords
- Determines thread status based on last activity: active (<2 days), recent (<7 days), aging (<14 days), stale (>14 days)
- Outputs to `warehouse/threads/threads_current.json`

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

**Gemini Markdown Format:**
```markdown
# Email: Subject Line

**From:** Name <email@domain.com>
**To:** recipient@domain.com
**Date:** 2025-11-06 14:33:56
**Type:** sent

## Body
Email body content here...
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

**Gemini Config:**
```json
{
  "store_name": "waste-management-emails",
  "created_at": "2025-12-03T12:31:27",
  "files": [
    {"name": "batch_2025-11_001.md", "uri": "https://...", "size_mb": 4.76}
  ]
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

### Gemini RAG Architecture

**Components:**
- **File Storage**: Gemini Files API manages uploaded markdown batches
- **Model**: gemini-2.0-flash-exp (latest experimental model)
- **Search Strategy**: Keyword-based markdown file filtering + Gemini grounding
- **Config Tracking**: `config/gemini_config.json` stores file URIs and metadata

**Query Flow:**
1. User submits natural language question
2. System searches markdown files for relevant keywords (line setup_gemini_rag.py:200+)
3. Relevant chunks passed to Gemini as context
4. Gemini generates answer grounded in actual email content
5. Returns AI response with citations

**Performance:**
- Query time: 3-6 seconds
- Cost: ~$0.001-0.003 per query
- Max context: 10 email chunks per query (configurable)

### API Layer Architecture

**Purpose**: Clean integration layer for using email knowledge in existing systems (e.g., WasteWise invoice processing)

**Location**: `api/email_knowledge_api.py`

**Key Methods:**
- `get_vendor_insights(vendor_name)`: Historical vendor communication analysis
- `get_similar_invoices(invoice_details)`: Find past similar scenarios
- `get_resolution_history(issue_type)`: How similar issues were resolved
- `get_property_communication_history(property_name)`: Property-specific email history
- `get_writing_style_examples(topic)`: Your writing style for AI-assisted composition
- `get_contract_negotiation_insights(vendor)`: Negotiation tactics and pricing insights

**Integration Example:**
```python
# In invoice processing system
def review_invoice(invoice):
    kb = EmailKnowledgeAPI(gemini_api_key)
    vendor_history = kb.get_vendor_insights(invoice['vendor'])
    similar_cases = kb.get_similar_invoices({
        'vendor': invoice['vendor'],
        'property': invoice['property']
    })
    return {
        'approve': has_precedent(similar_cases),
        'confidence': calculate_confidence(vendor_history),
        'notes': similar_cases['recommendations']
    }
```

See `api/README.md` for full integration guide and `api/integration_examples.py` for working examples.

### Flask REST API Architecture (Backend for Dashboard)

**Location**: `api/rag_api.py`

**Purpose**: Provides live RAG query endpoints for dashboard-v2

**Endpoints:**
- `GET /api/health` - Health check
- `POST /api/query` - Query RAG system with natural language
- `GET /api/stats` - Get RAG system statistics
- `GET /api/example-queries` - Get example queries for UI

**Technology:**
- Flask web framework
- Flask-CORS for cross-origin requests
- Integrates with `setup_gemini_rag.py` GeminiRAGManager

**Quick Start:**
```bash
# Method 1: Use startup script
cd api
.\start_rag_api.bat

# Method 2: Direct Python
set GOOGLE_API_KEY=your_key
python api/rag_api.py
```

**API runs at**: `http://localhost:5000`

**Query Example:**
```bash
curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What are recent contamination issues?"}'
```

### Dashboard v2 Architecture (Modern UI)

**Location**: `dashboard-v2/`

**Features:**
- **Overview**: Stats cards, email volume chart, type distribution, recent activity
- **Analytics**: Top senders/recipients, vendor analysis, property tracking
- **AI Query**: **Live** natural language RAG queries via Flask API backend
- **Search**: Full-text search with date range and type filters
- **Timeline**: Bar charts showing email volume by day/week/month

**Technology Stack:**
- Vanilla JavaScript (no frameworks)
- Chart.js for data visualization
- CSS Grid for responsive layout
- Fetch API for loading local JSON files
- **REST API integration** with backend Flask server

**Important**: Dashboard uses `fetch()` to load JSON from `../warehouse/daily/`. **Live RAG queries** require the Flask backend API (`api/rag_api.py`) running on port 5000. Use `start-email-warehouse.bat` to launch both servers automatically.

### Dashboard v1 Architecture (Original - Client-Side Only)

**Location**: `dashboard/`

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

**Performance optimization - Restrict filtering:**
```powershell
# OLD (slow): Loop through all items
foreach ($item in $items) {
    if ($item.ReceivedTime -ge $StartDate -and $item.ReceivedTime -le $EndDate) { ... }
}

# NEW (fast): Let Outlook filter server-side
$filter = "[ReceivedTime] >= '$startFilter' AND [ReceivedTime] <= '$endFilter'"
$restrictedItems = $items.Restrict($filter)
```

**Folder navigation:**
- Default folders: `$namespace.GetDefaultFolder([Microsoft.Office.Interop.Outlook.OlDefaultFolders]::"olFolderName")`
- Custom folders: Search through `$namespace.Folders` collection

**Email filtering:**
- Items sorted by ReceivedTime: `$items.Sort("[ReceivedTime]", $true)`
- Date comparison on `$Item.ReceivedTime` (received) or `$Item.SentOn` (sent)
- Category exclusion checked against config's `exclude_categories`

## Development Workflow

### Initial Setup

1. **Extract emails**: Run `Export-DailyEmails.ps1` or `Backfill-2025-Emails.ps1`
2. **Convert to markdown**: Run `convert_to_gemini_format.py --batch-by month`
3. **Upload to Gemini**: Run `setup_gemini_rag.py --upload-all`
4. **Start the system**: Run `start-email-warehouse.bat` (launches API + dashboard)
5. **Query your data**: Use dashboard AI Query tab or `setup_gemini_rag.py --query "your question"`

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

**Recommended additional fields** (see IMPROVEMENT_PLAN.md for full list):
```powershell
bcc = @()
read_status = $Item.UnRead
flag_status = $Item.FlagStatus
message_size = $Item.Size
body_html = $Item.HTMLBody
sensitivity = $Item.Sensitivity
```

### Adding Custom API Methods

Extend `api/email_knowledge_api.py`:
```python
class EmailKnowledgeAPI:
    def get_quarterly_summary(self, vendor, quarter):
        """Custom method for quarterly reports"""
        query = f"Summarize {vendor} interactions in Q{quarter}"
        return self._query_rag(query, max_chunks=20)
```

### Dashboard View Customization

**Dashboard v2** (`dashboard-v2/app.js`):
- Add view: Create new tab in HTML + render method in JavaScript
- Modify charts: Edit Chart.js configurations
- Change styling: Update `styles.css` CSS variables

**Dashboard v1** (`dashboard/app.js`):
- Add view: Create `render[ViewName]View()` method + HTML section in `index.html`
- Modify filters: Update `getFilteredEmails()` or `applyFilter()` switch statements
- Change UI: Edit `styles.css` (uses CSS Grid for responsive layout)

### Improving RAG Query Quality

**Adjust search sensitivity** (setup_gemini_rag.py:200+):
- Modify keyword extraction logic
- Tune number of chunks sent to Gemini (`max_chunks` parameter)
- Adjust markdown file filtering strategy

**Optimize markdown format** (convert_to_gemini_format.py):
- Enhance metadata headers
- Add more context (e.g., thread information)
- Include attachment summaries

## Data Flow and Dependencies

### Full Pipeline (Recommended)
1. `Export-DailyEmails.ps1` or `Backfill-2025-Emails.ps1` → creates `warehouse/daily/*.json`
2. `convert_to_gemini_format.py` → reads daily JSON → creates `warehouse/gemini/*.md`
3. `setup_gemini_rag.py --upload-all` → uploads markdown to Gemini → updates `config/gemini_config.json`
4. **Runtime servers:**
   - `api/rag_api.py` (Flask) → provides REST API for live RAG queries
   - `dashboard-v2/index.html` (via http.server) → displays data + live RAG interface
5. **Query options:**
   - Dashboard AI Query tab → calls Flask API → Gemini RAG
   - `setup_gemini_rag.py --query` → direct Gemini RAG query
   - `api/email_knowledge_api.py` → Python integration for WasteWise

### Optional Legacy Pipeline
1. `Export-DailyEmails.ps1` → creates `warehouse/daily/*.json`
2. `aggregate_threads.py` → reads daily JSON → creates `warehouse/threads/threads_current.json`
3. `generate_summary.py` → reads daily JSON + threads → creates `warehouse/summaries/*.md`
4. `dashboard/index.html` → displays data (no RAG)

### Configuration Dependencies

**settings.json** (legacy - for thread aggregation):
- Used by: `aggregate_threads.py`, `generate_summary.py`
- Contains: Project detection rules, retention settings

**gemini_config.json** (RAG system):
- Used by: `setup_gemini_rag.py`, `api/email_knowledge_api.py`
- Contains: Uploaded file URIs, store metadata
- Auto-generated when uploading files to Gemini

## Logging and Troubleshooting

### Log Files
- **Export logs:** `logs/export.log` (per-execution, created by Export-DailyEmails.ps1)
- **Daily sync logs:** `logs/daily-sync.log` (created by Run-DailySync.ps1) - **RECOMMENDED**
- **Scheduled task logs (legacy):** `logs/scheduled-export.log` (created by old wrapper script)
- **API logs:** Console output when running Flask API (visible in PowerShell window)

### Common Issues

**PowerShell Scripts Won't Run:**
- Execute: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

**Outlook COM Errors:**
- Ensure Outlook Desktop is running before executing export
- Close and reopen Outlook if extraction hangs

**Python Dependencies:**
```bash
pip install google-generativeai flask flask-cors
```

**API/Gemini Issues:**
- Set environment variable: `set GOOGLE_API_KEY=your_key` (Windows)
- Test API: `curl http://localhost:5000/api/health`

**Dashboard Issues:**
- **CORS errors:** Use local server (`python -m http.server 8000`) instead of opening HTML directly
- **RAG queries not working:** Ensure Flask API is running on port 5000
- **No emails showing:** Check `warehouse/daily/` folder has JSON files

**Port Conflicts:**
- If port 5000 or 8000 is in use, kill the process or change ports in scripts

## Windows Task Scheduler Integration

### Recommended: Daily Sync Automation (RAG-Focused)

`Setup-DailySync.ps1` creates a modern scheduled task focused on RAG updates:

**Created Components:**
1. **Wrapper script:** `scripts/Run-DailySync.ps1` (export → convert → upload to RAG)
2. **Scheduled task:** "Email Warehouse Daily Sync" runs at configured time
3. **Task settings:** AllowStartIfOnBatteries, StartWhenAvailable, RunOnlyIfNetworkAvailable:$false

**Execution Flow:**
1. `Export-DailyEmails.ps1` - Export today's emails from Outlook
2. `convert_to_gemini_format.py` - Convert today's emails to markdown
3. `setup_gemini_rag.py --upload-all` - Upload to Gemini RAG

**Logs:** `logs/daily-sync.log` with timestamps

**Setup:**
```powershell
cd scripts
.\Setup-DailySync.ps1              # Default: 08:00 AM daily
.\Setup-DailySync.ps1 -RunTime "07:00"  # Custom time
```

**Test manually:**
```powershell
.\Run-DailySync.ps1  # Check logs/daily-sync.log for results
```

### Legacy: Full Pipeline Automation

`Setup-ScheduledTask.ps1` creates the original automation (includes thread aggregation):

**Wrapper script:** `scripts/Run-DailyExport.ps1`

**Execution Flow:**
1. Export-DailyEmails.ps1
2. aggregate_threads.py (if Python available) - optional
3. generate_summary.py (if Python available) - optional
4. convert_to_gemini_format.py (if configured)
5. setup_gemini_rag.py --upload-all (if configured)

**Logs:** `scheduled-export.log` with timestamps

## Performance Benchmarks

**Email Extraction:**
- Old method: 2-3 minutes per 1,000 emails
- New method (Restrict filtering): ~3 seconds per day
- Full 2025 backfill (337 days): 17 minutes

**Markdown Conversion:**
- ~1-2 seconds per monthly batch
- Full 2025 conversion: <30 seconds

**Gemini RAG:**
- Upload: ~3-5 seconds per batch
- Query: 3-6 seconds (keyword search + AI generation)
- Cost: ~$0.001-0.003 per query

**Dashboard:**
- Load time: ~1-2 seconds for 1,182 emails
- Chart rendering: <500ms per chart
- Search: Real-time (client-side filtering)

## Common Use Cases

### 1. Daily Email Monitoring
```powershell
# RECOMMENDED: All-in-one startup (launches API + dashboard)
.\start-email-warehouse.bat

# OR: Manual workflow
cd scripts
.\Export-DailyEmails.ps1
python convert_to_gemini_format.py --batch-by month
python setup_gemini_rag.py --upload-all

# Start servers manually
cd api
.\start_rag_api.bat  # Terminal 1
cd dashboard-v2
python -m http.server 8000  # Terminal 2
```

### 2. Historical Analysis
```bash
# Query vendor history
python setup_gemini_rag.py --query "What's our history with Waste Management?"

# Or use API in your code
from api.email_knowledge_api import EmailKnowledgeAPI
kb = EmailKnowledgeAPI()
insights = kb.get_vendor_insights("Waste Management")
```

### 3. Invoice Processing Integration
```python
# In your invoice system
from api.email_knowledge_api import EmailKnowledgeAPI

def process_invoice(invoice):
    kb = EmailKnowledgeAPI(gemini_api_key)
    similar = kb.get_similar_invoices({
        'vendor': invoice['vendor'],
        'property': invoice['property'],
        'issue_type': 'contamination'
    })
    return similar['recommendations']
```

### 4. Bulk Backfill
```powershell
# Extract all of 2025
.\Backfill-2025-Emails.ps1 -StartDate "2025-01-01"

# Resume if interrupted
.\Backfill-2025-Emails.ps1 -StartDate "2025-01-01" -SkipExisting
```

## Key Files Reference

### Startup Scripts (Root)
- `start-email-warehouse.bat` - **RECOMMENDED** all-in-one startup (API + dashboard)

### PowerShell Scripts (scripts/)
- `Export-DailyEmails.ps1` - Daily email extraction (line 174: Export-EmailItem function)
- `Backfill-2025-Emails.ps1` - Bulk historical extraction with resume capability
- `Setup-DailySync.ps1` - **RECOMMENDED** automated daily sync setup (RAG-focused)
- `Run-DailySync.ps1` - Daily sync wrapper (export → convert → upload)
- `Setup-ScheduledTask.ps1` - Legacy automated task scheduling (full pipeline)
- `Find-All-Email-Stores.ps1` - Discover available email stores
- `Count-Emails-2025.ps1` - Count emails in default folders
- `Count-Emails-2025-All-Stores.ps1` - Count emails across all stores

### Python Scripts (scripts/)
- `convert_to_gemini_format.py` - JSON → Markdown conversion for RAG
- `setup_gemini_rag.py` - Gemini RAG management and queries (line 34: GeminiRAGManager class)
- `aggregate_threads.py` - Thread aggregation (line 84: project detection) - **Legacy**
- `generate_summary.py` - Daily summaries (line 106: action items, line 242: project detection) - **Legacy**

### API Layer (api/)
- `rag_api.py` - **NEW** Flask REST API server for live dashboard queries
- `start_rag_api.bat` - Quick launcher for Flask API
- `test_api.py` - API testing script
- `email_knowledge_api.py` - Python API class for integration (WasteWise)
- `integration_examples.py` - Working examples for WasteWise integration
- `README.md` - Complete integration guide

### Dashboards
- `dashboard-v2/` - **RECOMMENDED** modern dashboard with live RAG, analytics, charts
- `dashboard/` - Original dashboard with basic views (legacy, no live RAG)

### Configuration (config/)
- `settings.json` - Project detection rules, retention settings (for legacy aggregation)
- `gemini_config.json` - RAG file URIs, store metadata (auto-generated)

### Documentation
- `CLAUDE.md` - **This file** - Complete architecture and development guide
- `README.md` - Project overview and quick start
- `QUICK_START.md` - One-page quick start guide
- `IMPROVEMENT_PLAN.md` - Future enhancement ideas

## Important Constraints

- **Outlook Desktop Required**: Must have Outlook Desktop installed and running for COM extraction
- **Windows Only**: PowerShell COM automation requires Windows
- **Gemini API**: Requires Google AI API key and internet connection for RAG features
- **Python Dependencies**:
  - Python 3.8+ required
  - `pip install google-generativeai` - For Gemini RAG
  - `pip install flask flask-cors` - For live dashboard API
- **Browser**: Modern browser (Chrome, Firefox, Safari, Edge) for dashboard
- **Ports**: 5000 (API), 8000 (dashboard) must be available

## Known Limitations & Improvement Opportunities

See `IMPROVEMENT_PLAN.md` for comprehensive analysis. Key areas:

1. **Email Coverage**: Currently only scans Inbox + Sent Items - consider adding Archive, Deleted Items, custom folders
2. **Additional Fields**: Can add 14+ more fields (bcc, read_status, flag_status, etc.) - see IMPROVEMENT_PLAN.md:39
3. **Dashboard Enhancements**: Network graphs, entity profiles, advanced filtering - see IMPROVEMENT_PLAN.md:59
4. **Entity Extraction**: Auto-detect vendors, properties, amounts, dates from email content
5. ~~**Backend API**: Add Flask/FastAPI backend for live RAG queries in dashboard~~ ✅ **COMPLETED** - Flask API implemented
