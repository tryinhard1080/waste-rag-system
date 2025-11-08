# Setup Guide

Complete setup instructions for the Waste RAG System.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Verification](#verification)
- [Common Issues](#common-issues)

## Prerequisites

### System Requirements

- **Python**: 3.10 or higher
- **RAM**: Minimum 4GB
- **Storage**: 500MB for code + space for your documents
- **Internet**: Required for Gemini API access

### Required Accounts

1. **Google Account** for Gemini API access
2. **GitHub Account** (optional, for version control)

## Installation

### Step 1: Clone or Download

```bash
# Option A: Clone from GitHub
git clone https://github.com/your-org/waste-rag-system.git
cd waste-rag-system

# Option B: Download ZIP and extract
# Navigate to the extracted folder
cd waste-rag-system
```

### Step 2: Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# Verify installation
pip list
```

Expected packages:
- google-generativeai (>=0.8.0)
- python-dotenv (>=1.0.0)
- tqdm (>=4.66.0)

### Step 4: Get Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key (starts with `AIzaSy...`)

### Step 5: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file (use any text editor)
# Windows: notepad .env
# Linux/Mac: nano .env
```

Add your API key:
```
GEMINI_API_KEY=AIzaSy...your-actual-key-here
```

**Important**: Never commit `.env` to version control!

## Configuration

### Configure Document Sources

Edit `config.json`:

```json
{
  "file_sources": [
    {
      "name": "my_documents",
      "type": "directory",
      "path": "C:/path/to/your/documents",  // Update this path
      "recursive": true,
      "extensions": [".pdf", ".txt", ".html", ".md", ".csv"]
    }
  ],
  "store_name": "my-knowledge-base",  // Customize store name
  "model": "gemini-2.0-flash-exp"
}
```

### Create Document Folders

```bash
# Create local documents folder
mkdir waste_documents

# Add your PDF/text files to this folder
# Or configure path to existing document folder in config.json
```

## Verification

### Test 1: Python Environment

```bash
python --version
# Should show: Python 3.10.x or higher
```

### Test 2: Dependencies

```bash
python -c "import google.generativeai as genai; print('OK: Gemini installed')"
python -c "from dotenv import load_dotenv; print('OK: dotenv installed')"
python -c "from tqdm import tqdm; print('OK: tqdm installed')"
```

### Test 3: API Key

```bash
python -c "
from dotenv import load_dotenv
import os
load_dotenv()
key = os.getenv('GEMINI_API_KEY')
if key and key.startswith('AIzaSy'):
    print('OK: API key configured')
else:
    print('ERROR: API key not found or invalid')
"
```

### Test 4: API Connection

```bash
python -c "
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

try:
    models = genai.list_models()
    print('OK: Connected to Gemini API')
except Exception as e:
    print(f'ERROR: {e}')
"
```

### Test 5: Test Upload

```bash
python upload_test_run.py
```

Expected output:
```
=== TEST RUN: Uploading 15 files for validation ===
...
[OK] Uploaded: document.pdf
...
[SUCCESS] System ready for testing!
```

## Common Issues

### Issue 1: Module Not Found

**Error**: `ModuleNotFoundError: No module named 'google.generativeai'`

**Solution**:
```bash
# Ensure virtual environment is activated
pip install -r requirements.txt
```

### Issue 2: API Key Error

**Error**: `ValueError: GEMINI_API_KEY not found`

**Solution**:
1. Check `.env` file exists
2. Verify format: `GEMINI_API_KEY=AIzaSy...`
3. No spaces around `=`
4. No quotes around the key

### Issue 3: Permission Denied

**Error**: `PermissionError` when reading documents

**Solution**:
- Check file permissions
- Run as administrator (Windows)
- Use `sudo` (Linux/Mac) if necessary

### Issue 4: Path Issues (Windows)

**Error**: Path not found with backslashes

**Solution**: Use forward slashes in `config.json`:
```json
"path": "C:/Users/name/Documents"  // ✓ Correct
"path": "C:\\Users\\name\\Documents"  // ✗ Incorrect
```

### Issue 5: Firewall/Proxy

**Error**: Connection timeout to Gemini API

**Solution**:
- Check firewall settings
- If behind corporate proxy, configure:
  ```bash
  export HTTP_PROXY=http://proxy:port
  export HTTPS_PROXY=http://proxy:port
  ```

## Next Steps

After successful setup:

1. **Test Upload**: `python upload_test_run.py`
2. **Full Upload**: `python upload_from_config.py`
3. **Interactive Q&A**: `python waste_rag.py`
4. **Read USAGE.md** for detailed usage instructions

## Getting Help

- Check [FAQ.md](FAQ.md) for common questions
- Review [TESTING.md](TESTING.md) for testing guides
- Open a GitHub issue for bugs
- Review Gemini API documentation: https://ai.google.dev/

---

**Setup complete!** 🎉
