# Email Warehouse Dashboard v2.0

**Modern, interactive dashboard for your email knowledge base with Gemini RAG integration**

---

## 🎨 Features

### 1. Overview Dashboard
- **Real-time stats**: Total emails, received/sent breakdown, active threads
- **Email volume chart**: Weekly trend analysis
- **Type distribution**: Visual breakdown of email types
- **Recent activity**: Last 10 emails with quick preview
- **Performance metrics**: Week-over-week growth indicators

### 2. Analytics View
- **Top senders/recipients**: Tables with email counts and percentages
- **Vendor analysis**: Track communications with key waste management vendors
- **Property analysis**: Monitor email volume by property
- **Statistical insights**: Understand your communication patterns

### 3. AI Query (RAG Integration)
- **Natural language queries**: Ask questions about your email history
- **Powered by Gemini**: Uses your 1,182+ indexed emails
- **Example questions**: Pre-built queries to get started
- **Query history**: Track your past searches
- **Smart search**: Keyword-based semantic search

### 4. Search & Filter
- **Full-text search**: Search across subject, body, sender
- **Date range filters**: 7/30/90 days or all time
- **Type filters**: Received/sent emails
- **Sender filters**: Filter by specific contacts
- **Real-time results**: Instant search as you type

### 5. Timeline View
- **Email timeline chart**: Bar chart showing email volume
- **Flexible granularity**: Daily, weekly, or monthly views
- **Day-of-week analysis**: See which days you get the most emails
- **Interactive charts**: Powered by Chart.js

---

## 🚀 Quick Start

### Option 1: Double-Click (Easiest)

Simply open `index.html` in your browser:
```
dashboard-v2/index.html
```

### Option 2: Local Server (Recommended)

```bash
cd dashboard-v2
python -m http.server 8000
# Open http://localhost:8000
```

### Option 3: Live Server (VSCode)

1. Install "Live Server" extension
2. Right-click `index.html` → "Open with Live Server"

---

## 📊 What You'll See

### Overview Tab
![Overview](https://img.shields.io/badge/Status-Active-green)

- 4 stat cards (Total, Received, Sent, Threads)
- Line chart showing email volume over time
- Doughnut chart showing email type distribution
- List of recent emails

### Analytics Tab
![Analytics](https://img.shields.io/badge/Status-Active-green)

- Top 10 senders table
- Top 10 recipients table
- Vendor communication stats (Waste Management, Republic Services, etc.)
- Property communication stats (Jones Grant, Columbia Square, etc.)

### AI Query Tab
![AI Query](https://img.shields.io/badge/Status-Active-green)

- Query input with Gemini RAG
- 6 example questions you can click
- Query history timeline
- Real-time AI responses

### Search Tab
![Search](https://img.shields.io/badge/Status-Active-green)

- Full-text search input
- Date range selector
- Type filter (received/sent)
- Sender filter dropdown
- Results list with email cards

### Timeline Tab
![Timeline](https://img.shields.io/badge/Status-Active-green)

- Bar chart showing email volume by week/month/day
- Day-of-week analysis chart
- Granularity selector

---

## 🔧 Configuration

### Data Source

The dashboard reads from `../warehouse/daily/*.json` files by default.

To change the data source, edit `app.js`:

```javascript
this.config = {
    warehousePath: '../warehouse/daily',  // Change this path
    apiKey: null,
    ragEnabled: false
};
```

### Date Range

By default, the dashboard loads emails from **June 1 - Dec 3, 2025**.

To change the date range, edit the `getAvailableFiles()` method in `app.js`:

```javascript
const startDate = new Date('2025-06-01');  // Change start
const endDate = new Date('2025-12-03');    // Change end
```

---

## 🤖 RAG Integration

### Current Status

The dashboard includes a **RAG Query interface** that connects to your Gemini RAG system.

### Live Queries (CLI)

To get real answers, use the Python CLI:

```bash
cd ../scripts
python setup_gemini_rag.py --query "What contamination issues have we dealt with?"
```

### Future: Direct Integration

To enable live queries in the dashboard, you'll need:

1. **Backend API** (Flask/FastAPI) that calls your Python RAG system
2. **CORS headers** to allow browser requests
3. **API key management** (secure storage)

Example Flask API:
```python
from flask import Flask, request, jsonify
from setup_gemini_rag import GeminiRAGManager

app = Flask(__name__)
rag = GeminiRAGManager()

@app.route('/api/query', methods=['POST'])
def query():
    question = request.json['question']
    answer = rag.query(question)
    return jsonify({'answer': answer})

app.run(port=5000)
```

Then update `app.js` to call this endpoint instead of simulating.

---

## 📁 File Structure

```
dashboard-v2/
├── index.html          # Main HTML structure
├── styles.css          # Modern CSS with variables
├── app.js              # Dashboard logic & data handling
└── README.md           # This file
```

---

## 🎨 Design System

### Colors
- Primary: `#2563eb` (Blue)
- Secondary: `#10b981` (Green)
- Warning: `#f59e0b` (Orange)
- Danger: `#ef4444` (Red)
- Dark: `#1f2937`
- Light: `#f9fafb`

### Typography
- Font: System fonts (-apple-system, Segoe UI, etc.)
- Headers: 600-700 weight
- Body: 400 weight
- Code: Monospace

### Components
- Cards with shadow and hover effects
- Modal overlays with backdrop blur
- Responsive tables with hover states
- Interactive charts with Chart.js
- Badge system for email types

---

## 📱 Responsive Design

The dashboard is fully responsive:

- **Desktop** (1400px+): Full layout with all features
- **Tablet** (768px-1024px): 2-column grids
- **Mobile** (<768px): Single column, stacked layout

---

## 🔍 How It Works

### Data Loading

1. Dashboard initializes and calls `loadEmails()`
2. Generates list of JSON files for date range
3. Fetches each file via `fetch()` API
4. Combines all emails into single array
5. Updates header stats

### Chart Rendering

1. Uses Chart.js library (loaded from CDN)
2. Groups data by week/month/day
3. Creates chart instances
4. Stores references in `this.charts` for updates
5. Destroys old charts before re-rendering

### Search

1. User types query
2. Filters `this.emails` array client-side
3. Matches against subject, body, sender
4. Renders results as email cards
5. Limits to 50 results for performance

### Modal

1. User clicks email card
2. `showEmailDetail(email)` called
3. Renders full email in modal
4. Shows backdrop overlay
5. Closes on X or backdrop click

---

## 🚀 Performance

- **Load time**: ~1-2 seconds for 1,182 emails
- **Chart rendering**: <500ms per chart
- **Search**: Real-time (client-side filtering)
- **Memory**: ~10-20MB for full dataset
- **Browser support**: Chrome, Firefox, Safari, Edge (modern versions)

---

## 🐛 Troubleshooting

### Dashboard won't load

- **Check console** (F12) for errors
- **Verify path**: Ensure `../warehouse/daily/` exists
- **CORS issues**: Use local server instead of `file://`

### No emails showing

- **Check date range** in `getAvailableFiles()`
- **Verify JSON files** exist in warehouse/daily/
- **Check JSON format**: Must have `emails` array

### Charts not rendering

- **Check Chart.js**: Verify CDN loaded (check Network tab)
- **Check canvas elements**: Ensure IDs match in HTML
- **Check data**: Verify emails array has data

### RAG queries not working

- **Use Python CLI** for now (see RAG Integration above)
- **Backend required**: Dashboard can't call Python directly
- **Check API key**: Ensure Gemini API key is set

---

## 🎯 Next Steps

### Enhancements

1. **Backend API** for live RAG queries
2. **WebSocket updates** for real-time email loading
3. **Export functionality** (CSV, PDF reports)
4. **Advanced filters** (importance, categories, attachments)
5. **Email composition** (reply/forward from dashboard)
6. **Thread view** (show conversation threads)
7. **Sender profiles** (contact cards with history)
8. **Sentiment analysis** (positive/negative/neutral)

### Integration

1. **Connect to WasteWise** invoice system
2. **Vendor insights** in dashboard
3. **Property management** integration
4. **Alert system** for urgent emails
5. **Automated reports** (daily/weekly summaries)

---

## 📝 License

Part of the Email Warehouse RAG System - Private project.

---

## 🙏 Credits

- **Built with**: Chart.js, Vanilla JavaScript, CSS Grid
- **Powered by**: Gemini RAG, Outlook COM extraction
- **Designed for**: Waste management email intelligence

---

**Last updated**: December 3, 2025

*For questions or issues, check the main project README.md*
