"""
Flask API for WASTE Master Brain - Semantic RAG System
Provides REST endpoints with true semantic search using Gemini embeddings

UPGRADE from rag_api.py:
- Uses Gemini text-embedding-004 for semantic search
- Understands meaning, not just keywords
- "contamination issues" matches "trash quality problems"

Usage:
    python semantic_api.py

    Then access at: http://localhost:5000
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from semantic_rag import SemanticRAGManager

app = Flask(__name__)
CORS(app)  # Enable CORS for dashboard access

# Initialize RAG manager
API_KEY = os.environ.get('GOOGLE_API_KEY')
if not API_KEY:
    print("ERROR: GOOGLE_API_KEY environment variable not set")
    print("Set it with: set GOOGLE_API_KEY=your_key")
    sys.exit(1)

rag_manager = SemanticRAGManager(API_KEY)


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    embeddings_count = len(rag_manager.embeddings_cache.get('chunks', {}))
    return jsonify({
        'status': 'ok',
        'service': 'WASTE Master Brain Semantic RAG',
        'version': '2.0.0',
        'search_type': 'semantic' if embeddings_count > 0 else 'keyword',
        'embeddings_cached': embeddings_count
    })


@app.route('/api/query', methods=['POST'])
def query_rag():
    """
    Query the RAG system with a natural language question

    Request body:
        {
            "question": "Your question here",
            "max_chunks": 10,     // optional
            "keyword_only": false // optional - force keyword search
        }

    Response:
        {
            "status": "success",
            "question": "Your question",
            "answer": "AI-generated answer",
            "chunks_found": 10,
            "search_type": "semantic",
            "error": null
        }
    """
    try:
        data = request.get_json()

        if not data or 'question' not in data:
            return jsonify({
                'status': 'error',
                'error': 'Missing required field: question'
            }), 400

        question = data['question']
        max_results = data.get('max_chunks', 5)
        keyword_only = data.get('keyword_only', False)

        # Query the RAG system
        print(f"Processing query: {question}")
        print(f"  Mode: {'keyword' if keyword_only else 'semantic'}")

        result = rag_manager.query(
            question,
            max_results=max_results,
            keyword_only=keyword_only
        )

        return jsonify({
            'status': 'success',
            'question': question,
            'answer': result['answer'],
            'chunks_found': result.get('chunks_found', 0),
            'search_type': result.get('search_type', 'unknown'),
            'error': None
        })

    except Exception as e:
        print(f"Error processing query: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """
    Get statistics about the RAG system

    Response:
        {
            "status": "success",
            "files_uploaded": 8,
            "total_size_mb": 25.5,
            "store_name": "waste-management-emails",
            "embeddings_cached": 1186,
            "search_type": "semantic"
        }
    """
    try:
        config = rag_manager.config
        embeddings_count = len(rag_manager.embeddings_cache.get('chunks', {}))

        total_size = sum(f.get('size_mb', 0) for f in config.get('files', []))

        return jsonify({
            'status': 'success',
            'files_uploaded': len(config.get('files', [])),
            'total_size_mb': round(total_size, 2),
            'store_name': config.get('store_name', 'unknown'),
            'embeddings_cached': embeddings_count,
            'search_type': 'semantic' if embeddings_count > 0 else 'keyword'
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/build-embeddings', methods=['POST'])
def build_embeddings():
    """
    Trigger embedding build (may take several minutes for large corpus)

    Request body:
        {
            "force": false  // optional - rebuild even if cached
        }

    Response:
        {
            "status": "success",
            "message": "Embeddings built successfully",
            "chunks_embedded": 1186
        }
    """
    try:
        data = request.get_json() or {}
        force = data.get('force', False)

        print(f"Building embeddings (force={force})...")
        rag_manager.build_embeddings(force_rebuild=force)

        embeddings_count = len(rag_manager.embeddings_cache.get('chunks', {}))

        return jsonify({
            'status': 'success',
            'message': 'Embeddings built successfully',
            'chunks_embedded': embeddings_count
        })

    except Exception as e:
        print(f"Error building embeddings: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/example-queries', methods=['GET'])
def get_example_queries():
    """
    Get example queries for the dashboard

    Response:
        {
            "status": "success",
            "examples": [...]
        }
    """
    examples = [
        # Semantic search shines on these - meaning-based queries
        "What contamination problems have we dealt with?",
        "Which properties have the worst waste issues?",
        "What strategies work for negotiating with haulers?",
        "How do we typically handle billing disputes?",
        "What are common issues with compactor service?",
        "Which vendors are difficult to work with?",
        # Waste-specific queries
        "What YPD issues have we seen at garden-style properties?",
        "Any discussions about DSQ monitoring?",
        "What has Keith Conrad recommended?",
        "Contamination fee reduction strategies"
    ]

    return jsonify({
        'status': 'success',
        'examples': examples
    })


if __name__ == '__main__':
    embeddings_count = len(rag_manager.embeddings_cache.get('chunks', {}))

    print("=" * 80)
    print("WASTE Master Brain - Semantic RAG API")
    print("=" * 80)
    print(f"Starting Flask server on http://localhost:5000")
    print(f"API Key: {'Set' if API_KEY else 'Not Set'}")
    print(f"CORS: Enabled for all origins")
    print(f"Search Mode: {'SEMANTIC' if embeddings_count > 0 else 'KEYWORD (run --build-embeddings first)'}")
    print(f"Embeddings Cached: {embeddings_count}")
    print("")
    print("Endpoints:")
    print("  GET  /api/health            - Health check + embedding status")
    print("  POST /api/query             - Query RAG system (semantic)")
    print("  GET  /api/stats             - Get RAG statistics")
    print("  POST /api/build-embeddings  - Build/rebuild embeddings")
    print("  GET  /api/example-queries   - Get example queries")
    print("")
    if embeddings_count == 0:
        print("WARNING: No embeddings cached!")
        print("         Run: python scripts/semantic_rag.py --build-embeddings")
        print("         Or POST to /api/build-embeddings")
        print("")
    print("Press Ctrl+C to stop")
    print("=" * 80)

    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)
