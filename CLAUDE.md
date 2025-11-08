# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Retrieval-Augmented Generation (RAG) system for waste management using Google's Gemini File Search API. The system ingests waste management documents and provides expert-level Q&A capabilities using semantic search.

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run interactive Q&A session (requires files already uploaded)
python waste_rag.py

# Upload files using CLI
python waste_rag_cli.py --directory "path/to/docs" --interactive
python waste_rag_cli.py --file "document.pdf"
python waste_rag_cli.py --pattern "**/*.pdf"

# Upload files using configuration
python upload_from_config.py

# List supported file formats
python waste_rag_cli.py --list-formats
```

## Architecture

### Core Components

1. **WasteRAGSystem** (`waste_rag.py`): Main class that handles:
   - Gemini API initialization with API key from `.env`
   - File search store creation and management
   - Document upload operations
   - Model initialization with specialized waste management prompt
   - Q&A generation through `generate_content()`

2. **File Ingestion Methods**:
   - **CLI Tool** (`waste_rag_cli.py`): Argparse-based interface for flexible file uploads
   - **Config-based** (`upload_from_config.py`): JSON configuration for batch operations
   - **Direct API**: Python interface through `WasteRAGSystem` class

3. **Configuration** (`config.json`): Defines:
   - File sources (directories, patterns, specific files)
   - Supported extensions
   - Store name and model selection

### Key Design Patterns

- **Single Responsibility**: Each script handles one primary task (ingestion, Q&A, configuration)
- **Environment-based Configuration**: API keys stored in `.env`, never in code
- **Stateful Session Management**: File search store persists across operations
- **Expert System Prompt**: Specialized system instruction in `WasteRAGSystem.__init__()` for waste management context

### API Integration Flow

1. Initialize `genai.configure()` with API key
2. Create file search store via `client.create_file_search_store()`
3. Upload files to store using `client.upload_to_file_search_store()`
4. Initialize GenerativeModel with file search tool pointing to store
5. Generate responses with RAG context from uploaded documents

## Important Constraints

- Maximum file size: 100 MB per file
- Storage limits: 1 GB - 1 TB based on user tier
- Model: Uses `gemini-2.5-pro` by default
- Supported file types: PDF, DOCX, XLSX, TXT, CSV, JSON, MD, and code files
- API key must be set in `.env` file (never commit this file)