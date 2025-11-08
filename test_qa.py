#!/usr/bin/env python3
"""
Quick Q&A test script
"""

from waste_rag import WasteRAGSystem

def test_qa():
    # Initialize system
    rag = WasteRAGSystem()

    # Use the test store we created
    rag.file_search_store = {
        'name': 'advantage-waste-docs-test',
        'files': []  # Will be populated if files exist
    }

    # List existing files
    import google.generativeai as genai
    files = genai.list_files()

    print("Uploaded files:")
    for f in files:
        print(f"  - {f.display_name}")
        rag.file_search_store['files'].append(f)

    if not rag.file_search_store['files']:
        print("\nNo files found. Run upload_test_run.py first.")
        return

    # Initialize model
    rag.initialize_model()

    # Test questions
    questions = [
        "What are the key terms in consulting services agreements?",
        "What are the typical deliverables mentioned in service agreements?",
        "What are common payment terms in these contracts?",
    ]

    print("\n" + "="*70)
    print("Testing Q&A System")
    print("="*70)

    for i, question in enumerate(questions, 1):
        print(f"\n[Question {i}] {question}")
        print("-" * 70)

        answer = rag.ask_question(question)

        if answer:
            print(f"Answer: {answer[:500]}...")  # Show first 500 chars
        else:
            print("No answer generated.")

        print()

if __name__ == "__main__":
    test_qa()
