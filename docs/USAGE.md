# Usage Guide

Complete usage guide for the Waste RAG System.

## Table of Contents

- [Quick Start](#quick-start)
- [Upload Documents](#upload-documents)
- [Ask Questions](#ask-questions)
- [Python API](#python-api)
- [Advanced Usage](#advanced-usage)
- [Best Practices](#best-practices)

## Quick Start

### 1. Test Upload (Recommended First Step)

Upload a small batch of files to verify the system:

```bash
python upload_test_run.py
```

This will:
- Upload 15 files from your configured directory
- Generate a test report in `logs/test_run_report.json`
- Initialize the model
- Display success metrics

### 2. Test Q&A

Verify question answering works:

```bash
python test_qa.py
```

### 3. Interactive Session

Start an interactive Q&A session:

```bash
python waste_rag.py
```

Type your questions and get answers. Type `quit` to exit.

## Upload Documents

### Test Upload

For validation and testing:

```bash
python upload_test_run.py
```

**Uploads**: First 15 files found
**Creates**: Test file search store
**Report**: `logs/test_run_report.json`

### Full Upload

Upload all configured documents:

```bash
python upload_from_config.py
```

**Uploads**: All files from `config.json`
**Features**:
- Progress bar
- Retry logic
- Detailed reporting
- Category tracking

**Report**: `logs/ingestion_report.json`

### Upload Single File

```python
from waste_rag import WasteRAGSystem

rag = WasteRAGSystem()
rag.create_file_search_store("my-store")
rag.upload_file("document.pdf")
```

### Upload Directory

```python
rag.upload_directory("./waste_documents")
```

## Ask Questions

### Interactive Mode

```bash
python waste_rag.py
```

Example session:
```
Waste Management RAG System - Interactive Session
Type 'quit' to exit
--------------------------------------------------

Your question: What are the main types of construction waste?

Thinking...

Answer:
The main types of construction waste include:
1. Concrete and masonry
2. Wood and lumber
3. Metal (steel, aluminum)
4. Drywall and gypsum
5. Cardboard and packaging
[...]

Your question: quit
```

### Programmatic Q&A

```python
from waste_rag import WasteRAGSystem

# Initialize
rag = WasteRAGSystem()

# Load existing files
import google.generativeai as genai
files = genai.list_files()
rag.file_search_store = {'name': 'my-store', 'files': list(files)}
rag.initialize_model()

# Ask question
answer = rag.ask_question("How do I dispose of hazardous waste?")
print(answer)
```

### Batch Questions

```python
questions = [
    "What are waste classification methods?",
    "What safety equipment is required?",
    "What are the reporting requirements?"
]

for q in questions:
    answer = rag.ask_question(q)
    print(f"\nQ: {q}")
    print(f"A: {answer}\n")
```

## Python API

### Basic Workflow

```python
from waste_rag import WasteRAGSystem

# 1. Initialize
rag = WasteRAGSystem()

# 2. Create file tracking
rag.create_file_search_store("knowledge-base")

# 3. Upload files
rag.upload_file("document1.pdf")
rag.upload_file("document2.pdf")

# 4. Initialize model
rag.initialize_model()

# 5. Ask questions
answer = rag.ask_question("Your question here?")
```

### Advanced Workflow

```python
import os
from pathlib import Path
from waste_rag import WasteRAGSystem

# Initialize with custom config
rag = WasteRAGSystem()
rag.create_file_search_store("advanced-store")

# Upload with metadata
documents_folder = Path("./documents")
for pdf_file in documents_folder.glob("*.pdf"):
    file_size = os.path.getsize(pdf_file) / (1024 * 1024)  # MB

    if file_size < 100:  # Skip files > 100MB
        result = rag.upload_file(
            str(pdf_file),
            display_name=f"Doc-{pdf_file.stem}"
        )

        if result:
            print(f"✓ Uploaded: {pdf_file.name}")

# Initialize
rag.initialize_model()

# Ask with context
context = "Focus on construction waste management"
answer = rag.ask_question(f"{context}. What are the best practices?")
```

## Advanced Usage

### Custom System Prompt

Modify `waste_rag.py` to customize the system prompt:

```python
self.system_prompt = """You are a specialized assistant for [YOUR DOMAIN].

Focus on:
- [Custom requirement 1]
- [Custom requirement 2]

When answering:
1. [Custom instruction 1]
2. [Custom instruction 2]
"""
```

### File Management

#### List Uploaded Files

```python
import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

files = genai.list_files()
for f in files:
    print(f"{f.display_name} - {f.state.name}")
```

#### Delete Files

```python
import google.generativeai as genai

# Delete specific file
genai.delete_file("files/abc123")

# Delete all files
for f in genai.list_files():
    genai.delete_file(f.name)
    print(f"Deleted: {f.display_name}")
```

### Error Handling

```python
from waste_rag import WasteRAGSystem

rag = WasteRAGSystem()
rag.create_file_search_store("error-handling-demo")

try:
    result = rag.upload_file("document.pdf")

    if result:
        print("Upload successful")
    else:
        print("Upload failed - check file format and size")

except Exception as e:
    print(f"Error: {e}")
    # Handle error (log, retry, notify, etc.)
```

### Logging

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('waste_rag.log'),
        logging.StreamHandler()
    ]
)

# Use in your code
logger = logging.getLogger(__name__)
logger.info("Starting upload process")
```

## Configuration Patterns

### Multiple Document Sources

```json
{
  "file_sources": [
    {
      "name": "regulations",
      "path": "/path/to/regulations",
      "extensions": [".pdf"]
    },
    {
      "name": "guidelines",
      "path": "/path/to/guidelines",
      "extensions": [".pdf", ".txt"]
    },
    {
      "name": "case_studies",
      "path": "/path/to/studies",
      "extensions": [".pdf", ".md"]
    }
  ]
}
```

### Environment-Specific Config

```python
import os
import json

env = os.getenv('APP_ENV', 'development')
config_file = f'config.{env}.json'

with open(config_file, 'r') as f:
    config = json.load(f)
```

## Best Practices

### 1. File Organization

```
documents/
├── regulations/
│   ├── federal/
│   └── state/
├── guidelines/
│   ├── internal/
│   └── industry/
└── reports/
    ├── 2023/
    └── 2024/
```

### 2. Naming Conventions

- Use descriptive file names
- Include dates: `regulation_2024-01-15.pdf`
- Use categories: `guideline_hazmat_disposal.pdf`
- Avoid special characters

### 3. Upload Strategy

**For Small Collections (< 50 files)**:
- Upload all files at once
- Use `upload_from_config.py`

**For Large Collections (> 100 files)**:
- Start with test upload
- Upload in batches
- Monitor API usage

**For Very Large Collections (> 500 files)**:
- Upload by category
- Prioritize important documents
- Use rate limiting

### 4. Query Optimization

**Good Questions**:
- Specific: "What are the disposal requirements for asbestos?"
- Contextual: "How should construction sites handle hazardous waste?"
- Action-oriented: "What steps are needed for waste segregation?"

**Avoid**:
- Too vague: "Tell me about waste"
- Too broad: "Explain everything about waste management"
- Too specific: "What's on page 5 of document X?"

### 5. Error Recovery

```python
def upload_with_retry(rag, file_path, max_retries=3):
    """Upload with retry logic"""
    for attempt in range(max_retries):
        try:
            result = rag.upload_file(file_path)
            if result:
                return result
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise
    return None
```

## Performance Tips

### 1. Batch Operations

```python
# Upload multiple files efficiently
files_to_upload = list(Path("docs").glob("*.pdf"))

for i, file in enumerate(files_to_upload):
    rag.upload_file(str(file))

    # Rate limiting
    if (i + 1) % 10 == 0:
        time.sleep(1)  # Brief pause every 10 files
```

### 2. Caching Responses

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_answer(question):
    return rag.ask_question(question)
```

### 3. Async Operations

For high-volume operations, consider async patterns:

```python
import asyncio

async def upload_async(file_path):
    # Implement async upload
    pass

async def main():
    files = ["file1.pdf", "file2.pdf", "file3.pdf"]
    await asyncio.gather(*[upload_async(f) for f in files])
```

## Monitoring Usage

### Track API Calls

```python
class RAGWithTracking(WasteRAGSystem):
    def __init__(self):
        super().__init__()
        self.query_count = 0
        self.upload_count = 0

    def ask_question(self, question):
        self.query_count += 1
        return super().ask_question(question)

    def upload_file(self, file_path):
        self.upload_count += 1
        return super().upload_file(file_path)
```

### Generate Usage Reports

```python
report = {
    "date": datetime.now().isoformat(),
    "queries": rag.query_count,
    "uploads": rag.upload_count,
    "files_stored": len(rag.file_search_store['files'])
}

with open('usage_report.json', 'w') as f:
    json.dump(report, f, indent=2)
```

## Next Steps

- Review [TESTING.md](TESTING.md) for testing guidelines
- Check [FAQ.md](FAQ.md) for common questions
- See [SETUP.md](SETUP.md) for configuration details

---

**Happy Querying!** 🚀
