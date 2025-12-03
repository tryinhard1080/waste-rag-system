# Email Warehouse - Quick Start Guide

## 🚀 One-Click Startup

**Double-click this file:**
```
start-email-warehouse.bat
```

This will:
1. ✅ Start the RAG API Server (port 5000)
2. ✅ Start the Dashboard Server (port 8000)
3. ✅ Open the dashboard in your browser

**Two PowerShell windows will open - keep both running!**

---

## 📊 Using the Dashboard

Once the dashboard opens at `http://localhost:8000`:

### Main Features

1. **Overview Tab** - Email statistics and charts
2. **Analytics Tab** - Top senders, recipients, vendor analysis
3. **AI Query Tab** - 🎯 **Ask questions about your emails!**
4. **Search Tab** - Full-text search
5. **Timeline Tab** - Email volume trends

### Try These AI Queries

Click the "AI Query" tab and try:

```
What are the main waste management issues from November?
Who are my key contacts at Waste Management?
Summarize recent contamination fee discussions
What properties have had billing disputes?
What vendors do I communicate with most?
```

---

## 📅 Daily Automated Sync

### One-Time Setup (Run as Administrator)

```powershell
cd scripts
.\Setup-DailySync.ps1
```

This creates a scheduled task that runs daily at 8:00 AM to:
- Export today's emails from Outlook
- Convert to Gemini format
- Upload to RAG system

**To change the time:**
```powershell
.\Setup-DailySync.ps1 -RunTime "07:00"
```

---

## 🛑 Stopping the System

**Method 1:** Close both PowerShell windows that opened

**Method 2:** Press Ctrl+C in each PowerShell window

---

## 📁 Key Locations

- **Dashboard**: `dashboard-v2/index.html`
- **Email Data**: `warehouse/daily/`
- **RAG Batches**: `warehouse/gemini/`
- **Logs**: `logs/`
- **Configuration**: `config/`

---

## 🔧 Manual Operation

If you prefer manual control:

### Start RAG API Only
```powershell
cd api
.\start_rag_api.bat
```

### Start Dashboard Only
```powershell
cd dashboard-v2
python -m http.server 8000
# Then open: http://localhost:8000
```

### Run Daily Sync Manually
```powershell
cd scripts
.\Run-DailySync.ps1
```

---

## 📚 Current Data

- **Total Emails**: 897 (June - December 2025)
- **November Emails**: 846
- **RAG Batches**: 8 batches (25+ MB)
- **Query Speed**: 3-6 seconds

---

## ❓ Troubleshooting

**Dashboard won't load emails:**
- Make sure you're accessing via `http://localhost:8000` (not file://)
- Check that both servers are running

**RAG queries not working:**
- Verify the RAG API server is running (port 5000)
- Check the PowerShell window for errors

**No emails showing:**
- Run the export: `cd scripts; .\Export-DailyEmails.ps1`
- Check `warehouse/daily/` folder has JSON files

---

## 🎯 Next Steps

1. ✅ Double-click `start-email-warehouse.bat`
2. ✅ Try some AI queries in the dashboard
3. ✅ Set up daily automated sync (run as admin)
4. ✅ Enjoy your AI-powered email search!

---

**For detailed documentation, see:**
- `CLAUDE.md` - Full system architecture
- `README.md` - Project overview
- `api/README.md` - API integration guide
- `dashboard-v2/README.md` - Dashboard features

---

*Last updated: December 3, 2025*
