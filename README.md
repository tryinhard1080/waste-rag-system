# Waste Management RAG System

A Retrieval-Augmented Generation (RAG) system for waste management using Google's Gemini File Search API.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up API key:**
   - Get your Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Copy `.env.example` to `.env`
   - Add your API key to the `.env` file

3. **Prepare your waste documents:**
   - Create a `waste_documents` folder
   - Add your PDF, Word docs, Excel files, text files, etc.

## Usage

### Basic Usage

```python
from waste_rag import WasteRAGSystem

# Initialize system
rag_system = WasteRAGSystem()

# Create file search store
rag_system.create_file_search_store("my-waste-docs")

# Upload documents
rag_system.upload_directory("./waste_documents")

# Initialize model
rag_system.initialize_model()

# Ask questions
answer = rag_system.ask_question("How do I dispose of electronic waste?")
print(answer)
```

### Interactive Session

```bash
python waste_rag.py
```

## Supported File Types

- PDF documents
- Word documents (.docx)
- Excel spreadsheets (.xlsx)
- Text files (.txt)
- CSV files (.csv)
- JSON files (.json)
- Markdown files (.md)
- Code files (.py, .js)

## Example Questions

- "What are the regulations for hazardous waste disposal?"
- "How do I classify different types of plastic for recycling?"
- "What safety protocols should I follow for chemical waste?"
- "What are cost-effective waste reduction strategies for manufacturing?"
- "How do I properly dispose of electronic waste?"

## Features

- Semantic search through waste management documents
- Citations from source documents
- Expert-level guidance on waste management topics
- Support for multiple file types
- Interactive Q&A sessions