# Waste Management RAG System

A production-ready Retrieval-Augmented Generation (RAG) system for waste management using Google's Gemini File API. This system enables intelligent Q&A over your waste management documents with semantic search, automated testing, and comprehensive reporting.

[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.10+-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

## 🌟 Features

- **Intelligent Document Processing**: Automatic upload and indexing of PDF, TXT, HTML, MD, and CSV files
- **Semantic Search**: Context-aware question answering using Google Gemini 2.0 Flash
- **Comprehensive Testing**: Automated test suite for file upload, Q&A accuracy, coverage, and citations
- **Detailed Reporting**: Ingestion metrics, processing times, and success rates
- **Production Ready**: CI/CD workflows, error handling, and retry logic
- **Expert System Prompts**: Specialized waste management context for accurate responses

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [API Costs](#api-costs)
- [Troubleshooting](#troubleshooting)

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd waste-rag-system

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment
cp .env.example .env
# Add your GEMINI_API_KEY to .env

# 4. Run test upload (15 files)
python upload_test_run.py

# 5. Test Q&A
python test_qa.py

# 6. Start interactive session
python waste_rag.py
```

## 📦 Installation

### Prerequisites

- Python 3.10 or higher
- Google Gemini API key ([Get one here](https://aistudio.google.com/app/apikey))
- Git

### Setup

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API key:**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your Gemini API key:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

3. **Verify installation:**
   ```bash
   python -c "import google.generativeai as genai; print('✓ Installation successful')"
   ```

## ⚙️ Configuration

Edit `config.json` to customize your setup:

```json
{
  "file_sources": [
    {
      "name": "construction_development",
      "type": "directory",
      "path": "/path/to/your/documents",
      "recursive": true,
      "extensions": [".pdf", ".txt", ".html", ".md", ".csv"]
    }
  ],
  "store_name": "your-knowledge-base",
  "model": "gemini-2.0-flash-exp",
  "processing": {
    "batch_size": 10,
    "retry_attempts": 3
  }
}
```

### Supported File Types

| Type | Extensions | Support |
|------|------------|---------|
| PDF | `.pdf` | ✅ Full |
| Text | `.txt`, `.md`, `.html`, `.csv` | ✅ Full |
| Office | `.docx`, `.xlsx` | ❌ Not supported by Gemini |
| Code | `.py`, `.js`, `.json`, `.xml` | ✅ Full |

## 💻 Usage

### Command-Line Scripts

#### Test Upload (Recommended First Step)
```bash
python upload_test_run.py
```
Uploads 15 files for validation and testing.

#### Full Upload
```bash
python upload_from_config.py
```
Processes all files from `config.json` with detailed reporting.

#### Interactive Q&A
```bash
python waste_rag.py
```
Start an interactive question-answering session.

#### Quick Test
```bash
python test_qa.py
```
Run predefined test questions.

### Python API

```python
from waste_rag import WasteRAGSystem

# Initialize
rag = WasteRAGSystem()

# Create file tracking
rag.create_file_search_store("my-docs")

# Upload files
rag.upload_file("document.pdf")

# Initialize model
rag.initialize_model()

# Ask questions
answer = rag.ask_question("What are the waste disposal guidelines?")
print(answer)
```

### Example Questions

**Construction Waste:**
- "What are the main categories of construction waste?"
- "How should hazardous materials be handled on construction sites?"
- "What are the recycling requirements for construction debris?"

**Compliance:**
- "What documentation is required for waste disposal?"
- "What are the penalties for improper waste disposal?"
- "What training is required for waste management personnel?"

**Best Practices:**
- "What are best practices for reducing construction waste?"
- "How do you properly segregate waste on a construction site?"
- "How do you calculate waste diversion rates?"

## 🧪 Testing

### Run Full Test Suite

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

### Individual Test Suites

```bash
# File upload tests
pytest tests/test_file_upload.py -v

# Q&A accuracy tests
pytest tests/test_qa_accuracy.py -v

# Coverage tests
pytest tests/test_coverage.py -v

# Citation tests
pytest tests/test_citations.py -v
```

### Test Results (Latest Run)

✅ **Test Upload**: 8/15 files (53% - 7 .docx files skipped)
✅ **Processing Time**: 37 seconds (2.5s per file)
✅ **Storage Used**: 3.55 MB
✅ **Q&A Quality**: Detailed, contextual responses with proper citations

## 📁 Project Structure

```
waste-rag-system/
├── .github/
│   └── workflows/          # CI/CD workflows
│       ├── test.yml
│       └── lint.yml
├── tests/
│   ├── test_file_upload.py
│   ├── test_qa_accuracy.py
│   ├── test_coverage.py
│   ├── test_citations.py
│   └── golden_qa.json      # Golden Q&A dataset
├── logs/                    # Processing logs (gitignored)
├── waste_documents/         # Local documents folder
├── config.json              # Configuration
├── waste_rag.py            # Core RAG system
├── upload_from_config.py   # Full upload script
├── upload_test_run.py      # Test upload script
├── test_qa.py              # Quick Q&A test
└── requirements.txt        # Dependencies
```

## 💰 API Costs

**Google Gemini API Pricing:**

| Operation | Cost | Notes |
|-----------|------|-------|
| File Upload | FREE | One-time per file |
| Storage | FREE | Up to quota limits |
| Query (Input) | $0.15 / 1M tokens | Context from files |
| Query (Output) | $0.60 / 1M tokens | Generated responses |

**Example Costs (348 PDF files):**
- Upload: FREE
- Storage: ~100-200 MB (FREE)
- 1000 queries: ~$1-5 depending on complexity

## 🔧 Troubleshooting

### Common Issues

**1. API Key Error**
```
ValueError: GEMINI_API_KEY not found
```
Solution: Ensure `.env` file exists with valid `GEMINI_API_KEY=...`

**2. Unsupported File Type**
```
[SKIP] Unsupported file type .docx
```
Solution: Gemini doesn't support .docx. Convert to PDF or use supported formats.

**3. File Processing Failed**
```
[FAIL] Failed to process: document.pdf
```
Solution: Check file size (< 100MB limit) and file isn't corrupted.

**4. No Answer Generated**
```
Model not initialized. Call initialize_model() first.
```
Solution: Run `rag.initialize_model()` after uploading files.

### Debug Mode

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📊 Reporting

After uploading, check:
- `logs/test_run_report.json` - Test upload results
- `logs/ingestion_report.json` - Full upload metrics

Example report:
```json
{
  "total_files": 15,
  "successful_uploads": 8,
  "success_rate": 53.3,
  "total_processing_time_seconds": 37.07,
  "total_storage_mb": 3.55,
  "extensions_processed": [".pdf"]
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- Built with [Google Gemini API](https://ai.google.dev/)
- Testing framework: [pytest](https://pytest.org/)
- Developed with [Claude Code](https://claude.ai/code)

---

**Generated with Claude Code** 🤖

For questions or issues, please open a GitHub issue.
