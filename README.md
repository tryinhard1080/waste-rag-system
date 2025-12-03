# Email Warehouse RAG System

**AI-Powered Email Knowledge Base with Gemini RAG**

Transform your Outlook emails into a searchable knowledge base using Google's Gemini AI. Query historical communications, find similar scenarios, and get intelligent insights from years of email data.

---

## 🎯 What This Does

- **Extracts** emails from Outlook Desktop (via COM interface)
- **Converts** to markdown format optimized for AI search
- **Indexes** in Gemini RAG for semantic search
- **Queries** your email history using natural language
- **Integrates** with your existing systems via clean API

---

## 📊 Current Status

- **1,182 emails** indexed (June 2025 - December 2025)
- **7 monthly batches** (~19MB total)
- **Gemini RAG** fully operational
- **WasteWise integration** ready

---

## 🚀 Quick Start

### Prerequisites

```powershell
# PowerShell (Windows)
# Python 3.8+
pip install google-generativeai

# Get Gemini API key: https://aistudio.google.com/app/apikey
set GOOGLE_API_KEY=your_key_here
```

### Daily Email Export

```powershell
cd scripts
.\Export-DailyEmails.ps1
```

### Query Your Emails

```bash
python scripts/setup_gemini_rag.py --query "What contamination issues have we had?"
```

### Use in Your Code

```python
from api.email_knowledge_api import EmailKnowledgeAPI

kb = EmailKnowledgeAPI()
insights = kb.get_vendor_insights("Waste Management")
print(insights['summary'])
```

---

## 📁 Project Structure

```
email-warehouse/
├── scripts/
│   ├── Export-DailyEmails.ps1       # Daily Outlook extraction
│   ├── Backfill-2025-Emails.ps1     # Bulk historical export
│   ├── convert_to_gemini_format.py  # JSON → Markdown converter
│   └── setup_gemini_rag.py          # Gemini RAG manager
├── api/
│   ├── email_knowledge_api.py       # Python API for integration
│   ├── integration_examples.py      # Usage examples
│   └── README.md                    # Integration guide
├── warehouse/
│   ├── daily/                       # Daily JSON exports
│   └── gemini/                      # Markdown batches for RAG
├── dashboard-v2/                    # Interactive dashboard (WIP)
└── config/
    └── settings.json                # Configuration

```

---

## 🔧 Core Scripts

### 1. Export-DailyEmails.ps1

Ultra-fast Outlook email extraction (10-100x faster than previous methods).

```powershell
# Export today's emails
.\Export-DailyEmails.ps1

# Export date range
.\Export-DailyEmails.ps1 -StartDate "2025-11-01" -EndDate "2025-11-30"

# Export specific folders
.\Export-DailyEmails.ps1 -Folders @("Inbox", "Sent Items", "Archive")
```

**Key Features:**
- Uses Outlook Restrict filtering (blazing fast)
- Handles large mailboxes (50K+ emails)
- Automatic COM cleanup
- Progress logging

### 2. Backfill-2025-Emails.ps1

Bulk historical extraction with resume capability.

```powershell
# Extract all of 2025
.\Backfill-2025-Emails.ps1 -StartDate "2025-01-01"

# Resume after interruption
.\Backfill-2025-Emails.ps1 -StartDate "2025-01-01" -SkipExisting

# Process in 7-day chunks
.\Backfill-2025-Emails.ps1 -StartDate "2025-01-01" -ChunkSize 7
```

**Performance:**
- ~17 minutes for 337 days
- Day-by-day processing (clean JSON files)
- Automatic error recovery

### 3. convert_to_gemini_format.py

Converts JSON exports to Gemini-optimized markdown.

```bash
# Convert all emails, batch by month
python convert_to_gemini_format.py --batch-by month

# Convert specific date range
python convert_to_gemini_format.py --start-date 2025-06-01 --end-date 2025-12-01

# Single batch for all emails
python convert_to_gemini_format.py --batch-by all
```

**Output:**
- Markdown batches under 100MB each
- Clean metadata headers
- Thread-aware formatting

### 4. setup_gemini_rag.py

Manages Gemini RAG system and queries.

```bash
# Upload all batches to Gemini
python setup_gemini_rag.py --upload-all

# Query your knowledge base
python setup_gemini_rag.py --query "What vendors do I communicate with most?"

# List uploaded files
python setup_gemini_rag.py --list-files
```

---

## 🔌 Integration with WasteWise

The `api/` directory contains a clean integration layer for using email knowledge in your existing systems.

### Example: Invoice Processing

```python
from api.email_knowledge_api import EmailKnowledgeAPI

kb = EmailKnowledgeAPI(gemini_api_key="YOUR_KEY")

def process_invoice(invoice):
    # Get vendor history
    vendor_history = kb.get_vendor_insights(invoice['vendor'])

    # Find similar past invoices
    similar_cases = kb.get_similar_invoices({
        'vendor': invoice['vendor'],
        'property': invoice['property'],
        'amount': invoice['amount']
    })

    # Make informed decision
    return {
        'approve': has_precedent(similar_cases),
        'confidence': calculate_confidence(vendor_history),
        'notes': similar_cases['recommendations']
    }
```

See `api/README.md` for full integration guide.

---

## 📋 Common Use Cases

### 1. Vendor History Lookup

```bash
python setup_gemini_rag.py --query "What's our history with Waste Management?"
```

### 2. Issue Resolution Research

```bash
python setup_gemini_rag.py --query "How did we resolve contamination fees in the past?"
```

### 3. Contract Insights

```bash
python setup_gemini_rag.py --query "What negotiation tactics worked with Republic Services?"
```

### 4. Property Communication History

```bash
python setup_gemini_rag.py --query "All communications about Jones Grant property"
```

---

## 🛠️ Configuration

Edit `config/settings.json`:

```json
{
  "outlook": {
    "folders": ["Inbox", "Sent Items"],
    "exclude_categories": ["Personal", "Archive"]
  },
  "warehouse": {
    "days_to_retain": 365,
    "batch_size_mb": 95
  }
}
```

---

## 🔒 Security & Privacy

- **Local Processing:** All email extraction happens locally
- **Sensitive Data:** Raw JSON files NOT committed to git (see `.gitignore`)
- **Gemini Storage:** Only markdown summaries uploaded (no attachments)
- **API Keys:** Stored in environment variables, never in code

---

## 🚀 Performance Benchmarks

**Extraction Speed:**
- Old method: 2-3 minutes per 1,000 emails
- New method (Restrict): ~3 seconds per day
- Full 2025 backfill (337 days): 17 minutes

**RAG Query Speed:**
- Keyword search: <1 second
- Gemini generation: 2-5 seconds
- Total query time: 3-6 seconds

---

## 📈 Roadmap

- [x] Fast Outlook extraction
- [x] Bulk backfill with resume
- [x] Gemini RAG integration
- [x] Python API for WasteWise
- [ ] Interactive dashboard (in progress)
- [ ] Automated daily sync
- [ ] Claude Projects integration
- [ ] Advanced analytics (sender networks, topic clustering)

---

## 🤝 Contributing

This is a personal project for waste management email intelligence. Integration examples welcome!

---

## 📄 License

Private project - all rights reserved.

---

## 🆘 Support

**Issues:**
- Outlook COM errors: Ensure Outlook Desktop is running
- PowerShell execution policy: `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`
- Python dependencies: `pip install google-generativeai`

**Questions:**
- Check `api/README.md` for integration help
- Review `CLAUDE.md` for architecture details
- See example queries in `api/integration_examples.py`

---

## 📊 Stats

- **Total Emails Indexed:** 1,182
- **Date Range:** June 2025 - December 2025
- **Batches Created:** 7
- **Total Size:** 19MB
- **Query Response Time:** 3-6 seconds
- **Extraction Speed:** 17 minutes for 337 days

---

**Built with:**
- PowerShell (Outlook COM automation)
- Python (data processing, Gemini integration)
- Google Gemini AI (semantic search & RAG)

---

*Last updated: December 3, 2025*
