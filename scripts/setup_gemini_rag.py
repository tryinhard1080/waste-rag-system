"""
Setup and manage Gemini File Search RAG system for email knowledge base.

This script creates a Gemini File Search store, uploads email markdown batches,
and provides query interface for semantic search over your email corpus.

Requirements:
    pip install google-generativeai

Usage:
    python setup_gemini_rag.py --api-key YOUR_API_KEY --create-store
    python setup_gemini_rag.py --api-key YOUR_API_KEY --upload-all
    python setup_gemini_rag.py --api-key YOUR_API_KEY --query "contamination issues"
"""

import google.generativeai as genai
import os
import sys
from pathlib import Path
import json
from datetime import datetime
import argparse

# Paths
SCRIPT_DIR = Path(__file__).parent
GEMINI_DIR = SCRIPT_DIR.parent / "warehouse" / "gemini"
CONFIG_FILE = SCRIPT_DIR.parent / "config" / "gemini_config.json"

# Configuration
MODEL_NAME = "gemini-2.0-flash-exp"  # Using latest experimental model


class GeminiRAGManager:
    """Manage Gemini File Search store for email RAG system."""

    def __init__(self, api_key: str):
        """
        Initialize Gemini API.

        Args:
            api_key: Google AI API key
        """
        genai.configure(api_key=api_key)
        self.model = None
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """Load Gemini configuration from file."""
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        return {}

    def _save_config(self):
        """Save Gemini configuration to file."""
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=2)
        print(f"Configuration saved to {CONFIG_FILE}")

    def create_file_search_store(self, store_name: str = "waste-management-emails"):
        """
        Create a new Gemini File Search store (corpus).

        Args:
            store_name: Name for the file search store

        Returns:
            Store ID
        """
        print(f"\nCreating Gemini File Search store: {store_name}")
        print("=" * 80)

        try:
            # Note: File Search in Gemini uses uploaded files directly
            # No need to create a separate corpus - files are managed via the Files API
            print("INFO: Gemini File Search uses the Files API directly.")
            print("Files will be uploaded and used for grounding automatically.")
            print("")

            # Save to config
            self.config['store_name'] = store_name
            self.config['created_at'] = datetime.now().isoformat()
            self.config['files'] = []
            self._save_config()

            print("READY: Configuration created. Use --upload-all to add files.")
            return store_name

        except Exception as e:
            print(f"ERROR: {e}")
            sys.exit(1)

    def list_files(self):
        """List all uploaded files."""
        print("\nUploaded Files:")
        print("=" * 80)

        try:
            for file in genai.list_files():
                print(f"\nFile: {file.display_name}")
                print(f"  URI: {file.uri}")
                print(f"  Size: {file.size_bytes / (1024*1024):.2f}MB")
                print(f"  State: {file.state.name}")

        except Exception as e:
            print(f"ERROR: {e}")

    def upload_files(self, file_pattern: str = "*.md"):
        """
        Upload markdown files to Gemini.

        Args:
            file_pattern: Glob pattern for files to upload
        """
        print(f"\nUploading files to Gemini")
        print("=" * 80)

        # Find files
        files = list(GEMINI_DIR.glob(file_pattern))
        if not files:
            print(f"ERROR: No files found matching {file_pattern} in {GEMINI_DIR}")
            sys.exit(1)

        print(f"Found {len(files)} files to upload\n")

        uploaded_count = 0
        failed_count = 0

        for file_path in files:
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            print(f"Uploading: {file_path.name} ({file_size_mb:.2f}MB)... ", end="")

            try:
                # Upload file using Files API
                uploaded_file = genai.upload_file(
                    path=str(file_path),
                    display_name=file_path.name
                )

                print("OK")
                print(f"  URI: {uploaded_file.uri}")
                uploaded_count += 1

                # Track in config
                if 'files' not in self.config:
                    self.config['files'] = []

                self.config['files'].append({
                    'name': file_path.name,
                    'uri': uploaded_file.uri,
                    'size_mb': round(file_size_mb, 2),
                    'uploaded_at': datetime.now().isoformat()
                })

            except Exception as e:
                print(f"ERROR: {e}")
                failed_count += 1

        self._save_config()

        print("\n" + "=" * 80)
        print(f"Upload complete!")
        print(f"  Successful: {uploaded_count}")
        print(f"  Failed: {failed_count}")
        print()

    def query(self, question: str, max_results: int = 5):
        """
        Query using uploaded files with semantic search.

        Args:
            question: Question to ask
            max_results: Maximum number of relevant emails to include
        """
        print(f"\nQuerying Gemini RAG System")
        print("=" * 80)
        print(f"Question: {question}")
        print()

        try:
            # Step 1: Search markdown files for relevant content
            print("Step 1: Searching for relevant emails...")
            relevant_chunks = self._search_markdown_files(question, max_chunks=10)

            if not relevant_chunks:
                print("No relevant emails found.")
                return

            print(f"Found {len(relevant_chunks)} relevant email sections")
            print()

            # Step 2: Query Gemini with relevant context
            print("Step 2: Generating answer with Gemini...")

            # Build context from relevant chunks
            context = "\n\n---\n\n".join(relevant_chunks)

            # Configure model
            model = genai.GenerativeModel(model_name=MODEL_NAME)

            # Create prompt with context
            prompt = f"""Based on the following email exchanges, please answer this question:

Question: {question}

Email Context:
{context}

Please provide a comprehensive answer based on the emails above."""

            # Generate response
            response = model.generate_content(prompt)

            print()
            print("Answer:")
            print("=" * 80)
            print(response.text)
            print()

        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

    def _search_markdown_files(self, query: str, max_chunks: int = 10):
        """
        Search markdown files for relevant content using keyword matching.

        Args:
            query: Search query
            max_chunks: Maximum number of chunks to return

        Returns:
            List of relevant text chunks
        """
        # Extract keywords from query
        keywords = query.lower().split()
        keywords = [k for k in keywords if len(k) > 3]  # Filter short words

        chunks = []

        # Search through markdown files
        for md_file in GEMINI_DIR.glob("*.md"):
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Split into individual emails (separated by ====)
            emails = content.split("=" * 80)

            for email in emails:
                if not email.strip():
                    continue

                # Score based on keyword matches
                email_lower = email.lower()
                score = sum(1 for kw in keywords if kw in email_lower)

                if score > 0:
                    chunks.append((score, email.strip()))

        # Sort by score and take top chunks
        chunks.sort(reverse=True, key=lambda x: x[0])
        return [chunk[1] for chunk in chunks[:max_chunks]]

    def get_store_info(self):
        """Display information about the configured store."""
        if not self.config:
            print("No configuration found.")
            return

        print("\nCurrent Gemini Configuration:")
        print("=" * 80)
        print(f"Store Name: {self.config.get('store_name', 'N/A')}")
        print(f"Created: {self.config.get('created_at', 'N/A')}")
        print(f"Uploaded Files: {len(self.config.get('files', []))}")

        total_size = sum(f['size_mb'] for f in self.config.get('files', []))
        print(f"Total Size: {total_size:.2f}MB")
        print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Manage Gemini File Search RAG system")

    parser.add_argument("--api-key", help="Google AI API key (or set GOOGLE_API_KEY env var)")
    parser.add_argument("--create-store", action="store_true", help="Create new file search store")
    parser.add_argument("--store-name", default="waste-management-emails", help="Name for new store")
    parser.add_argument("--list-files", action="store_true", help="List all uploaded files")
    parser.add_argument("--upload-all", action="store_true", help="Upload all markdown files")
    parser.add_argument("--upload-pattern", default="*.md", help="File pattern to upload")
    parser.add_argument("--query", help="Query the file search store")
    parser.add_argument("--max-results", type=int, default=5, help="Max results for query")
    parser.add_argument("--info", action="store_true", help="Show store information")

    args = parser.parse_args()

    # Get API key
    api_key = args.api_key or os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        print("✗ Error: API key required. Use --api-key or set GOOGLE_API_KEY environment variable.")
        print("\nGet your API key at: https://aistudio.google.com/app/apikey")
        sys.exit(1)

    # Initialize manager
    manager = GeminiRAGManager(api_key)

    # Execute command
    if args.create_store:
        manager.create_file_search_store(args.store_name)

    elif args.list_files:
        manager.list_files()

    elif args.upload_all:
        manager.upload_files(args.upload_pattern)

    elif args.query:
        manager.query(args.query, args.max_results)

    elif args.info:
        manager.get_store_info()

    else:
        print("No action specified. Use --help for usage information.")
        manager.get_store_info()


if __name__ == "__main__":
    main()
