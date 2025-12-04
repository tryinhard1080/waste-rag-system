"""
Unit tests for WASTE Master Brain database module.

Run with: pytest tests/test_database.py -v
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.database import WastewiseDB


@pytest.fixture
def db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    # Initialize schema
    schema_path = Path(__file__).parent.parent / "data" / "schema.sql"
    conn = sqlite3.connect(db_path)
    if schema_path.exists():
        with open(schema_path, 'r') as f:
            conn.executescript(f.read())
    conn.close()

    db = WastewiseDB(db_path)
    yield db

    # Cleanup
    Path(db_path).unlink(missing_ok=True)


class TestProperties:
    """Tests for property management."""

    def test_add_property(self, db):
        """Test adding a new property."""
        prop_id = db.add_property(
            "Test Property",
            property_type="garden",
            unit_count=100
        )
        assert prop_id > 0

    def test_get_property(self, db):
        """Test retrieving a property."""
        db.add_property("Test Property", property_type="garden", unit_count=100)
        prop = db.get_property("Test Property")

        assert prop is not None
        assert prop['name'] == "Test Property"
        assert prop['property_type'] == "garden"
        assert prop['unit_count'] == 100

    def test_get_nonexistent_property(self, db):
        """Test retrieving a property that doesn't exist."""
        prop = db.get_property("Nonexistent Property")
        assert prop is None

    def test_list_properties(self, db):
        """Test listing all properties."""
        db.add_property("Property A", unit_count=100)
        db.add_property("Property B", unit_count=200)

        properties = db.list_properties()
        assert len(properties) == 2
        names = [p['name'] for p in properties]
        assert "Property A" in names
        assert "Property B" in names

    def test_upsert_property(self, db):
        """Test that adding same property updates instead of duplicating."""
        id1 = db.add_property("Test Property", unit_count=100)
        id2 = db.add_property("Test Property", unit_count=200)

        # Should return same ID (upsert)
        assert id1 == id2

        # Should have updated unit_count
        prop = db.get_property("Test Property")
        assert prop['unit_count'] == 200


class TestRateHistory:
    """Tests for rate history tracking."""

    def test_add_rate_history(self, db):
        """Test adding a rate history record."""
        rate_id = db.add_rate_history(
            vendor="WM",
            service_type="compactor",
            rate_type="haul_fee",
            rate_value=125.00,
            effective_date="2025-01-15",
            region="Sacramento"
        )
        assert rate_id > 0

    def test_get_rate_benchmarks(self, db):
        """Test getting rate benchmarks."""
        # Add test data
        db.add_rate_history("WM", "compactor", "haul_fee", 100.00, "2025-01-01")
        db.add_rate_history("WM", "compactor", "haul_fee", 120.00, "2025-01-15")
        db.add_rate_history("WM", "compactor", "haul_fee", 140.00, "2025-02-01")

        benchmarks = db.get_rate_benchmarks(vendor="WM", service_type="compactor")

        assert benchmarks['sample_count'] == 3
        assert benchmarks['avg_rate'] == 120.00
        assert benchmarks['min_rate'] == 100.00
        assert benchmarks['max_rate'] == 140.00

    def test_get_rate_benchmarks_empty(self, db):
        """Test getting benchmarks with no data."""
        benchmarks = db.get_rate_benchmarks(vendor="Nonexistent")

        assert benchmarks['sample_count'] == 0
        assert benchmarks['avg_rate'] is None

    def test_get_rate_trends(self, db):
        """Test getting rate trends."""
        # Add test data for multiple months
        db.add_rate_history("WM", "compactor", "haul_fee", 100.00, "2025-01-15")
        db.add_rate_history("WM", "compactor", "haul_fee", 110.00, "2025-02-15")
        db.add_rate_history("WM", "compactor", "haul_fee", 120.00, "2025-03-15")

        trends = db.get_rate_trends("WM", months=12)

        assert len(trends) == 3
        # Most recent should be first
        assert trends[0]['period'] == "2025-03"


class TestKPIHistory:
    """Tests for KPI tracking."""

    def test_add_kpi_history(self, db):
        """Test adding KPI history."""
        prop_id = db.add_property("Test Property", unit_count=100)
        kpi_id = db.add_kpi_history(
            property_id=prop_id,
            period="2025-01",
            cost_per_door=10.50,
            yards_per_door=2.2,
            total_cost=1050.00
        )
        assert kpi_id > 0

    def test_get_property_kpis(self, db):
        """Test getting KPIs for a property."""
        prop_id = db.add_property("Test Property", unit_count=100)
        db.add_kpi_history(prop_id, "2025-01", cost_per_door=10.00)
        db.add_kpi_history(prop_id, "2025-02", cost_per_door=11.00)

        kpis = db.get_property_kpis("Test Property", limit=12)

        assert len(kpis) == 2
        # Most recent first
        assert kpis[0]['period'] == "2025-02"


class TestStatistics:
    """Tests for database statistics."""

    def test_get_stats(self, db):
        """Test getting database statistics."""
        # Add some test data
        db.add_property("Property A")
        db.add_rate_history("WM", "compactor", "haul_fee", 100.00, "2025-01-01")

        stats = db.get_stats()

        assert 'properties' in stats
        assert stats['properties'] >= 1
        assert 'rate_history' in stats
        assert stats['rate_history'] >= 1


class TestInputValidation:
    """Tests for input validation and security."""

    def test_sql_injection_property_name(self, db):
        """Test that SQL injection in property name is prevented."""
        malicious_name = "Test'; DROP TABLE properties; --"
        db.add_property(malicious_name)

        # Should store the malicious string as-is (parameterized query)
        prop = db.get_property(malicious_name)
        assert prop is not None
        assert prop['name'] == malicious_name

        # Properties table should still exist
        properties = db.list_properties()
        assert len(properties) >= 1

    def test_sql_injection_vendor_filter(self, db):
        """Test that SQL injection in vendor filter is prevented."""
        db.add_rate_history("WM", "compactor", "haul_fee", 100.00, "2025-01-01")

        # Try SQL injection in vendor filter
        malicious_vendor = "WM' OR '1'='1"
        benchmarks = db.get_rate_benchmarks(vendor=malicious_vendor)

        # Should return no results (parameterized query prevents injection)
        assert benchmarks['sample_count'] == 0
