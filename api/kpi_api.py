"""
KPI API Server for WASTE Master Brain Dashboard

Provides REST endpoints for:
- Database statistics
- Rate benchmarks
- Property KPIs
- Rate trends

Usage:
    python kpi_api.py
    # Runs on http://localhost:5001

Endpoints:
    GET /api/stats - Database statistics
    GET /api/rates - Rate benchmarks with filters
    GET /api/properties - Property list with KPIs
    GET /api/kpis/<property> - KPIs for specific property
"""

import sys
from pathlib import Path
from flask import Flask, jsonify, request
from flask_cors import CORS

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.database import WastewiseDB
from lib.rate_rag import RateDatabaseRAG

app = Flask(__name__)
CORS(app)

# Initialize database
db = WastewiseDB()
rate_rag = RateDatabaseRAG()


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get database statistics."""
    try:
        stats = db.get_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/rates', methods=['GET'])
def get_rates():
    """Get rate benchmarks with optional filters."""
    try:
        vendor = request.args.get('vendor')
        service_type = request.args.get('service_type')
        rate_type = request.args.get('rate_type')
        region = request.args.get('region')

        result = rate_rag.get_rate_benchmark(vendor, service_type, rate_type, region)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/properties', methods=['GET'])
def get_properties():
    """Get all properties with their latest KPIs."""
    try:
        properties = db.list_properties()

        # Enrich with latest KPIs
        result = []
        for prop in properties:
            kpis = db.get_property_kpis(prop['name'], limit=1)
            latest_kpi = kpis[0] if kpis else {}

            result.append({
                'id': prop['id'],
                'name': prop['name'],
                'property_type': prop.get('property_type'),
                'unit_count': prop.get('unit_count'),
                'region': prop.get('region'),
                'cost_per_door': latest_kpi.get('cost_per_door'),
                'yards_per_door': latest_kpi.get('yards_per_door'),
                'total_cost': latest_kpi.get('total_cost'),
                'period': latest_kpi.get('period')
            })

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/kpis/<property_name>', methods=['GET'])
def get_property_kpis(property_name):
    """Get KPI history for a specific property."""
    try:
        include_history = request.args.get('history', 'false').lower() == 'true'
        limit = int(request.args.get('limit', 12))

        kpis = db.get_property_kpis(property_name, limit=limit)
        return jsonify(kpis)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/trends/<vendor>', methods=['GET'])
def get_rate_trends(vendor):
    """Get rate trends for a vendor."""
    try:
        service_type = request.args.get('service_type')
        months = int(request.args.get('months', 12))

        result = rate_rag.get_pricing_trends(vendor, service_type, months)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/compare', methods=['POST'])
def compare_rate():
    """Compare a rate against benchmarks."""
    try:
        data = request.get_json()

        result = rate_rag.compare_rate(
            rate_value=data['rate_value'],
            vendor=data['vendor'],
            service_type=data['service_type'],
            rate_type=data['rate_type'],
            region=data.get('region')
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'service': 'kpi-api',
        'version': '1.0.0'
    })


if __name__ == '__main__':
    print("Starting KPI API server on http://localhost:5001")
    print("Endpoints:")
    print("  GET  /api/stats")
    print("  GET  /api/rates?vendor=WM&service_type=compactor")
    print("  GET  /api/properties")
    print("  GET  /api/kpis/<property_name>")
    print("  GET  /api/trends/<vendor>")
    print("  POST /api/compare")
    print()
    app.run(host='0.0.0.0', port=5001, debug=True)
