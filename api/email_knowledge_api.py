"""
Email Knowledge Base API

Provides a clean interface for WasteWise to query the email RAG system.
This API bridges the email warehouse (Gemini RAG) with the operational
WasteWise system for invoice processing, contract analysis, and decision-making.

Usage:
    from api.email_knowledge_api import EmailKnowledgeAPI

    email_kb = EmailKnowledgeAPI(gemini_api_key="YOUR_KEY")

    # Get vendor insights
    insights = email_kb.get_vendor_insights("Waste Management")

    # Get similar scenarios
    similar = email_kb.get_similar_invoices({"vendor": "WM", "property": "Avana"})
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional
import json

# Add email warehouse scripts to path
SCRIPT_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from setup_gemini_rag import GeminiRAGManager


class EmailKnowledgeAPI:
    """
    API for querying email knowledge base from WasteWise.

    This provides a clean interface between the email RAG system and
    the operational WasteWise invoice/contract processing system.
    """

    def __init__(self, gemini_api_key: str, config_path: Optional[Path] = None):
        """
        Initialize the Email Knowledge API.

        Args:
            gemini_api_key: Google AI API key for Gemini
            config_path: Optional path to Gemini config (auto-detected if None)
        """
        self.rag_manager = GeminiRAGManager(gemini_api_key)
        self.cache = {}  # Simple in-memory cache for repeated queries

    def get_vendor_insights(self, vendor_name: str, limit: int = 5) -> Dict:
        """
        Get comprehensive insights about a vendor from email history.

        Args:
            vendor_name: Name of vendor (e.g., "Waste Management", "DSQ Technology")
            limit: Max number of relevant emails to analyze

        Returns:
            Dict with:
            - vendor_name: str
            - email_count: int (estimated)
            - key_contacts: List[str]
            - common_issues: List[str]
            - recent_activity: str (summary)
            - raw_response: str (full Gemini response)
        """
        cache_key = f"vendor_{vendor_name}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        query = f"""Analyze all communications with {vendor_name}. Provide:
1. Key contact names and emails
2. Most common issues discussed
3. Recent activity summary
4. Communication patterns (frequency, tone)"""

        try:
            response = self._query_rag(query, max_chunks=limit)

            result = {
                "vendor_name": vendor_name,
                "email_count": "Unknown",  # Could enhance with actual count
                "key_contacts": self._extract_contacts(response),
                "common_issues": self._extract_issues(response),
                "recent_activity": response[:500],  # First 500 chars
                "raw_response": response
            }

            self.cache[cache_key] = result
            return result

        except Exception as e:
            return {
                "error": str(e),
                "vendor_name": vendor_name
            }

    def get_similar_invoices(self, invoice_details: Dict, limit: int = 5) -> Dict:
        """
        Find similar past invoices based on vendor, property, or issue type.

        Args:
            invoice_details: Dict with keys like:
                - vendor: str
                - property: str
                - amount: float (optional)
                - issue_type: str (e.g., "contamination fee", "rate increase")
            limit: Max similar invoices to return

        Returns:
            Dict with:
            - similar_count: int
            - examples: List[Dict] (parsed email threads)
            - patterns: str (common patterns identified)
            - recommendations: str (based on past resolutions)
            - raw_response: str
        """
        vendor = invoice_details.get('vendor', '')
        property_name = invoice_details.get('property', '')
        issue = invoice_details.get('issue_type', '')

        query = f"""Find past invoices or billing discussions for:
Vendor: {vendor}
Property: {property_name}
Issue type: {issue}

What were the outcomes? How were similar issues resolved?"""

        try:
            response = self._query_rag(query, max_chunks=limit)

            return {
                "similar_count": self._count_mentions(response, ["invoice", "bill"]),
                "patterns": self._extract_patterns(response),
                "recommendations": self._extract_recommendations(response),
                "raw_response": response
            }

        except Exception as e:
            return {
                "error": str(e),
                "invoice_details": invoice_details
            }

    def get_resolution_history(self, issue_type: str, limit: int = 10) -> Dict:
        """
        Get historical resolutions for specific issue types.

        Args:
            issue_type: Type of issue (e.g., "contamination", "billing dispute",
                       "service interruption", "contract renewal")
            limit: Max examples to retrieve

        Returns:
            Dict with:
            - issue_type: str
            - resolution_examples: List[Dict]
            - success_patterns: str
            - escalation_paths: str
            - typical_timeline: str
            - raw_response: str
        """
        query = f"""Find all {issue_type} issues in the email history. For each:
1. What was the specific problem?
2. How was it resolved?
3. Who was involved?
4. How long did it take?
5. What worked and what didn't?"""

        try:
            response = self._query_rag(query, max_chunks=limit)

            return {
                "issue_type": issue_type,
                "success_patterns": self._extract_patterns(response),
                "escalation_paths": self._extract_escalations(response),
                "typical_timeline": self._extract_timeline(response),
                "raw_response": response
            }

        except Exception as e:
            return {
                "error": str(e),
                "issue_type": issue_type
            }

    def get_property_communication_history(self, property_name: str,
                                           days_back: int = 90) -> Dict:
        """
        Get all recent communications about a specific property.

        Args:
            property_name: Name of property (e.g., "Avana Collins Creek")
            days_back: How many days of history to retrieve

        Returns:
            Dict with:
            - property_name: str
            - email_count: int (estimated)
            - active_issues: List[str]
            - vendor_interactions: Dict[vendor_name, count]
            - summary: str
            - raw_response: str
        """
        query = f"""Summarize all recent communications about {property_name}:
1. What issues are currently active?
2. Which vendors are involved?
3. Any pending actions or follow-ups?
4. Overall status of waste management services"""

        try:
            response = self._query_rag(query, max_chunks=10)

            return {
                "property_name": property_name,
                "active_issues": self._extract_issues(response),
                "vendor_interactions": self._extract_vendor_mentions(response),
                "summary": response[:500],
                "raw_response": response
            }

        except Exception as e:
            return {
                "error": str(e),
                "property_name": property_name
            }

    def get_writing_style_examples(self, topic: str, count: int = 3) -> Dict:
        """
        Get examples of your writing style for specific topics.
        Useful for AI-assisted email composition.

        Args:
            topic: Topic area (e.g., "vendor negotiation", "escalation",
                  "service request", "thank you")
            count: Number of examples to retrieve

        Returns:
            Dict with:
            - topic: str
            - examples: List[str] (sample emails you wrote)
            - tone: str (identified communication style)
            - key_phrases: List[str]
            - raw_response: str
        """
        query = f"""Find emails I SENT about {topic}. Show my exact writing style:
1. How do I typically open these emails?
2. What tone do I use?
3. What phrases do I commonly use?
4. How do I close?"""

        try:
            response = self._query_rag(query, max_chunks=count)

            return {
                "topic": topic,
                "tone": self._identify_tone(response),
                "key_phrases": self._extract_key_phrases(response),
                "raw_response": response
            }

        except Exception as e:
            return {
                "error": str(e),
                "topic": topic
            }

    def get_contract_negotiation_insights(self, vendor: str) -> Dict:
        """
        Get insights from past contract negotiations with a vendor.

        Args:
            vendor: Vendor name

        Returns:
            Dict with negotiation history, successful tactics, pricing trends
        """
        query = f"""Find contract and pricing discussions with {vendor}:
1. Past rate negotiations and outcomes
2. Contract terms discussed
3. What leverage points worked?
4. Pricing trends over time"""

        try:
            response = self._query_rag(query, max_chunks=10)

            return {
                "vendor": vendor,
                "negotiation_tactics": self._extract_patterns(response),
                "pricing_insights": self._extract_pricing(response),
                "raw_response": response
            }

        except Exception as e:
            return {
                "error": str(e),
                "vendor": vendor
            }

    # Internal helper methods

    def _query_rag(self, question: str, max_chunks: int = 10) -> str:
        """Internal method to query RAG system and return response text."""
        # Search for relevant content
        relevant_chunks = self.rag_manager._search_markdown_files(question, max_chunks)

        if not relevant_chunks:
            return "No relevant information found in email history."

        # Build context
        context = "\n\n---\n\n".join(relevant_chunks)

        # Query Gemini
        import google.generativeai as genai
        model = genai.GenerativeModel(model_name="gemini-2.0-flash-exp")

        prompt = f"""Based on the following email exchanges, please answer this question:

Question: {question}

Email Context:
{context}

Please provide a comprehensive answer based on the emails above."""

        response = model.generate_content(prompt)
        return response.text

    def _extract_contacts(self, text: str) -> List[str]:
        """Extract contact names from response text."""
        # Simple extraction - could be enhanced with NLP
        contacts = []
        lines = text.split('\n')
        for line in lines:
            if '@' in line or 'contact' in line.lower():
                contacts.append(line.strip())
        return contacts[:5]  # Top 5

    def _extract_issues(self, text: str) -> List[str]:
        """Extract common issues mentioned."""
        issues = []
        keywords = ['contamination', 'billing', 'service', 'rate', 'fee', 'dispute']
        lines = text.split('\n')
        for line in lines:
            if any(kw in line.lower() for kw in keywords):
                issues.append(line.strip())
        return issues[:5]

    def _extract_patterns(self, text: str) -> str:
        """Extract patterns from response."""
        # Look for pattern indicators in text
        pattern_lines = [line for line in text.split('\n')
                        if any(word in line.lower() for word in
                              ['pattern', 'common', 'typically', 'usually', 'often'])]
        return '\n'.join(pattern_lines[:3])

    def _extract_recommendations(self, text: str) -> str:
        """Extract actionable recommendations."""
        rec_lines = [line for line in text.split('\n')
                    if any(word in line.lower() for word in
                          ['recommend', 'should', 'suggest', 'consider', 'try'])]
        return '\n'.join(rec_lines[:3])

    def _extract_escalations(self, text: str) -> str:
        """Extract escalation paths."""
        esc_lines = [line for line in text.split('\n')
                    if any(word in line.lower() for word in
                          ['escalate', 'manager', 'supervisor', 'contact'])]
        return '\n'.join(esc_lines[:3])

    def _extract_timeline(self, text: str) -> str:
        """Extract timeline information."""
        time_lines = [line for line in text.split('\n')
                     if any(word in line.lower() for word in
                           ['days', 'weeks', 'hours', 'time', 'duration'])]
        return '\n'.join(time_lines[:2])

    def _extract_vendor_mentions(self, text: str) -> Dict[str, int]:
        """Count vendor mentions."""
        vendors = {}
        common_vendors = ['Waste Management', 'WM', 'DSQ', 'Formstack']
        for vendor in common_vendors:
            count = text.lower().count(vendor.lower())
            if count > 0:
                vendors[vendor] = count
        return vendors

    def _count_mentions(self, text: str, keywords: List[str]) -> int:
        """Count keyword mentions in text."""
        return sum(text.lower().count(kw.lower()) for kw in keywords)

    def _identify_tone(self, text: str) -> str:
        """Identify communication tone."""
        formal_words = ['please', 'thank you', 'appreciate', 'kindly']
        urgent_words = ['urgent', 'asap', 'immediate', 'critical']

        formal_count = sum(1 for word in formal_words if word in text.lower())
        urgent_count = sum(1 for word in urgent_words if word in text.lower())

        if urgent_count > formal_count:
            return "Urgent/Direct"
        elif formal_count > 2:
            return "Professional/Formal"
        else:
            return "Neutral/Standard"

    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract commonly used phrases."""
        # Simple extraction - could use NLP for better results
        phrases = []
        lines = text.split('\n')
        for line in lines:
            if len(line) > 20 and len(line) < 100:
                phrases.append(line.strip())
        return phrases[:5]

    def _extract_pricing(self, text: str) -> str:
        """Extract pricing-related information."""
        price_lines = [line for line in text.split('\n')
                      if any(word in line.lower() for word in
                            ['$', 'price', 'rate', 'cost', 'fee', 'charge'])]
        return '\n'.join(price_lines[:3])

    def clear_cache(self):
        """Clear the query cache."""
        self.cache = {}


# Convenience functions for quick queries

def quick_vendor_check(vendor_name: str, api_key: str) -> str:
    """Quick vendor insights without creating API instance."""
    api = EmailKnowledgeAPI(api_key)
    result = api.get_vendor_insights(vendor_name)
    return result.get('raw_response', 'No data found')


def quick_issue_search(issue_type: str, api_key: str) -> str:
    """Quick search for issue resolutions."""
    api = EmailKnowledgeAPI(api_key)
    result = api.get_resolution_history(issue_type)
    return result.get('raw_response', 'No data found')


# Example usage
if __name__ == "__main__":
    import os

    # Get API key from environment or hardcode for testing
    api_key = os.environ.get('GOOGLE_API_KEY', 'YOUR_API_KEY')

    # Initialize API
    email_kb = EmailKnowledgeAPI(api_key)

    # Example 1: Get vendor insights
    print("=" * 80)
    print("Example 1: Vendor Insights")
    print("=" * 80)
    insights = email_kb.get_vendor_insights("Waste Management")
    print(json.dumps(insights, indent=2))

    # Example 2: Find similar invoices
    print("\n" + "=" * 80)
    print("Example 2: Similar Invoice Scenarios")
    print("=" * 80)
    similar = email_kb.get_similar_invoices({
        "vendor": "Waste Management",
        "property": "Avana",
        "issue_type": "contamination fee"
    })
    print(json.dumps(similar, indent=2))

    # Example 3: Resolution history
    print("\n" + "=" * 80)
    print("Example 3: Contamination Resolution History")
    print("=" * 80)
    resolutions = email_kb.get_resolution_history("contamination")
    print(json.dumps(resolutions, indent=2))
