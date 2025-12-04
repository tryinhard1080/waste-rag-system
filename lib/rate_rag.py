"""
Rate Database RAG for WASTE Master Brain

Combines SQLite rate data with semantic search to provide:
- Historical pricing benchmarks by vendor/region/service
- Rate trend analysis
- Intelligent rate comparison recommendations

Usage:
    from lib.rate_rag import RateDatabaseRAG

    rag = RateDatabaseRAG()
    benchmark = rag.get_rate_benchmark("WM", "compactor", region="Sacramento")
    trends = rag.get_pricing_trends("WM", months=12)
    comparison = rag.compare_rate(125.00, "WM", "compactor", "haul_fee")
"""

import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.database import WastewiseDB

# Try to import Gemini for semantic analysis
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class RateDatabaseRAG:
    """
    Rate Database with RAG capabilities.

    Combines structured rate data from SQLite with semantic understanding
    via Gemini for intelligent pricing analysis.
    """

    def __init__(self, db_path: str = None, api_key: str = None):
        """Initialize rate database RAG.

        Args:
            db_path: Path to SQLite database
            api_key: Google AI API key (optional, for semantic features)
        """
        self.db = WastewiseDB(db_path)
        self.api_key = api_key or os.environ.get('GOOGLE_API_KEY')

        if GEMINI_AVAILABLE and self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        else:
            self.model = None

    def get_rate_benchmark(
        self,
        vendor: str = None,
        service_type: str = None,
        rate_type: str = None,
        region: str = None
    ) -> Dict:
        """
        Get rate benchmarks with statistics.

        Args:
            vendor: Filter by hauler (e.g., "WM", "Republic")
            service_type: compactor, dumpster, recycling, organics
            rate_type: haul_fee, disposal_per_ton, rental, etc.
            region: Geographic region

        Returns:
            Dict containing:
            - avg_rate: Average rate
            - min_rate: Minimum observed
            - max_rate: Maximum observed
            - sample_count: Number of data points
            - percentiles: 25th, 50th, 75th percentiles
            - interpretation: Human-readable analysis
        """
        # Get basic statistics from database
        stats = self.db.get_rate_benchmarks(vendor, service_type, rate_type, region)

        if not stats['sample_count']:
            return {
                'avg_rate': None,
                'min_rate': None,
                'max_rate': None,
                'sample_count': 0,
                'message': 'No rate data available for these criteria'
            }

        # Add interpretation
        result = {
            **stats,
            'filters': {
                'vendor': vendor,
                'service_type': service_type,
                'rate_type': rate_type,
                'region': region
            }
        }

        # Generate semantic interpretation if Gemini available
        if self.model and stats['sample_count'] >= 3:
            result['interpretation'] = self._generate_benchmark_interpretation(result)

        return result

    def get_pricing_trends(
        self,
        vendor: str,
        service_type: str = None,
        months: int = 12
    ) -> Dict:
        """
        Get pricing trends over time for a vendor.

        Args:
            vendor: Hauler name
            service_type: Optional filter by service type
            months: Number of months to analyze

        Returns:
            Dict containing:
            - trends: List of monthly averages
            - direction: "increasing", "decreasing", "stable"
            - percent_change: Total % change over period
            - analysis: AI-generated trend analysis
        """
        trends = self.db.get_rate_trends(vendor, service_type, months)

        if not trends:
            return {
                'vendor': vendor,
                'trends': [],
                'direction': 'unknown',
                'message': f'No trend data available for {vendor}'
            }

        # Calculate direction and percent change
        if len(trends) >= 2:
            first_rate = trends[-1]['avg_rate']  # Oldest
            last_rate = trends[0]['avg_rate']    # Most recent

            if first_rate and last_rate and first_rate > 0:
                pct_change = ((last_rate - first_rate) / first_rate) * 100

                if pct_change > 5:
                    direction = 'increasing'
                elif pct_change < -5:
                    direction = 'decreasing'
                else:
                    direction = 'stable'
            else:
                pct_change = 0
                direction = 'unknown'
        else:
            pct_change = 0
            direction = 'unknown'

        result = {
            'vendor': vendor,
            'service_type': service_type,
            'trends': trends,
            'direction': direction,
            'percent_change': round(pct_change, 2),
            'months_analyzed': len(trends)
        }

        # Generate AI analysis if available
        if self.model and len(trends) >= 3:
            result['analysis'] = self._generate_trend_analysis(result)

        return result

    def compare_rate(
        self,
        rate_value: float,
        vendor: str,
        service_type: str,
        rate_type: str,
        region: str = None
    ) -> Dict:
        """
        Compare a specific rate against benchmarks.

        Args:
            rate_value: The rate to compare
            vendor: Hauler name
            service_type: Service type
            rate_type: Rate type
            region: Optional region filter

        Returns:
            Dict containing:
            - position: "below_average", "average", "above_average", "significantly_above"
            - percentile: Estimated percentile ranking
            - savings_potential: Estimated potential savings
            - recommendation: Action recommendation
        """
        # Get benchmarks for comparison
        benchmark = self.get_rate_benchmark(vendor, service_type, rate_type, region)

        if not benchmark.get('avg_rate'):
            # Fall back to broader comparison
            benchmark = self.get_rate_benchmark(None, service_type, rate_type, region)

        if not benchmark.get('avg_rate'):
            return {
                'rate_value': rate_value,
                'position': 'unknown',
                'message': 'Insufficient data for comparison'
            }

        avg = benchmark['avg_rate']
        min_rate = benchmark['min_rate']
        max_rate = benchmark['max_rate']

        # Calculate position
        if rate_value <= min_rate:
            position = 'excellent'
            percentile = 10
        elif rate_value < avg * 0.9:
            position = 'below_average'
            percentile = 25
        elif rate_value <= avg * 1.1:
            position = 'average'
            percentile = 50
        elif rate_value < max_rate:
            position = 'above_average'
            percentile = 75
        else:
            position = 'significantly_above'
            percentile = 95

        # Calculate savings potential
        savings_potential = max(0, rate_value - avg)
        savings_pct = (savings_potential / rate_value * 100) if rate_value > 0 else 0

        result = {
            'rate_value': rate_value,
            'benchmark': benchmark,
            'position': position,
            'percentile': percentile,
            'savings_potential': round(savings_potential, 2),
            'savings_potential_pct': round(savings_pct, 1)
        }

        # Generate recommendation
        result['recommendation'] = self._generate_recommendation(result)

        return result

    def query_rates(self, natural_language_query: str) -> Dict:
        """
        Query rate database using natural language.

        Args:
            natural_language_query: Free-form question about rates

        Returns:
            Dict with answer and supporting data
        """
        if not self.model:
            return {
                'query': natural_language_query,
                'error': 'Semantic query requires Gemini API key'
            }

        # Get context from database
        context = self._build_rate_context()

        prompt = f"""You are a waste management pricing analyst. Answer this question using the rate data below.

Question: {natural_language_query}

Rate Data Context:
{context}

Provide a specific, data-driven answer. Include relevant numbers and comparisons.
If the data is insufficient, say so clearly."""

        try:
            response = self.model.generate_content(prompt)
            return {
                'query': natural_language_query,
                'answer': response.text,
                'context_used': True
            }
        except Exception as e:
            return {
                'query': natural_language_query,
                'error': str(e)
            }

    def save_rate_from_invoice(
        self,
        property_name: str,
        vendor: str,
        invoice_date: str,
        rates: List[Dict],
        region: str = None,
        source_document: str = None
    ) -> List[int]:
        """
        Save extracted rates from an invoice.

        Args:
            property_name: Property name (will create if not exists)
            vendor: Hauler name
            invoice_date: Invoice date (YYYY-MM-DD)
            rates: List of rate dicts: [{service_type, rate_type, rate_value}]
            region: Geographic region
            source_document: Invoice reference

        Returns:
            List of created rate IDs
        """
        property_id = self.db.get_property_id(property_name)

        rate_ids = []
        for rate in rates:
            rate_id = self.db.add_rate_history(
                vendor=vendor,
                service_type=rate['service_type'],
                rate_type=rate['rate_type'],
                rate_value=rate['rate_value'],
                effective_date=invoice_date,
                property_id=property_id,
                region=region,
                source_document=source_document
            )
            rate_ids.append(rate_id)

        return rate_ids

    def _build_rate_context(self) -> str:
        """Build context string from rate database for semantic queries."""
        stats = self.db.get_stats()

        if stats['rate_history'] == 0:
            return "No rate data available in database."

        context_parts = [
            f"Database contains {stats['rate_history']} rate records across {stats['properties']} properties."
        ]

        # Get vendor-level summaries
        # Note: This is a simplified version - could be enhanced with more queries
        return "\n".join(context_parts)

    def _generate_benchmark_interpretation(self, benchmark: Dict) -> str:
        """Generate human-readable interpretation of benchmark."""
        avg = benchmark['avg_rate']
        min_r = benchmark['min_rate']
        max_r = benchmark['max_rate']
        count = benchmark['sample_count']
        filters = benchmark.get('filters', {})

        parts = []

        # Filter description
        filter_desc = []
        if filters.get('vendor'):
            filter_desc.append(f"{filters['vendor']}")
        if filters.get('service_type'):
            filter_desc.append(f"{filters['service_type']}")
        if filters.get('rate_type'):
            filter_desc.append(f"{filters['rate_type']}")
        if filters.get('region'):
            filter_desc.append(f"in {filters['region']}")

        filter_str = " ".join(filter_desc) if filter_desc else "all rates"
        parts.append(f"Based on {count} data points for {filter_str}:")
        parts.append(f"• Average: ${avg:.2f}")
        parts.append(f"• Range: ${min_r:.2f} - ${max_r:.2f}")

        spread = ((max_r - min_r) / avg * 100) if avg > 0 else 0
        if spread > 50:
            parts.append("• High variability suggests room for negotiation")
        elif spread < 20:
            parts.append("• Low variability indicates stable market pricing")

        return "\n".join(parts)

    def _generate_trend_analysis(self, trend_data: Dict) -> str:
        """Generate AI analysis of pricing trends."""
        if not self.model:
            return self._generate_simple_trend_analysis(trend_data)

        prompt = f"""Analyze this waste hauler pricing trend data and provide a brief (2-3 sentence) analysis:

Vendor: {trend_data['vendor']}
Service: {trend_data.get('service_type', 'All services')}
Direction: {trend_data['direction']}
Change: {trend_data['percent_change']}% over {trend_data['months_analyzed']} months

Monthly data: {json.dumps(trend_data['trends'][:6])}

Focus on actionable insights for negotiation or budgeting."""

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception:
            return self._generate_simple_trend_analysis(trend_data)

    def _generate_simple_trend_analysis(self, trend_data: Dict) -> str:
        """Generate simple trend analysis without AI."""
        direction = trend_data['direction']
        pct = trend_data['percent_change']
        vendor = trend_data['vendor']

        if direction == 'increasing':
            return f"{vendor} rates have increased {pct}% over the analyzed period. Consider rate lock provisions in contracts."
        elif direction == 'decreasing':
            return f"{vendor} rates have decreased {pct}% over the analyzed period. Good time to negotiate new terms."
        else:
            return f"{vendor} rates have remained relatively stable (±{abs(pct)}%). Current pricing is consistent with market."

    def _generate_recommendation(self, comparison: Dict) -> str:
        """Generate recommendation based on rate comparison."""
        position = comparison['position']
        savings = comparison['savings_potential']
        savings_pct = comparison['savings_potential_pct']

        if position == 'excellent':
            return "Rate is competitive. No immediate action needed."
        elif position == 'below_average':
            return "Rate is favorable. Consider locking in current pricing."
        elif position == 'average':
            return "Rate is at market average. Monitor for opportunities."
        elif position == 'above_average':
            return f"Rate is above average. Potential savings of ${savings:.2f} ({savings_pct}%) through negotiation."
        else:
            return f"Rate significantly exceeds market. Recommend RFP process. Potential savings of ${savings:.2f}+ ({savings_pct}%)."


# Quick test
if __name__ == "__main__":
    rag = RateDatabaseRAG()

    # Add some test data
    rag.save_rate_from_invoice(
        property_name="Test Property",
        vendor="WM",
        invoice_date="2025-01-15",
        rates=[
            {"service_type": "compactor", "rate_type": "haul_fee", "rate_value": 125.00},
            {"service_type": "compactor", "rate_type": "disposal_per_ton", "rate_value": 65.00}
        ],
        region="Sacramento"
    )

    # Test benchmark
    benchmark = rag.get_rate_benchmark("WM", "compactor", "haul_fee")
    print("Benchmark:", json.dumps(benchmark, indent=2))

    # Test comparison
    comparison = rag.compare_rate(150.00, "WM", "compactor", "haul_fee")
    print("\nComparison:", json.dumps(comparison, indent=2))
