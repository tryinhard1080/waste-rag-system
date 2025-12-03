# Frequently Asked Questions (FAQ)

Common questions and answers about the Waste RAG System.

## General Questions

### What is RAG?

**RAG (Retrieval-Augmented Generation)** is an AI technique that combines:
1. **Retrieval**: Finding relevant information from documents
2. **Generation**: Creating natural language answers using that information

This ensures answers are grounded in your actual documents, not hallucinated.

### What does this system do?

This system:
- Uploads your waste management documents to Google Gemini
- Indexes them for semantic search
- Answers questions using content from those documents
- Provides citations and sources

### What file types are supported?

**Fully Supported**:
- PDF (`.pdf`)
- Text (`.txt`)
- HTML (`.html`)
- Markdown (`.md`)
- CSV (`.csv`)
- Code files (`.py`, `.js`, `.json`, `.xml`)

**Not Supported** (by Gemini API):
- Word documents (`.docx`, `.doc`)
- Excel spreadsheets (`.xlsx`, `.xls`)
- PowerPoint (`.pptx`)

**Workaround**: Convert Office files to PDF before uploading.

### Is my data secure?

- Documents are uploaded to Google's Gemini API
- Subject to [Google's privacy policy](https://policies.google.com/privacy)
- Use appropriate API keys and access controls
- Consider data sensitivity before uploading
- Review Google AI's [data usage policies](https://ai.google.dev/gemini-api/terms)

## Setup & Installation

### Do I need a paid API key?

No. Google Gemini offers a **free tier** with generous limits:
- File uploads: FREE
- Storage: FREE (up to quota)
- Queries: FREE tier available

Check current limits: https://ai.google.dev/pricing

### What Python version do I need?

**Python 3.10 or higher** is required.

Check your version:
```bash
python --version
```

### Can I use this on Windows/Mac/Linux?

Yes! The system works on all major operating systems:
- ✅ Windows 10/11
- ✅ macOS (Intel and Apple Silicon)
- ✅ Linux (Ubuntu, Debian, etc.)

### Do I need a GPU?

No. All processing happens in the cloud via Gemini API.

## Usage Questions

### How many files can I upload?

Technical limits:
- **File size**: Max 100MB per file
- **Total storage**: Depends on your API tier
- **File count**: No hard limit (practical limit ~1000s)

Recommendations:
- Start small (10-50 files)
- Test quality before uploading everything
- Monitor API quotas

### How long does upload take?

Average times (from testing):
- **Per file**: ~2-5 seconds
- **50 PDFs**: ~2-5 minutes
- **500 PDFs**: ~20-40 minutes

Factors affecting speed:
- File size
- Internet connection
- API rate limits
- Document complexity

### Why are .docx files skipped?

**Gemini API doesn't support .docx format**.

Solutions:
1. **Convert to PDF**: Use Microsoft Word, Google Docs, or online converters
2. **Save as TXT**: For text-only content
3. **Use LibreOffice**: Batch convert with command line

### Can I upload files from different folders?

Yes! Configure multiple sources in `config.json`:

```json
{
  "file_sources": [
    {
      "name": "folder1",
      "path": "/path/to/folder1"
    },
    {
      "name": "folder2",
      "path": "/path/to/folder2"
    }
  ]
}
```

### How do I update documents?

**Option 1**: Delete and re-upload
```python
import google.generativeai as genai

# Delete old file
genai.delete_file("files/old_file_id")

# Upload new version
rag.upload_file("updated_document.pdf")
```

**Option 2**: Upload with new name
- Upload updated file with version suffix
- Original remains for historical reference

### Can I use this for non-waste documents?

**Yes!** While designed for waste management, the system works for any domain:

1. Update the system prompt in `waste_rag.py`
2. Change store name in `config.json`
3. Upload your documents
4. Ask domain-specific questions

Examples:
- Legal documents
- Medical records
- Technical manuals
- Policy documents

## Technical Questions

### What model does this use?

**gemini-2.0-flash-exp** by default.

To change, edit `waste_rag.py`:
```python
self.model_name = "gemini-2.5-pro"  # Or other Gemini model
```

Available models: https://ai.google.dev/models

### How does semantic search work?

1. Documents are split into chunks
2. Each chunk gets an embedding (vector representation)
3. When you ask a question, it's converted to an embedding
4. Similar chunks are retrieved
5. Gemini generates an answer using those chunks

### Can I see what documents were used?

The system attempts to show citations when available. Check the `ask_question()` method in `waste_rag.py` for grounding metadata.

Future enhancement: Explicit source tracking and citation display.

### What if my question has no answer?

The system should indicate uncertainty. If it doesn't:

1. **Ask more specific questions**
2. **Check if relevant documents are uploaded**
3. **Review the system prompt** to encourage uncertainty acknowledgment

### How accurate are the answers?

Accuracy depends on:
- **Document quality**: Clear, well-structured documents
- **Document coverage**: Comprehensive information
- **Question specificity**: Targeted questions
- **Model limitations**: Current AI capabilities

Best practices:
- Verify critical information
- Cross-reference multiple sources
- Use as a starting point, not final authority

## Troubleshooting

### Upload fails with "Unsupported MIME type"

**Cause**: File type not supported by Gemini

**Solutions**:
1. Check file extension in `waste_rag.py` supported types
2. Convert to PDF
3. Use alternative format (TXT, HTML)

### "Model not initialized" error

**Cause**: Trying to ask questions before initialization

**Solution**:
```python
rag.create_file_search_store("store")
rag.upload_file("file.pdf")
rag.initialize_model()  # Don't forget this!
rag.ask_question("question?")
```

### Files upload but answers are generic

**Possible causes**:
1. Files not properly associated with model
2. Questions too vague
3. Documents don't contain relevant information

**Solutions**:
1. Verify files uploaded: `genai.list_files()`
2. Ask more specific questions
3. Check document content matches questions

### API rate limit errors

**Error**: `429 Too Many Requests`

**Solutions**:
1. Add delays between uploads:
   ```python
   import time
   time.sleep(1)  # Wait 1 second
   ```
2. Reduce batch size in config
3. Check API quotas: https://ai.google.dev/pricing

### Out of memory errors

**Cause**: Too many files or large files

**Solutions**:
1. Upload in smaller batches
2. Split very large PDFs
3. Increase system RAM
4. Use file size limits

## Cost & Performance

### How much does this cost?

**Google Gemini Pricing** (as of 2025):
- File upload: FREE
- File storage: FREE
- Query input: ~$0.15 per 1M tokens
- Query output: ~$0.60 per 1M tokens

**Estimated costs**:
- 100 files: FREE to upload
- 1000 queries: $1-10 depending on complexity

Check current pricing: https://ai.google.dev/pricing

### How can I reduce costs?

1. **Cache common queries**
2. **Limit file uploads** to essential documents
3. **Use concise questions**
4. **Batch similar questions**
5. **Monitor usage** with tracking

### Can I run this offline?

**No**. The system requires internet connection to:
- Upload files to Gemini API
- Process queries
- Generate responses

For offline needs, consider:
- Local RAG systems (LlamaIndex, LangChain)
- Self-hosted models (Ollama, GPT4All)

### How do I speed up uploads?

1. **Pre-filter files**: Only upload relevant documents
2. **Optimize file sizes**: Compress PDFs
3. **Parallel uploads**: Modify code for concurrent uploads
4. **Better internet**: Use faster connection
5. **Batch processing**: Group similar files

## Integration Questions

### Can I integrate this with my app?

**Yes!** The Python API can be integrated into:
- Web applications (Flask, Django, FastAPI)
- Desktop applications
- Command-line tools
- Automated workflows

Example FastAPI integration:
```python
from fastapi import FastAPI
from waste_rag import WasteRAGSystem

app = FastAPI()
rag = WasteRAGSystem()

@app.post("/ask")
def ask_question(question: str):
    answer = rag.ask_question(question)
    return {"answer": answer}
```

### Can I add a web interface?

Yes! Consider:
- **Streamlit**: Quick prototype
- **Gradio**: Interactive demos
- **FastAPI + React**: Production app
- **Django**: Full-stack application

### Can I use this in production?

**Yes, with considerations**:

✅ **Suitable for**:
- Internal tools
- Document search
- Knowledge bases
- Research assistance

⚠️ **Be careful with**:
- Critical decisions (verify answers)
- Sensitive data (review privacy)
- High availability needs (add redundancy)
- Regulatory compliance (check requirements)

**Production checklist**:
- [ ] Error handling
- [ ] Logging
- [ ] Monitoring
- [ ] Rate limiting
- [ ] Authentication
- [ ] Data backup
- [ ] Testing
- [ ] Documentation

## Contributing

### How can I contribute?

1. **Report bugs**: Open GitHub issues
2. **Suggest features**: Create feature requests
3. **Submit PRs**: Fix bugs or add features
4. **Improve docs**: Update guides
5. **Share examples**: Add use cases

### Where do I report bugs?

Open an issue on GitHub with:
- Description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Python version
- Error messages/logs

### Can I use this commercially?

Check the project license (MIT typically allows commercial use).

**Also consider**:
- Gemini API terms of service
- Data privacy requirements
- Your organization's policies

## Additional Resources

- **Gemini API Docs**: https://ai.google.dev/
- **Python Docs**: https://docs.python.org/
- **pytest Docs**: https://pytest.org/
- **RAG Concepts**: https://www.pinecone.io/learn/retrieval-augmented-generation/

## Still Have Questions?

- Check other documentation files (SETUP.md, USAGE.md, TESTING.md)
- Review the code comments
- Open a GitHub issue
- Contact the maintainers

---

**Updated**: 2025-11-08
