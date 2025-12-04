"""
Semantic RAG Module for WASTE Master Brain

This module provides true semantic search using Gemini embeddings,
replacing the primitive keyword matching in the original setup_gemini_rag.py.

Key Features:
- Uses Gemini text-embedding-004 (768 dimensions)
- Pre-computes and caches embeddings for fast queries
- Cosine similarity for semantic matching
- Falls back to keyword search if embeddings unavailable

Usage:
    python semantic_rag.py --build-embeddings  # First time setup
    python semantic_rag.py --query "contamination issues"
    python semantic_rag.py --query "What issues has Waste Management caused?" --keyword-only
"""

import google.generativeai as genai
import os
import sys
from pathlib import Path
import json
from datetime import datetime
import argparse
import hashlib
import math

# Paths
SCRIPT_DIR = Path(__file__).parent
GEMINI_DIR = SCRIPT_DIR.parent / "warehouse" / "gemini"
CONFIG_FILE = SCRIPT_DIR.parent / "config" / "gemini_config.json"
EMBEDDINGS_CACHE_FILE = SCRIPT_DIR.parent / "config" / "embeddings_cache.json"

# Configuration
MODEL_NAME = "gemini-2.0-flash-exp"  # For text generation
EMBEDDING_MODEL = "models/text-embedding-004"  # For semantic embeddings (768 dims)


def cosine_similarity(vec_a: list, vec_b: list) -> float:
    """
    Calculate cosine similarity between two vectors.

    Args:
        vec_a: First embedding vector
        vec_b: Second embedding vector

    Returns:
        Cosine similarity score (0-1, higher = more similar)
    """
    if not vec_a or not vec_b:
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (norm_a * norm_b)


class SemanticRAGManager:
    """
    Semantic RAG Manager using Gemini embeddings.

    This class provides true semantic search by:
    1. Pre-computing embeddings for all email chunks
    2. Caching embeddings to avoid re-computation
    3. Using cosine similarity for semantic matching
    4. Falling back to keyword search when needed
    """

    def __init__(self, api_key: str):
        """
        Initialize Gemini API and load caches.

        Args:
            api_key: Google AI API key
        """
        genai.configure(api_key=api_key)
        self.config = self._load_config()
        self.embeddings_cache = self._load_embeddings_cache()

    def _load_config(self) -> dict:
        """Load Gemini configuration from file."""
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        return {}

    def _load_embeddings_cache(self) -> dict:
        """Load cached embeddings from file."""
        if EMBEDDINGS_CACHE_FILE.exists():
            try:
                with open(EMBEDDINGS_CACHE_FILE, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print("Warning: Embeddings cache corrupted, starting fresh")
                return {"chunks": {}, "version": 1}
        return {"chunks": {}, "version": 1}

    def _save_embeddings_cache(self):
        """Save embeddings cache to file."""
        EMBEDDINGS_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(EMBEDDINGS_CACHE_FILE, 'w') as f:
            json.dump(self.embeddings_cache, f)
        print(f"Embeddings cache saved ({len(self.embeddings_cache['chunks'])} chunks)")

    def _get_embedding(self, text: str, task_type: str = "retrieval_document") -> list:
        """
        Get embedding for text using Gemini embedding model.

        Args:
            text: Text to embed
            task_type: "retrieval_document" for corpus, "retrieval_query" for queries

        Returns:
            768-dimensional embedding vector
        """
        try:
            # Truncate very long text (embedding model has limits)
            max_chars = 10000
            if len(text) > max_chars:
                text = text[:max_chars]

            result = genai.embed_content(
                model=EMBEDDING_MODEL,
                content=text,
                task_type=task_type
            )
            return result['embedding']
        except Exception as e:
            print(f"Embedding error: {e}")
            return []

    def _get_query_embedding(self, query: str) -> list:
        """Get embedding optimized for search queries."""
        return self._get_embedding(query, task_type="retrieval_query")

    def _chunk_hash(self, text: str) -> str:
        """Generate hash for a text chunk (for cache keying)."""
        return hashlib.md5(text.encode('utf-8')).hexdigest()[:16]

    def build_embeddings(self, force_rebuild: bool = False):
        """
        Build embeddings for all email chunks in the warehouse.

        This pre-computes embeddings for semantic search, avoiding
        the need to embed at query time.

        Args:
            force_rebuild: If True, rebuild all embeddings even if cached
        """
        print("\nBuilding Semantic Embeddings")
        print("=" * 80)
        print(f"Source: {GEMINI_DIR}")
        print(f"Model: {EMBEDDING_MODEL}")
        print()

        if not GEMINI_DIR.exists():
            print(f"ERROR: Gemini directory not found: {GEMINI_DIR}")
            print("Run email conversion first: python convert_to_gemini_format.py")
            return

        # Gather all chunks from markdown files
        all_chunks = []

        for md_file in GEMINI_DIR.glob("*.md"):
            print(f"Reading: {md_file.name}... ", end="")

            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Split into individual emails (separated by ==== dividers)
            emails = content.split("=" * 80)
            email_count = 0

            for email in emails:
                email = email.strip()
                if not email or len(email) < 50:  # Skip empty or tiny chunks
                    continue

                chunk_hash = self._chunk_hash(email)
                all_chunks.append({
                    'hash': chunk_hash,
                    'text': email,
                    'source': md_file.name
                })
                email_count += 1

            print(f"{email_count} emails")

        print(f"\nTotal chunks: {len(all_chunks)}")

        if not all_chunks:
            print("ERROR: No email chunks found!")
            return

        # Determine which chunks need embedding
        if force_rebuild:
            chunks_to_embed = all_chunks
            print("Force rebuild: embedding ALL chunks")
        else:
            chunks_to_embed = [
                c for c in all_chunks
                if c['hash'] not in self.embeddings_cache['chunks']
            ]
            print(f"New chunks to embed: {len(chunks_to_embed)}")
            print(f"Already cached: {len(all_chunks) - len(chunks_to_embed)}")

        if not chunks_to_embed:
            print("\nAll embeddings are up to date!")
            return

        print(f"\nEmbedding {len(chunks_to_embed)} chunks...")
        print("(This may take a few minutes)\n")

        embedded_count = 0
        error_count = 0

        for i, chunk in enumerate(chunks_to_embed):
            # Progress indicator
            if (i + 1) % 10 == 0 or i == 0:
                pct = int((i + 1) / len(chunks_to_embed) * 100)
                print(f"  Progress: {i + 1}/{len(chunks_to_embed)} ({pct}%)", end="\r")

            embedding = self._get_embedding(chunk['text'])

            if embedding:
                self.embeddings_cache['chunks'][chunk['hash']] = {
                    'embedding': embedding,
                    'source': chunk['source'],
                    'text_preview': chunk['text'][:200]  # Store preview for debugging
                }
                embedded_count += 1
            else:
                error_count += 1

            # Save periodically to avoid losing progress
            if (i + 1) % 100 == 0:
                self._save_embeddings_cache()

        print(f"\n\nEmbedding complete!")
        print(f"  Successful: {embedded_count}")
        print(f"  Errors: {error_count}")

        # Final save
        self._save_embeddings_cache()
        print()

    def _semantic_search(self, query: str, max_chunks: int = 10) -> list:
        """
        Search using semantic similarity (embeddings + cosine similarity).

        Args:
            query: Search query
            max_chunks: Maximum number of chunks to return

        Returns:
            List of relevant text chunks, sorted by relevance
        """
        if not self.embeddings_cache['chunks']:
            print("Warning: No embeddings cached. Run --build-embeddings first.")
            print("Falling back to keyword search...")
            return self._keyword_search(query, max_chunks)

        # Embed the query
        print("  Embedding query...", end=" ")
        query_embedding = self._get_query_embedding(query)
        if not query_embedding:
            print("FAILED")
            print("Warning: Could not embed query. Falling back to keyword search...")
            return self._keyword_search(query, max_chunks)
        print("OK")

        # Score all chunks by cosine similarity
        print(f"  Scoring {len(self.embeddings_cache['chunks'])} chunks...", end=" ")
        scored_chunks = []

        for chunk_hash, chunk_data in self.embeddings_cache['chunks'].items():
            similarity = cosine_similarity(query_embedding, chunk_data['embedding'])

            # Find full text from source files
            full_text = self._get_chunk_text(chunk_hash)
            if full_text:
                scored_chunks.append((similarity, full_text))

        print("OK")

        # Sort by similarity (highest first) and return top chunks
        scored_chunks.sort(reverse=True, key=lambda x: x[0])

        # Show top scores for debugging
        if scored_chunks:
            print(f"  Top similarity scores: {[round(s[0], 3) for s in scored_chunks[:5]]}")

        # Return just the text (without scores) for compatibility
        return [chunk[1] for chunk in scored_chunks[:max_chunks]]

    def _get_chunk_text(self, chunk_hash: str) -> str:
        """Retrieve full chunk text from source files."""
        chunk_data = self.embeddings_cache['chunks'].get(chunk_hash)
        if not chunk_data:
            return ""

        source_file = GEMINI_DIR / chunk_data['source']
        if not source_file.exists():
            return chunk_data.get('text_preview', '')

        # Read source file and find matching chunk
        with open(source_file, 'r', encoding='utf-8') as f:
            content = f.read()

        for email in content.split("=" * 80):
            email = email.strip()
            if self._chunk_hash(email) == chunk_hash:
                return email

        return chunk_data.get('text_preview', '')

    def _keyword_search(self, query: str, max_chunks: int = 10) -> list:
        """
        Fallback keyword search (original implementation).

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

    def query(self, question: str, max_results: int = 5, keyword_only: bool = False):
        """
        Query using semantic search with RAG.

        Args:
            question: Question to ask
            max_results: Maximum number of relevant emails to include
            keyword_only: If True, skip semantic search and use keywords only
        """
        print(f"\nQuerying WASTE Master Brain (Semantic RAG)")
        print("=" * 80)
        print(f"Question: {question}")
        print()

        try:
            # Step 1: Search for relevant content
            if keyword_only:
                print("Step 1: Keyword search for relevant emails...")
                relevant_chunks = self._keyword_search(question, max_chunks=10)
                search_type = "keyword"
            else:
                print("Step 1: Semantic search for relevant emails...")
                relevant_chunks = self._semantic_search(question, max_chunks=10)
                search_type = "semantic"

            if not relevant_chunks:
                print("No relevant emails found.")
                return {
                    'answer': "No relevant emails found for this query.",
                    'chunks_found': 0,
                    'question': question
                }

            print(f"\nFound {len(relevant_chunks)} relevant email sections")
            print()

            # Step 2: Query Gemini with relevant context
            print("Step 2: Generating answer with Gemini...")

            # Build context from relevant chunks (limit to avoid token overflow)
            context = "\n\n---\n\n".join(relevant_chunks[:max_results])

            # Configure model
            model = genai.GenerativeModel(model_name=MODEL_NAME)

            # Create prompt with context
            prompt = f"""Based on the following email exchanges from our waste management correspondence, please answer this question:

Question: {question}

Email Context:
{context}

Please provide a comprehensive answer based on the emails above. Include specific details, names, and dates when available."""

            # Generate response
            response = model.generate_content(prompt)

            print()
            print("Answer:")
            print("=" * 80)
            print(response.text)
            print()

            # Return structured data for API use
            return {
                'answer': response.text,
                'chunks_found': len(relevant_chunks),
                'question': question,
                'search_type': search_type
            }

        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
            return {
                'answer': f"Error: {str(e)}",
                'chunks_found': 0,
                'question': question,
                'error': str(e)
            }

    def get_info(self):
        """Display information about the semantic RAG system."""
        print("\nSemantic RAG System Status")
        print("=" * 80)
        print(f"Store Name: {self.config.get('store_name', 'N/A')}")
        print(f"Created: {self.config.get('created_at', 'N/A')}")
        print(f"Uploaded Files: {len(self.config.get('files', []))}")

        total_size = sum(f.get('size_mb', 0) for f in self.config.get('files', []))
        print(f"Total Size: {total_size:.2f}MB")

        print(f"\nEmbeddings Cache:")
        chunk_count = len(self.embeddings_cache.get('chunks', {}))
        print(f"  Cached Chunks: {chunk_count}")

        if chunk_count > 0:
            # Estimate cache size
            cache_size_mb = EMBEDDINGS_CACHE_FILE.stat().st_size / (1024*1024) if EMBEDDINGS_CACHE_FILE.exists() else 0
            print(f"  Cache Size: {cache_size_mb:.2f}MB")
            print(f"  Embedding Model: {EMBEDDING_MODEL}")
        else:
            print("  Status: NOT BUILT - run --build-embeddings")
        print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Semantic RAG for WASTE Master Brain",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Build embeddings (first time):
    python semantic_rag.py --build-embeddings

  Query with semantic search:
    python semantic_rag.py --query "contamination issues at garden properties"

  Query with keyword fallback:
    python semantic_rag.py --query "WM pricing" --keyword-only

  Check system status:
    python semantic_rag.py --info
"""
    )

    parser.add_argument("--api-key", help="Google AI API key (or set GOOGLE_API_KEY env var)")
    parser.add_argument("--build-embeddings", action="store_true", help="Build semantic embeddings for all emails")
    parser.add_argument("--force", action="store_true", help="Force rebuild embeddings even if cached")
    parser.add_argument("--query", help="Query the knowledge base")
    parser.add_argument("--keyword-only", action="store_true", help="Use keyword search instead of semantic")
    parser.add_argument("--max-results", type=int, default=5, help="Max email chunks to include in context")
    parser.add_argument("--info", action="store_true", help="Show system information")

    args = parser.parse_args()

    # Get API key
    api_key = args.api_key or os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        print("ERROR: API key required.")
        print("  Use --api-key YOUR_KEY")
        print("  Or set GOOGLE_API_KEY environment variable")
        print("\nGet your API key at: https://aistudio.google.com/app/apikey")
        sys.exit(1)

    # Initialize manager
    manager = SemanticRAGManager(api_key)

    # Execute command
    if args.build_embeddings:
        manager.build_embeddings(force_rebuild=args.force)

    elif args.query:
        manager.query(args.query, args.max_results, keyword_only=args.keyword_only)

    elif args.info:
        manager.get_info()

    else:
        print("No action specified. Use --help for usage information.")
        manager.get_info()


if __name__ == "__main__":
    main()
