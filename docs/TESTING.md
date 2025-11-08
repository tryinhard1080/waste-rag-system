# Testing Guide

Comprehensive testing guide for the Waste RAG System.

## Table of Contents

- [Test Framework](#test-framework)
- [Running Tests](#running-tests)
- [Test Suites](#test-suites)
- [Golden Q&A Dataset](#golden-qa-dataset)
- [Writing Tests](#writing-tests)
- [CI/CD Integration](#cicd-integration)

## Test Framework

The project uses **pytest** for automated testing with the following structure:

```
tests/
├── __init__.py
├── test_file_upload.py    # File upload validation
├── test_qa_accuracy.py    # Q&A accuracy testing
├── test_coverage.py       # Document coverage metrics
├── test_citations.py      # Citation validation
└── golden_qa.json         # Expected Q&A pairs
```

## Running Tests

### Install Test Dependencies

```bash
pip install pytest pytest-asyncio pytest-cov
```

### Run All Tests

```bash
# Basic run
pytest tests/ -v

# With coverage report
pytest tests/ --cov=. --cov-report=html

# Stop on first failure
pytest tests/ -x

# Run specific test file
pytest tests/test_file_upload.py -v
```

### Run Individual Tests

```bash
# Single test function
pytest tests/test_file_upload.py::TestFileUpload::test_initialize_system -v

# Test class
pytest tests/test_file_upload.py::TestFileUpload -v

# Tests matching pattern
pytest tests/ -k "upload" -v
```

## Test Suites

### 1. File Upload Tests (`test_file_upload.py`)

Tests file upload functionality:

```bash
pytest tests/test_file_upload.py -v
```

**Tests**:
- ✓ System initialization
- ✓ File search store creation
- ✓ Single file upload (PDF)
- ✓ Single file upload (DOCX)
- ✓ Custom chunking configuration
- ✓ Upload without store (error handling)
- ✓ Model initialization

**Expected Results**:
- Most tests should pass
- Some may skip if test files not available

### 2. Q&A Accuracy Tests (`test_qa_accuracy.py`)

Tests answer quality against golden dataset:

```bash
pytest tests/test_qa_accuracy.py -v
```

**Requirements**:
- Files must be uploaded first (`python upload_test_run.py`)
- Golden Q&A dataset must exist (`tests/golden_qa.json`)

**Tests**:
- ✓ System readiness
- ✓ Golden Q&A accuracy (15 questions)
- ✓ Answer quality metrics
- ✓ Citation presence
- ✓ Response time (< 30 seconds)
- ✓ Different question types
- ✓ Hallucination check

**Success Criteria**:
- Keyword accuracy: ≥ 60%
- Concept coverage: ≥ 50%
- Response time: < 30 seconds

### 3. Coverage Tests (`test_coverage.py`)

Tests document ingestion coverage:

```bash
pytest tests/test_coverage.py -v
```

**Requirements**:
- Ingestion report must exist (`logs/ingestion_report.json`)
- Run after upload: `python upload_from_config.py`

**Tests**:
- ✓ All sources exist
- ✓ Files found
- ✓ Coverage percentage (≥ 95%)
- ✓ File extension coverage
- ✓ No critical failures
- ✓ Upload success rate (≥ 90%)
- ✓ File size distribution
- ✓ Directory structure valid

### 4. Citation Tests (`test_citations.py`)

Tests source tracking and citations:

```bash
pytest tests/test_citations.py -v
```

**Tests**:
- ✓ System prompt includes citation guidance
- ✓ Responses reference sources
- ✓ Specific document attribution
- ✓ Multiple source synthesis
- ✓ Citation accuracy
- ✓ Source diversity
- ✓ No citation when uncertain

## Golden Q&A Dataset

The golden dataset (`tests/golden_qa.json`) contains expected Q&A pairs for validation.

### Structure

```json
{
  "qa_pairs": [
    {
      "id": 1,
      "question": "What are the main categories of construction waste?",
      "expected_keywords": ["concrete", "wood", "metal", "drywall"],
      "expected_concepts": ["segregation", "recycling", "disposal"]
    }
  ],
  "evaluation_criteria": {
    "keyword_accuracy_threshold": 0.6,
    "concept_coverage_threshold": 0.5
  }
}
```

### Adding New Test Cases

1. Edit `tests/golden_qa.json`
2. Add new Q&A pair:

```json
{
  "id": 16,
  "question": "Your new question here?",
  "expected_keywords": ["keyword1", "keyword2"],
  "expected_concepts": ["concept1", "concept2"]
}
```

3. Run tests:

```bash
pytest tests/test_qa_accuracy.py -v
```

## Writing Tests

### Example Test

```python
import pytest
from waste_rag import WasteRAGSystem

class TestMyFeature:
    @pytest.fixture
    def rag_system(self):
        """Create RAG system for testing"""
        return WasteRAGSystem()

    def test_something(self, rag_system):
        """Test description"""
        # Arrange
        rag_system.create_file_search_store("test-store")

        # Act
        result = rag_system.upload_file("test.pdf")

        # Assert
        assert result is not None
```

### Best Practices

1. **Use fixtures** for setup/teardown
2. **Clear test names** describing what is tested
3. **AAA pattern**: Arrange, Act, Assert
4. **Skip tests** when dependencies missing:

```python
@pytest.mark.skipif(not os.path.exists("data"), reason="Data not available")
def test_with_data():
    pass
```

5. **Parametrize** for multiple inputs:

```python
@pytest.mark.parametrize("file_ext", [".pdf", ".txt", ".html"])
def test_file_types(file_ext):
    pass
```

## Test Reports

### Coverage Report

```bash
# Generate HTML coverage report
pytest tests/ --cov=. --cov-report=html

# Open report
# Windows: start htmlcov/index.html
# Linux/Mac: open htmlcov/index.html
```

### JUnit XML Report

```bash
# For CI/CD integration
pytest tests/ --junit-xml=test-results.xml
```

### Verbose Output

```bash
# Show test names and results
pytest tests/ -v

# Show print statements
pytest tests/ -s

# Both
pytest tests/ -vs
```

## CI/CD Integration

### GitHub Actions

Tests run automatically on push/PR via `.github/workflows/test.yml`:

```yaml
name: Run Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/ -v
```

### Local Pre-commit

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash
pytest tests/test_file_upload.py -v
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi
```

Make executable:
```bash
chmod +x .git/hooks/pre-commit
```

## Troubleshooting Tests

### Tests Skip Due to Missing Files

**Issue**: `pytest.skip: No files found`

**Solution**: Upload test files first:
```bash
python upload_test_run.py
```

### Tests Fail with API Errors

**Issue**: `HttpError 401: API key invalid`

**Solution**: Check `.env` file has valid `GEMINI_API_KEY`

### Tests Timeout

**Issue**: Tests hang or timeout

**Solution**:
- Increase timeout in test
- Check internet connection
- Verify API rate limits

### Import Errors

**Issue**: `ModuleNotFoundError`

**Solution**:
```bash
# Install in editable mode
pip install -e .
```

## Performance Testing

### Response Time Benchmark

```bash
pytest tests/test_qa_accuracy.py::TestQAAccuracy::test_response_time -v
```

### Load Testing

Create `tests/test_load.py`:

```python
import time
import pytest

def test_concurrent_queries(rag_system):
    """Test system under load"""
    questions = ["Question 1", "Question 2", "Question 3"]

    start = time.time()
    for q in questions:
        rag_system.ask_question(q)
    duration = time.time() - start

    assert duration < 60  # Should complete in 60 seconds
```

## Next Steps

- Review [USAGE.md](USAGE.md) for usage patterns
- Check [FAQ.md](FAQ.md) for common questions
- See [SETUP.md](SETUP.md) for configuration

---

**Happy Testing!** 🧪
