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

import os
import sys
import logging
from pathlib import Path
from flask import Flask, jsonify, request
from flask_cors import CORS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.database import WastewiseDB
from lib.rate_rag import RateDatabaseRAG

# Constants
MAX_LIMIT = 100
ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', 'http://localhost:8000,http://localhost:3000,http://127.0.0.1:8000').split(',')
VALID_SERVICE_TYPES = {'compactor', 'dumpster', 'recycling', 'organics', 'bulky'}
VALID_RATE_TYPES = {'haul_fee', 'disposal_per_ton', 'rental', 'fuel_surcharge', 'environmental_fee', 'admin_fee', 'contamination_fee'}

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": ALLOWED_ORIGINS}})

# Initialize database
db = WastewiseDB()
rate_rag = RateDatabaseRAG()


def sanitize_string(value: str, max_length: int = 200) -> str:
    """Sanitize string input."""
    if not value or not isinstance(value, str):
        return None
    return value.strip()[:max_length]


def validate_positive_int(value: str, default: int, max_val: int = MAX_LIMIT) -> int:
    """Validate and convert to positive integer."""
    try:
        result = int(value)
        return min(max(1, result), max_val)
    except (TypeError, ValueError):
        return default


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get database statistics."""
    try:
        stats = db.get_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting stats: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/rates', methods=['GET'])
def get_rates():
    """Get rate benchmarks with optional filters."""
    try:
        vendor = sanitize_string(request.args.get('vendor'))
        service_type = sanitize_string(request.args.get('service_type'))
        rate_type = sanitize_string(request.args.get('rate_type'))
        region = sanitize_string(request.args.get('region'))

        # Validate service_type if provided
        if service_type and service_type not in VALID_SERVICE_TYPES:
            return jsonify({'error': f'Invalid service_type. Must be one of: {", ".join(VALID_SERVICE_TYPES)}'}), 400

        # Validate rate_type if provided
        if rate_type and rate_type not in VALID_RATE_TYPES:
            return jsonify({'error': f'Invalid rate_type. Must be one of: {", ".join(VALID_RATE_TYPES)}'}), 400

        result = rate_rag.get_rate_benchmark(vendor, service_type, rate_type, region)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting rates: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


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
        logger.error(f"Error getting properties: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/kpis/<property_name>', methods=['GET'])
def get_property_kpis(property_name):
    """Get KPI history for a specific property."""
    try:
        property_name = sanitize_string(property_name)
        if not property_name:
            return jsonify({'error': 'Property name is required'}), 400

        limit = validate_positive_int(request.args.get('limit'), default=12)

        kpis = db.get_property_kpis(property_name, limit=limit)
        if not kpis:
            return jsonify({'error': f'Property not found: {property_name}'}), 404

        return jsonify(kpis)
    except Exception as e:
        logger.error(f"Error getting KPIs for {property_name}: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/trends/<vendor>', methods=['GET'])
def get_rate_trends(vendor):
    """Get rate trends for a vendor."""
    try:
        vendor = sanitize_string(vendor)
        if not vendor:
            return jsonify({'error': 'Vendor name is required'}), 400

        service_type = sanitize_string(request.args.get('service_type'))
        months = validate_positive_int(request.args.get('months'), default=12, max_val=36)

        # Validate service_type if provided
        if service_type and service_type not in VALID_SERVICE_TYPES:
            return jsonify({'error': f'Invalid service_type. Must be one of: {", ".join(VALID_SERVICE_TYPES)}'}), 400

        result = rate_rag.get_pricing_trends(vendor, service_type, months)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting trends for {vendor}: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/compare', methods=['POST'])
def compare_rate():
    """Compare a rate against benchmarks."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        # Validate required fields
        required = ['rate_value', 'vendor', 'service_type', 'rate_type']
        missing = [f for f in required if f not in data]
        if missing:
            return jsonify({'error': f'Missing required fields: {", ".join(missing)}'}), 400

        # Validate rate_value
        try:
            rate_value = float(data['rate_value'])
            if rate_value < 0:
                return jsonify({'error': 'rate_value must be non-negative'}), 400
        except (TypeError, ValueError):
            return jsonify({'error': 'rate_value must be a number'}), 400

        # Validate service_type
        service_type = sanitize_string(data['service_type'])
        if service_type not in VALID_SERVICE_TYPES:
            return jsonify({'error': f'Invalid service_type. Must be one of: {", ".join(VALID_SERVICE_TYPES)}'}), 400

        # Validate rate_type
        rate_type = sanitize_string(data['rate_type'])
        if rate_type not in VALID_RATE_TYPES:
            return jsonify({'error': f'Invalid rate_type. Must be one of: {", ".join(VALID_RATE_TYPES)}'}), 400

        result = rate_rag.compare_rate(
            rate_value=rate_value,
            vendor=sanitize_string(data['vendor']),
            service_type=service_type,
            rate_type=rate_type,
            region=sanitize_string(data.get('region'))
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error comparing rate: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'service': 'kpi-api',
        'version': '1.1.0'
    })


if __name__ == '__main__':
    port = int(os.environ.get('KPI_API_PORT', 5001))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'

    logger.info(f"Starting KPI API server on http://localhost:{port}")
    logger.info(f"Debug mode: {debug}")
    logger.info(f"CORS allowed origins: {ALLOWED_ORIGINS}")
    print("Endpoints:")
    print("  GET  /api/stats")
    print("  GET  /api/rates?vendor=WM&service_type=compactor")
    print("  GET  /api/properties")
    print("  GET  /api/kpis/<property_name>")
    print("  GET  /api/trends/<vendor>")
    print("  POST /api/compare")
    print()
    app.run(host='0.0.0.0', port=port, debug=debug)
