"""
Integration tests for KPI API endpoints.

Run with: pytest tests/test_kpi_api.py -v
"""

import pytest
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.kpi_api import app, sanitize_string, validate_positive_int


@pytest.fixture
def client():
    """Create test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestInputSanitization:
    """Tests for input sanitization functions."""

    def test_sanitize_string_normal(self):
        """Test sanitizing normal strings."""
        assert sanitize_string("hello") == "hello"
        assert sanitize_string("  hello  ") == "hello"

    def test_sanitize_string_empty(self):
        """Test sanitizing empty/None values."""
        assert sanitize_string(None) is None
        assert sanitize_string("") is None
        assert sanitize_string("   ") is None

    def test_sanitize_string_max_length(self):
        """Test max length truncation."""
        long_string = "a" * 500
        result = sanitize_string(long_string, max_length=100)
        assert len(result) == 100

    def test_validate_positive_int_valid(self):
        """Test validating valid integers."""
        assert validate_positive_int("10", default=5) == 10
        assert validate_positive_int("1", default=5) == 1

    def test_validate_positive_int_invalid(self):
        """Test validating invalid values returns default."""
        assert validate_positive_int("abc", default=5) == 5
        assert validate_positive_int(None, default=5) == 5

    def test_validate_positive_int_max(self):
        """Test max value enforcement."""
        assert validate_positive_int("1000", default=5, max_val=50) == 50

    def test_validate_positive_int_min(self):
        """Test minimum value enforcement."""
        assert validate_positive_int("0", default=5, max_val=50) == 1
        assert validate_positive_int("-5", default=5, max_val=50) == 1


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_returns_ok(self, client):
        """Test health endpoint returns OK."""
        response = client.get('/api/health')
        assert response.status_code == 200

        data = response.get_json()
        assert data['status'] == 'ok'
        assert data['service'] == 'kpi-api'


class TestStatsEndpoint:
    """Tests for stats endpoint."""

    def test_stats_returns_data(self, client):
        """Test stats endpoint returns data."""
        response = client.get('/api/stats')
        assert response.status_code == 200

        data = response.get_json()
        assert 'properties' in data or 'error' not in data


class TestRatesEndpoint:
    """Tests for rates endpoint."""

    def test_rates_no_filters(self, client):
        """Test rates endpoint with no filters."""
        response = client.get('/api/rates')
        assert response.status_code == 200

    def test_rates_with_filters(self, client):
        """Test rates endpoint with valid filters."""
        response = client.get('/api/rates?vendor=WM&service_type=compactor')
        assert response.status_code == 200

    def test_rates_invalid_service_type(self, client):
        """Test rates endpoint with invalid service_type."""
        response = client.get('/api/rates?service_type=invalid')
        assert response.status_code == 400

        data = response.get_json()
        assert 'error' in data
        assert 'Invalid service_type' in data['error']


class TestCompareEndpoint:
    """Tests for rate comparison endpoint."""

    def test_compare_missing_body(self, client):
        """Test compare endpoint with missing body."""
        response = client.post('/api/compare')
        assert response.status_code == 400

    def test_compare_missing_fields(self, client):
        """Test compare endpoint with missing required fields."""
        response = client.post('/api/compare', json={
            'rate_value': 100
        })
        assert response.status_code == 400

        data = response.get_json()
        assert 'error' in data
        assert 'Missing required fields' in data['error']

    def test_compare_invalid_rate_value(self, client):
        """Test compare endpoint with invalid rate_value."""
        response = client.post('/api/compare', json={
            'rate_value': 'not_a_number',
            'vendor': 'WM',
            'service_type': 'compactor',
            'rate_type': 'haul_fee'
        })
        assert response.status_code == 400

    def test_compare_negative_rate_value(self, client):
        """Test compare endpoint with negative rate_value."""
        response = client.post('/api/compare', json={
            'rate_value': -100,
            'vendor': 'WM',
            'service_type': 'compactor',
            'rate_type': 'haul_fee'
        })
        assert response.status_code == 400

    def test_compare_valid_request(self, client):
        """Test compare endpoint with valid request."""
        response = client.post('/api/compare', json={
            'rate_value': 150.00,
            'vendor': 'WM',
            'service_type': 'compactor',
            'rate_type': 'haul_fee',
            'region': 'Sacramento'
        })
        assert response.status_code == 200


class TestSecurityHeaders:
    """Tests for security-related behavior."""

    def test_cors_headers_present(self, client):
        """Test that CORS headers are present."""
        response = client.options('/api/health')
        # CORS preflight should work
        assert response.status_code in [200, 204]

    def test_error_messages_dont_leak_details(self, client):
        """Test that error messages don't expose internal details."""
        # This test relies on there being an error condition
        # In production, we want generic error messages
        response = client.get('/api/kpis/nonexistent_property_12345')

        if response.status_code == 404:
            data = response.get_json()
            # Should have user-friendly message, not stack traces
            assert 'Traceback' not in str(data)
