"""
Flask API for Email Warehouse RAG System
Provides REST endpoints for live RAG queries from dashboard

Usage:
    python rag_api.py

    Then access at: http://localhost:5000
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from setup_gemini_rag import GeminiRAGManager

app = Flask(__name__)
CORS(app)  # Enable CORS for dashboard access

# Initialize RAG manager
API_KEY = os.environ.get('GOOGLE_API_KEY')
if not API_KEY:
    print("ERROR: GOOGLE_API_KEY environment variable not set")
    print("Set it with: set GOOGLE_API_KEY=your_key")
    sys.exit(1)

rag_manager = GeminiRAGManager(API_KEY)


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'Email Warehouse RAG API',
        'version': '1.0.0'
    })


@app.route('/api/query', methods=['POST'])
def query_rag():
    """
    Query the RAG system with a natural language question

    Request body:
        {
            "question": "Your question here",
            "max_chunks": 10  // optional
        }

    Response:
        {
            "status": "success",
            "question": "Your question",
            "answer": "AI-generated answer",
            "chunks_found": 10,
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
        max_results = data.get('max_chunks', 10)  # Accept max_chunks for backwards compatibility

        # Query the RAG system
        print(f"Processing query: {question}")
        result = rag_manager.query(question, max_results=max_results)

        return jsonify({
            'status': 'success',
            'question': question,
            'answer': result['answer'],
            'chunks_found': result.get('chunks_found', 0),
            'error': None
        })

    except Exception as e:
        print(f"Error processing query: {str(e)}")
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
            "store_name": "waste-management-emails"
        }
    """
    try:
        config = rag_manager.config

        total_size = sum(f.get('size_mb', 0) for f in config.get('files', []))

        return jsonify({
            'status': 'success',
            'files_uploaded': len(config.get('files', [])),
            'total_size_mb': round(total_size, 2),
            'store_name': config.get('store_name', 'unknown')
        })

    except Exception as e:
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
        "What are the main waste management issues discussed recently?",
        "Who are my key contacts at Waste Management?",
        "Summarize recent contamination fee issues",
        "What properties have billing disputes?",
        "What vendors do I communicate with most?",
        "What were the main topics discussed this week?"
    ]

    return jsonify({
        'status': 'success',
        'examples': examples
    })


if __name__ == '__main__':
    print("=" * 80)
    print("Email Warehouse RAG API")
    print("=" * 80)
    print(f"Starting Flask server on http://localhost:5000")
    print(f"API Key: {'Set' if API_KEY else 'Not Set'}")
    print(f"CORS: Enabled for all origins")
    print("")
    print("Endpoints:")
    print("  GET  /api/health          - Health check")
    print("  POST /api/query           - Query RAG system")
    print("  GET  /api/stats           - Get RAG statistics")
    print("  GET  /api/example-queries - Get example queries")
    print("")
    print("Press Ctrl+C to stop")
    print("=" * 80)

    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)
