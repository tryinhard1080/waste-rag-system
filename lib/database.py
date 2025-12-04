"""
Database Access Layer for WASTE Master Brain

Provides clean interface for all database operations including:
- Properties management
- Rate history queries
- KPI tracking
- Hauler profiles
- Invoice storage

Usage:
    from lib.database import WastewiseDB

    db = WastewiseDB()
    db.add_property("Avana Sacramento", property_type="garden", unit_count=240)
    db.add_rate_history("WM", "compactor", "haul_fee", 125.00, "2025-01-01", region="Sacramento")
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

# Default database path
DEFAULT_DB_PATH = Path(__file__).parent.parent / "data" / "wastewise.db"


class WastewiseDB:
    """Database access layer for WASTE Master Brain."""

    def __init__(self, db_path: str = None):
        """Initialize database connection.

        Args:
            db_path: Path to SQLite database. Defaults to data/wastewise.db
        """
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self._ensure_db_exists()

    def _ensure_db_exists(self):
        """Ensure database and schema exist."""
        if not self.db_path.exists():
            schema_path = self.db_path.parent / "schema.sql"
            if schema_path.exists():
                with self._connect() as conn:
                    with open(schema_path, 'r') as f:
                        conn.executescript(f.read())

    @contextmanager
    def _connect(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ==================== Properties ====================

    def add_property(
        self,
        name: str,
        property_type: str = None,
        unit_count: int = None,
        address: str = None,
        city: str = None,
        state: str = None,
        region: str = None
    ) -> int:
        """Add a new property.

        Returns:
            Property ID
        """
        with self._connect() as conn:
            cursor = conn.execute("""
                INSERT INTO properties (name, property_type, unit_count, address, city, state, region)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    property_type = COALESCE(excluded.property_type, properties.property_type),
                    unit_count = COALESCE(excluded.unit_count, properties.unit_count),
                    address = COALESCE(excluded.address, properties.address),
                    city = COALESCE(excluded.city, properties.city),
                    state = COALESCE(excluded.state, properties.state),
                    region = COALESCE(excluded.region, properties.region),
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            """, (name, property_type, unit_count, address, city, state, region))
            return cursor.fetchone()[0]

    def get_property(self, name: str) -> Optional[Dict]:
        """Get property by name."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM properties WHERE name = ?", (name,)
            ).fetchone()
            return dict(row) if row else None

    def get_property_id(self, name: str) -> Optional[int]:
        """Get property ID by name, creating if needed."""
        prop = self.get_property(name)
        if prop:
            return prop['id']
        return self.add_property(name)

    def list_properties(self) -> List[Dict]:
        """List all properties."""
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM properties ORDER BY name").fetchall()
            return [dict(row) for row in rows]

    # ==================== Rate History ====================

    def add_rate_history(
        self,
        vendor: str,
        service_type: str,
        rate_type: str,
        rate_value: float,
        effective_date: str,
        property_id: int = None,
        region: str = None,
        source_document: str = None,
        notes: str = None
    ) -> int:
        """Add a rate history record.

        Args:
            vendor: Hauler name (e.g., "WM", "Republic", "Waste Connections")
            service_type: compactor, dumpster, recycling, organics, bulky
            rate_type: haul_fee, disposal_per_ton, rental, fuel_surcharge, etc.
            rate_value: Dollar amount
            effective_date: YYYY-MM-DD
            property_id: Optional property reference
            region: Geographic region for benchmarking
            source_document: Invoice/contract reference
            notes: Additional context

        Returns:
            Rate history ID
        """
        with self._connect() as conn:
            cursor = conn.execute("""
                INSERT INTO rate_history
                (property_id, vendor, service_type, rate_type, rate_value, effective_date, region, source_document, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (property_id, vendor, service_type, rate_type, rate_value, effective_date, region, source_document, notes))
            return cursor.lastrowid

    def get_rate_benchmarks(
        self,
        vendor: str = None,
        service_type: str = None,
        rate_type: str = None,
        region: str = None
    ) -> Dict:
        """Get rate benchmarks with statistics.

        Returns:
            Dict with avg, min, max, count, percentiles
        """
        conditions = []
        params = []

        if vendor:
            conditions.append("vendor = ?")
            params.append(vendor)
        if service_type:
            conditions.append("service_type = ?")
            params.append(service_type)
        if rate_type:
            conditions.append("rate_type = ?")
            params.append(rate_type)
        if region:
            conditions.append("region = ?")
            params.append(region)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        with self._connect() as conn:
            row = conn.execute(f"""
                SELECT
                    AVG(rate_value) as avg_rate,
                    MIN(rate_value) as min_rate,
                    MAX(rate_value) as max_rate,
                    COUNT(*) as sample_count
                FROM rate_history
                WHERE {where_clause}
            """, params).fetchone()

            return {
                'avg_rate': round(row['avg_rate'], 2) if row['avg_rate'] else None,
                'min_rate': row['min_rate'],
                'max_rate': row['max_rate'],
                'sample_count': row['sample_count']
            }

    def get_rate_trends(
        self,
        vendor: str,
        service_type: str = None,
        months: int = 12
    ) -> List[Dict]:
        """Get rate trends over time."""
        conditions = ["vendor = ?"]
        params = [vendor]

        if service_type:
            conditions.append("service_type = ?")
            params.append(service_type)

        where_clause = " AND ".join(conditions)

        with self._connect() as conn:
            rows = conn.execute(f"""
                SELECT
                    strftime('%Y-%m', effective_date) as period,
                    service_type,
                    rate_type,
                    AVG(rate_value) as avg_rate
                FROM rate_history
                WHERE {where_clause}
                GROUP BY period, service_type, rate_type
                ORDER BY period DESC
                LIMIT ?
            """, params + [months]).fetchall()

            return [dict(row) for row in rows]

    # ==================== KPI History ====================

    def add_kpi_history(
        self,
        property_id: int,
        period: str,
        cost_per_door: float = None,
        yards_per_door: float = None,
        contamination_rate: float = None,
        fee_burden_pct: float = None,
        total_cost: float = None,
        source_invoice_id: str = None,
        notes: str = None
    ) -> int:
        """Add KPI history record.

        Args:
            property_id: Property ID
            period: YYYY-MM format
            cost_per_door: Cost per residential unit
            yards_per_door: Cubic yards per unit
            contamination_rate: 0.0-1.0
            fee_burden_pct: Fees as % of total
            total_cost: Total monthly cost

        Returns:
            KPI history ID
        """
        with self._connect() as conn:
            cursor = conn.execute("""
                INSERT INTO kpi_history
                (property_id, period, cost_per_door, yards_per_door, contamination_rate, fee_burden_pct, total_cost, source_invoice_id, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(property_id, period) DO UPDATE SET
                    cost_per_door = COALESCE(excluded.cost_per_door, kpi_history.cost_per_door),
                    yards_per_door = COALESCE(excluded.yards_per_door, kpi_history.yards_per_door),
                    contamination_rate = COALESCE(excluded.contamination_rate, kpi_history.contamination_rate),
                    fee_burden_pct = COALESCE(excluded.fee_burden_pct, kpi_history.fee_burden_pct),
                    total_cost = COALESCE(excluded.total_cost, kpi_history.total_cost)
            """, (property_id, period, cost_per_door, yards_per_door, contamination_rate, fee_burden_pct, total_cost, source_invoice_id, notes))
            return cursor.lastrowid

    def get_property_kpis(self, property_name: str, limit: int = 12) -> List[Dict]:
        """Get KPI history for a property."""
        prop = self.get_property(property_name)
        if not prop:
            return []

        with self._connect() as conn:
            rows = conn.execute("""
                SELECT * FROM kpi_history
                WHERE property_id = ?
                ORDER BY period DESC
                LIMIT ?
            """, (prop['id'], limit)).fetchall()

            return [dict(row) for row in rows]

    def get_portfolio_kpis(self, period: str = None) -> List[Dict]:
        """Get KPIs across all properties."""
        if not period:
            period = datetime.now().strftime('%Y-%m')

        with self._connect() as conn:
            rows = conn.execute("""
                SELECT
                    p.name as property_name,
                    p.property_type,
                    p.unit_count,
                    k.*
                FROM properties p
                LEFT JOIN kpi_history k ON p.id = k.property_id AND k.period = ?
                ORDER BY p.name
            """, (period,)).fetchall()

            return [dict(row) for row in rows]

    # ==================== Hauler Profiles ====================

    def add_hauler_profile(
        self,
        vendor_name: str,
        avg_response_days: float = None,
        dispute_rate: float = None,
        negotiation_notes: str = None,
        contact_info: List[Dict] = None,
        service_regions: List[str] = None,
        strengths: str = None,
        weaknesses: str = None
    ) -> int:
        """Add or update hauler profile."""
        with self._connect() as conn:
            cursor = conn.execute("""
                INSERT INTO hauler_profiles
                (vendor_name, avg_response_days, dispute_rate, negotiation_notes, contact_info, service_regions, strengths, weaknesses)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(vendor_name) DO UPDATE SET
                    avg_response_days = COALESCE(excluded.avg_response_days, hauler_profiles.avg_response_days),
                    dispute_rate = COALESCE(excluded.dispute_rate, hauler_profiles.dispute_rate),
                    negotiation_notes = COALESCE(excluded.negotiation_notes, hauler_profiles.negotiation_notes),
                    contact_info = COALESCE(excluded.contact_info, hauler_profiles.contact_info),
                    service_regions = COALESCE(excluded.service_regions, hauler_profiles.service_regions),
                    strengths = COALESCE(excluded.strengths, hauler_profiles.strengths),
                    weaknesses = COALESCE(excluded.weaknesses, hauler_profiles.weaknesses),
                    updated_at = CURRENT_TIMESTAMP
            """, (
                vendor_name,
                avg_response_days,
                dispute_rate,
                negotiation_notes,
                json.dumps(contact_info) if contact_info else None,
                json.dumps(service_regions) if service_regions else None,
                strengths,
                weaknesses
            ))
            return cursor.lastrowid

    def get_hauler_profile(self, vendor_name: str) -> Optional[Dict]:
        """Get hauler profile."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM hauler_profiles WHERE vendor_name = ?", (vendor_name,)
            ).fetchone()

            if not row:
                return None

            result = dict(row)
            # Parse JSON fields
            if result.get('contact_info'):
                result['contact_info'] = json.loads(result['contact_info'])
            if result.get('service_regions'):
                result['service_regions'] = json.loads(result['service_regions'])
            return result

    # ==================== Invoices ====================

    def add_invoice(
        self,
        property_id: int,
        vendor: str,
        invoice_date: str,
        total_amount: float,
        invoice_number: str = None,
        service_period_start: str = None,
        service_period_end: str = None,
        haul_count: int = None,
        tons_total: float = None,
        base_service_cost: float = None,
        disposal_cost: float = None,
        fees_total: float = None,
        fees_breakdown: Dict = None,
        source_file: str = None,
        extraction_json: Dict = None
    ) -> int:
        """Add an invoice record."""
        with self._connect() as conn:
            cursor = conn.execute("""
                INSERT INTO invoices
                (property_id, vendor, invoice_number, invoice_date, service_period_start, service_period_end,
                 total_amount, haul_count, tons_total, base_service_cost, disposal_cost, fees_total,
                 fees_breakdown, source_file, extraction_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                property_id, vendor, invoice_number, invoice_date, service_period_start, service_period_end,
                total_amount, haul_count, tons_total, base_service_cost, disposal_cost, fees_total,
                json.dumps(fees_breakdown) if fees_breakdown else None,
                source_file,
                json.dumps(extraction_json) if extraction_json else None
            ))
            return cursor.lastrowid

    def get_property_invoices(self, property_name: str, limit: int = 12) -> List[Dict]:
        """Get invoices for a property."""
        prop = self.get_property(property_name)
        if not prop:
            return []

        with self._connect() as conn:
            rows = conn.execute("""
                SELECT * FROM invoices
                WHERE property_id = ?
                ORDER BY invoice_date DESC
                LIMIT ?
            """, (prop['id'], limit)).fetchall()

            return [dict(row) for row in rows]

    # ==================== Statistics ====================

    def get_stats(self) -> Dict:
        """Get database statistics."""
        with self._connect() as conn:
            stats = {}

            tables = ['properties', 'rate_history', 'kpi_history', 'hauler_profiles', 'invoices', 'email_index']
            for table in tables:
                row = conn.execute(f"SELECT COUNT(*) as count FROM {table}").fetchone()
                stats[table] = row['count']

            # Schema version
            row = conn.execute("SELECT value FROM _metadata WHERE key = 'schema_version'").fetchone()
            stats['schema_version'] = row['value'] if row else 'unknown'

            return stats


# Convenience functions for quick access
def get_db(db_path: str = None) -> WastewiseDB:
    """Get database instance."""
    return WastewiseDB(db_path)
