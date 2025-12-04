#!/usr/bin/env python3
"""
WASTE Master Brain MCP Server (Python)

Connects Claude Code to waste intelligence data including:
- Rate database with benchmarks and trends
- Semantic email search
- Property KPI tracking
- Extraction persistence

Usage:
    python server.py

MCP Config (~/.claude/mcp_settings.json):
    {
      "mcpServers": {
        "waste-master-brain": {
          "command": "python",
          "args": ["C:/Users/Richard/Documents/Waste Rag Master Brain/waste-rag-system/mcp-server/server.py"],
          "env": {
            "GOOGLE_API_KEY": "your-api-key"
          }
        }
      }
    }
"""

import sys
import os
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
import subprocess

# Add parent directories to path
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Try to import MCP SDK
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Tool,
        TextContent,
        Resource,
        ListToolsResult,
        CallToolResult,
        ListResourcesResult,
        ReadResourceResult,
    )
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("MCP SDK not installed. Install with: pip install mcp", file=sys.stderr)

# Database path
DB_PATH = os.environ.get('DB_PATH', str(PROJECT_ROOT / "data" / "wastewise.db"))
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY', '')


class WasteMasterBrainServer:
    """MCP Server for WASTE Master Brain."""

    def __init__(self):
        self.db_path = DB_PATH

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ==================== Tool Handlers ====================

    def query_rates(
        self,
        vendor: str = None,
        service_type: str = None,
        rate_type: str = None,
        region: str = None
    ) -> Dict:
        """Query historical rate data with benchmarks."""
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

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        with self._get_connection() as conn:
            # Get statistics
            stats = conn.execute(f"""
                SELECT
                    AVG(rate_value) as avg_rate,
                    MIN(rate_value) as min_rate,
                    MAX(rate_value) as max_rate,
                    COUNT(*) as sample_count
                FROM rate_history
                {where_clause}
            """, params).fetchone()

            # Get recent trends
            trends = conn.execute(f"""
                SELECT
                    strftime('%Y-%m', effective_date) as period,
                    AVG(rate_value) as avg_rate
                FROM rate_history
                {where_clause}
                GROUP BY period
                ORDER BY period DESC
                LIMIT 6
            """, params).fetchall()

        avg_rate = stats['avg_rate']
        min_rate = stats['min_rate']
        max_rate = stats['max_rate']
        sample_count = stats['sample_count']

        interpretation = (
            f"Based on {sample_count} rate records, average is ${avg_rate:.2f} (range: ${min_rate} - ${max_rate})"
            if sample_count > 0 else "No rate data found for these filters."
        )

        return {
            'benchmarks': {
                'avg_rate': round(avg_rate, 2) if avg_rate else None,
                'min_rate': min_rate,
                'max_rate': max_rate,
                'sample_count': sample_count
            },
            'filters': {'vendor': vendor, 'service_type': service_type, 'rate_type': rate_type, 'region': region},
            'recent_trends': [dict(t) for t in trends],
            'interpretation': interpretation
        }

    def search_emails(self, query: str, max_results: int = 5) -> Dict:
        """Semantic search over email knowledge base."""
        script_path = PROJECT_ROOT / "scripts" / "semantic_rag.py"

        try:
            result = subprocess.run(
                [sys.executable, str(script_path), "--query", query, "--max-results", str(max_results)],
                capture_output=True,
                text=True,
                env={**os.environ, 'GOOGLE_API_KEY': GOOGLE_API_KEY},
                timeout=120
            )

            if result.returncode != 0:
                return {
                    'query': query,
                    'error': result.stderr,
                    'results': []
                }

            # Parse answer from output
            output = result.stdout
            if "Answer:" in output:
                answer = output.split("Answer:\n" + "=" * 80 + "\n")[-1].strip()
            else:
                answer = output

            return {
                'query': query,
                'answer': answer,
                'results_found': True
            }

        except subprocess.TimeoutExpired:
            return {'query': query, 'error': 'Search timed out', 'results': []}
        except Exception as e:
            return {'query': query, 'error': str(e), 'results': []}

    def get_property_kpis(
        self,
        property_name: str,
        period: str = None,
        include_history: bool = False
    ) -> Dict:
        """Get KPI metrics for a property."""
        with self._get_connection() as conn:
            # Get property
            prop = conn.execute(
                "SELECT * FROM properties WHERE name = ?", (property_name,)
            ).fetchone()

            if not prop:
                return {
                    'property_name': property_name,
                    'error': 'Property not found',
                    'suggestion': 'Use save_extraction to add this property first'
                }

            # Get KPIs
            if include_history:
                kpis = conn.execute("""
                    SELECT * FROM kpi_history
                    WHERE property_id = ?
                    ORDER BY period DESC
                    LIMIT 12
                """, (prop['id'],)).fetchall()
                kpis = [dict(k) for k in kpis]
            elif period:
                kpi = conn.execute("""
                    SELECT * FROM kpi_history
                    WHERE property_id = ? AND period = ?
                """, (prop['id'], period)).fetchone()
                kpis = dict(kpi) if kpi else None
            else:
                kpi = conn.execute("""
                    SELECT * FROM kpi_history
                    WHERE property_id = ?
                    ORDER BY period DESC
                    LIMIT 1
                """, (prop['id'],)).fetchone()
                kpis = dict(kpi) if kpi else None

            return {
                'property': {
                    'name': prop['name'],
                    'unit_count': prop['unit_count']
                },
                'kpis': kpis or [],
                'period': period or 'latest'
            }

    def save_extraction(
        self,
        property_name: str,
        extraction_type: str,
        data: Dict,
        vendor: str = None,
        source_document: str = None
    ) -> Dict:
        """Save WasteWise extraction results to database."""
        with self._get_connection() as conn:
            # Get or create property
            prop = conn.execute(
                "SELECT id FROM properties WHERE name = ?", (property_name,)
            ).fetchone()

            if not prop:
                cursor = conn.execute(
                    "INSERT INTO properties (name) VALUES (?)", (property_name,)
                )
                property_id = cursor.lastrowid
            else:
                property_id = prop['id']

            if extraction_type == 'invoice':
                cursor = conn.execute("""
                    INSERT INTO invoices
                    (property_id, vendor, invoice_number, invoice_date, total_amount,
                     haul_count, tons_total, base_service_cost, disposal_cost, fees_total,
                     source_file, extraction_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    property_id,
                    vendor or data.get('vendor'),
                    data.get('invoice_number'),
                    data.get('invoice_date'),
                    data.get('total_amount'),
                    data.get('haul_count'),
                    data.get('tons_total'),
                    data.get('base_service_cost'),
                    data.get('disposal_cost'),
                    data.get('fees_total'),
                    source_document,
                    json.dumps(data)
                ))
                saved_id = cursor.lastrowid

                # Save rates if present
                if 'rates' in data and isinstance(data['rates'], list):
                    for rate in data['rates']:
                        conn.execute("""
                            INSERT INTO rate_history
                            (property_id, vendor, service_type, rate_type, rate_value, effective_date, source_document)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            property_id,
                            vendor or data.get('vendor'),
                            rate['service_type'],
                            rate['rate_type'],
                            rate['rate_value'],
                            data.get('invoice_date'),
                            source_document
                        ))

            elif extraction_type == 'kpi':
                cursor = conn.execute("""
                    INSERT INTO kpi_history
                    (property_id, period, cost_per_door, yards_per_door, contamination_rate,
                     fee_burden_pct, total_cost, source_invoice_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(property_id, period) DO UPDATE SET
                        cost_per_door = excluded.cost_per_door,
                        yards_per_door = excluded.yards_per_door,
                        contamination_rate = excluded.contamination_rate,
                        fee_burden_pct = excluded.fee_burden_pct,
                        total_cost = excluded.total_cost
                """, (
                    property_id,
                    data['period'],
                    data.get('cost_per_door'),
                    data.get('yards_per_door'),
                    data.get('contamination_rate'),
                    data.get('fee_burden_pct'),
                    data.get('total_cost'),
                    source_document
                ))
                saved_id = cursor.lastrowid

            elif extraction_type == 'contract':
                cursor = conn.execute("""
                    INSERT INTO contracts
                    (property_id, vendor, contract_type, start_date, end_date, auto_renewal,
                     renewal_notice_days, termination_notice_days, rate_increase_cap, key_terms, source_file)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    property_id,
                    vendor,
                    data.get('contract_type'),
                    data.get('start_date'),
                    data.get('end_date'),
                    1 if data.get('auto_renewal') else 0,
                    data.get('renewal_notice_days'),
                    data.get('termination_notice_days'),
                    data.get('rate_increase_cap'),
                    json.dumps(data.get('key_terms')),
                    source_document
                ))
                saved_id = cursor.lastrowid
            else:
                return {'error': f'Unknown extraction type: {extraction_type}'}

            conn.commit()

        return {
            'success': True,
            'extraction_type': extraction_type,
            'property_name': property_name,
            'saved_id': saved_id,
            'message': f'Successfully saved {extraction_type} data for {property_name}'
        }

    def generate_kpi_chart(
        self,
        chart_type: str,
        kpi_type: str,
        title: str,
        description: str = None,
        property_filter: str = None,
        vendor_filter: str = None,
        months: int = 12
    ) -> Dict:
        """Generate chart data for KPI visualizations."""
        with self._get_connection() as conn:
            if kpi_type == 'cost_per_door':
                if property_filter:
                    rows = conn.execute("""
                        SELECT p.name, k.period, k.cost_per_door as value
                        FROM kpi_history k
                        JOIN properties p ON k.property_id = p.id
                        WHERE p.name LIKE ?
                        ORDER BY k.period DESC
                        LIMIT ?
                    """, (f'%{property_filter}%', months)).fetchall()
                else:
                    rows = conn.execute("""
                        SELECT p.name, k.period, k.cost_per_door as value
                        FROM kpi_history k
                        JOIN properties p ON k.property_id = p.id
                        ORDER BY k.period DESC
                        LIMIT ?
                    """, (months,)).fetchall()
                chart_config = {'value': {'label': 'Cost/Door ($)', 'color': 'hsl(var(--chart-1))'}}

            elif kpi_type == 'yards_per_door':
                rows = conn.execute("""
                    SELECT p.name, k.period, k.yards_per_door as value
                    FROM kpi_history k
                    JOIN properties p ON k.property_id = p.id
                    ORDER BY k.period DESC
                    LIMIT ?
                """, (months,)).fetchall()
                chart_config = {'value': {'label': 'Yards/Door', 'color': 'hsl(var(--chart-2))'}}

            elif kpi_type == 'pricing_trends':
                if vendor_filter:
                    rows = conn.execute("""
                        SELECT strftime('%Y-%m', effective_date) as period, vendor, AVG(rate_value) as value
                        FROM rate_history
                        WHERE vendor = ?
                        GROUP BY period, vendor
                        ORDER BY period DESC
                        LIMIT ?
                    """, (vendor_filter, months)).fetchall()
                else:
                    rows = conn.execute("""
                        SELECT strftime('%Y-%m', effective_date) as period, vendor, AVG(rate_value) as value
                        FROM rate_history
                        GROUP BY period, vendor
                        ORDER BY period DESC
                        LIMIT ?
                    """, (months,)).fetchall()
                chart_config = {'value': {'label': 'Avg Rate ($)', 'color': 'hsl(var(--chart-3))'}}

            else:
                rows = []
                chart_config = {}

        return {
            'chartType': chart_type,
            'kpiType': kpi_type,
            'config': {
                'title': title,
                'description': description or f'{kpi_type} visualization'
            },
            'data': [dict(r) for r in rows],
            'chartConfig': chart_config
        }

    def get_stats(self) -> Dict:
        """Get database statistics."""
        with self._get_connection() as conn:
            stats = {}
            tables = ['properties', 'rate_history', 'kpi_history', 'invoices', 'contracts', 'hauler_profiles']
            for table in tables:
                row = conn.execute(f"SELECT COUNT(*) as count FROM {table}").fetchone()
                stats[table] = row['count']
        return stats


# Tool definitions
TOOLS = [
    {
        'name': 'query_rates',
        'description': 'Search historical waste hauler rates by vendor, service type, and region. Returns benchmarks including average, min, max rates.',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'vendor': {'type': 'string', 'description': "Filter by hauler name (e.g., 'WM', 'Republic')"},
                'service_type': {'type': 'string', 'enum': ['compactor', 'dumpster', 'recycling', 'organics', 'bulky']},
                'rate_type': {'type': 'string', 'enum': ['haul_fee', 'disposal_per_ton', 'rental', 'fuel_surcharge', 'environmental_fee', 'admin_fee', 'contamination_fee']},
                'region': {'type': 'string', 'description': 'Geographic region'}
            }
        }
    },
    {
        'name': 'search_emails',
        'description': 'Semantic search over waste management email knowledge base using Gemini embeddings.',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'query': {'type': 'string', 'description': 'Natural language search query'},
                'max_results': {'type': 'number', 'description': 'Maximum results (default: 5)'}
            },
            'required': ['query']
        }
    },
    {
        'name': 'get_property_kpis',
        'description': 'Get KPI metrics for a property including cost per door, yards per door, contamination rate.',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'property_name': {'type': 'string', 'description': 'Name of the property'},
                'period': {'type': 'string', 'description': 'Period in YYYY-MM format'},
                'include_history': {'type': 'boolean', 'description': 'Include historical KPIs'}
            },
            'required': ['property_name']
        }
    },
    {
        'name': 'save_extraction',
        'description': 'Save WasteWise extraction results (invoices, contracts, KPIs) to the Master Brain database.',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'property_name': {'type': 'string', 'description': 'Property name'},
                'extraction_type': {'type': 'string', 'enum': ['invoice', 'contract', 'kpi']},
                'vendor': {'type': 'string', 'description': 'Vendor name'},
                'data': {'type': 'object', 'description': 'Extracted data'},
                'source_document': {'type': 'string', 'description': 'Source file reference'}
            },
            'required': ['property_name', 'extraction_type', 'data']
        }
    },
    {
        'name': 'generate_kpi_chart',
        'description': 'Generate structured chart data for waste management KPI visualizations.',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'chart_type': {'type': 'string', 'enum': ['bar', 'line', 'pie', 'area']},
                'kpi_type': {'type': 'string', 'enum': ['cost_per_door', 'yards_per_door', 'contamination', 'pricing_trends']},
                'title': {'type': 'string', 'description': 'Chart title'},
                'description': {'type': 'string', 'description': 'Chart description'},
                'property_filter': {'type': 'string', 'description': 'Filter by property'},
                'vendor_filter': {'type': 'string', 'description': 'Filter by vendor'},
                'months': {'type': 'number', 'description': 'Months for trends (default: 12)'}
            },
            'required': ['chart_type', 'kpi_type', 'title']
        }
    }
]


def main():
    """Main entry point for MCP server."""
    if not MCP_AVAILABLE:
        # Fallback: simple JSON-RPC style interface for testing
        print("MCP SDK not available. Running in test mode.", file=sys.stderr)
        server = WasteMasterBrainServer()

        # Print available tools
        print(json.dumps({'tools': TOOLS}, indent=2))

        # Test query_rates
        result = server.query_rates(vendor='WM', service_type='compactor')
        print(json.dumps({'test_query_rates': result}, indent=2))

        return

    # MCP Server setup
    server = WasteMasterBrainServer()
    mcp_server = Server("waste-master-brain")

    @mcp_server.list_tools()
    async def list_tools() -> list[Tool]:
        return [Tool(**t) for t in TOOLS]

    @mcp_server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        try:
            if name == 'query_rates':
                result = server.query_rates(**arguments)
            elif name == 'search_emails':
                result = server.search_emails(**arguments)
            elif name == 'get_property_kpis':
                result = server.get_property_kpis(**arguments)
            elif name == 'save_extraction':
                result = server.save_extraction(**arguments)
            elif name == 'generate_kpi_chart':
                result = server.generate_kpi_chart(**arguments)
            else:
                result = {'error': f'Unknown tool: {name}'}

            return [TextContent(type='text', text=json.dumps(result, indent=2))]
        except Exception as e:
            return [TextContent(type='text', text=json.dumps({'error': str(e)}))]

    @mcp_server.list_resources()
    async def list_resources() -> list[Resource]:
        return [Resource(
            uri='wastewise://stats',
            name='Database Statistics',
            description='Current counts of properties, rates, KPIs, and other data',
            mimeType='application/json'
        )]

    @mcp_server.read_resource()
    async def read_resource(uri: str) -> str:
        if uri == 'wastewise://stats':
            return json.dumps(server.get_stats(), indent=2)
        raise ValueError(f'Unknown resource: {uri}')

    # Run server with proper async context
    import asyncio

    async def run_server():
        async with stdio_server() as (read_stream, write_stream):
            await mcp_server.run(read_stream, write_stream, mcp_server.create_initialization_options())

    asyncio.run(run_server())


if __name__ == '__main__':
    main()
