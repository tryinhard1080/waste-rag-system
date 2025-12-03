"""
Integration Examples: How to use Email Knowledge API in WasteWise

These examples show how to integrate the email knowledge base into your
existing WasteWise invoice processing, contract analysis, and decision-making.
"""

from email_knowledge_api import EmailKnowledgeAPI
import json


# Example 1: Enhanced Invoice Processing
# ========================================

def process_invoice_with_email_context(invoice_data, gemini_api_key):
    """
    Process invoice with historical email context.

    This would integrate into your existing invoice_processor.py or similar.
    """
    email_kb = EmailKnowledgeAPI(gemini_api_key)

    print(f"\n📄 Processing Invoice from {invoice_data['vendor']}")
    print("=" * 80)

    # Step 1: Get vendor communication history
    vendor_insights = email_kb.get_vendor_insights(invoice_data['vendor'])

    print(f"\n🔍 Vendor Insights:")
    print(f"  Key Contacts: {', '.join(vendor_insights.get('key_contacts', [])[:2])}")
    print(f"  Common Issues: {', '.join(vendor_insights.get('common_issues', [])[:2])}")

    # Step 2: Check for similar past invoices
    similar_invoices = email_kb.get_similar_invoices({
        'vendor': invoice_data['vendor'],
        'property': invoice_data.get('property', ''),
        'issue_type': invoice_data.get('flags', [''])[0]  # First flagged issue
    })

    print(f"\n📋 Similar Past Scenarios:")
    print(f"  {similar_invoices.get('patterns', 'No patterns found')[:200]}...")

    # Step 3: Make recommendation based on historical data
    recommendation = {
        'should_approve': True,
        'confidence': 0.8,
        'reasoning': similar_invoices.get('recommendations', 'No historical data'),
        'suggested_actions': [
            'Review vendor contact history',
            'Check for similar past resolutions'
        ],
        'historical_context': similar_invoices.get('raw_response', '')[:500]
    }

    print(f"\n✅ Recommendation: {'APPROVE' if recommendation['should_approve'] else 'REVIEW'}")
    print(f"   Confidence: {recommendation['confidence']:.0%}")

    return recommendation


# Example 2: Contract Analysis with Historical Context
# ====================================================

def analyze_contract_with_email_history(contract_data, gemini_api_key):
    """
    Analyze contract renewal/negotiation with email context.

    This would integrate into your contract analysis module.
    """
    email_kb = EmailKnowledgeAPI(gemini_api_key)

    vendor = contract_data['vendor']
    print(f"\n📝 Analyzing Contract: {vendor}")
    print("=" * 80)

    # Get negotiation insights
    negotiation_insights = email_kb.get_contract_negotiation_insights(vendor)

    print(f"\n💼 Past Negotiation Insights:")
    print(f"  {negotiation_insights.get('negotiation_tactics', 'No history')[:200]}...")

    print(f"\n💰 Pricing Insights:")
    print(f"  {negotiation_insights.get('pricing_insights', 'No pricing data')[:200]}...")

    # Build recommendation
    return {
        'vendor': vendor,
        'negotiation_leverage': negotiation_insights.get('negotiation_tactics', ''),
        'pricing_trends': negotiation_insights.get('pricing_insights', ''),
        'recommended_approach': 'Use historical pricing data to negotiate better rates',
        'risk_factors': 'Check for past service issues before committing'
    }


# Example 3: Property Issue Tracker
# ==================================

def get_property_status_with_email_context(property_name, gemini_api_key):
    """
    Get comprehensive property status including email communications.

    Useful for property managers to see full context.
    """
    email_kb = EmailKnowledgeAPI(gemini_api_key)

    print(f"\n🏢 Property Status: {property_name}")
    print("=" * 80)

    # Get property communication history
    prop_history = email_kb.get_property_communication_history(property_name)

    print(f"\n📧 Communication Summary:")
    print(f"  Active Issues: {', '.join(prop_history.get('active_issues', [])[:3])}")
    print(f"  Vendor Activity: {json.dumps(prop_history.get('vendor_interactions', {}), indent=2)}")

    print(f"\n📝 Recent Summary:")
    print(f"  {prop_history.get('summary', 'No recent activity')}")

    return prop_history


# Example 4: Smart Issue Resolution Advisor
# =========================================

def get_issue_resolution_advice(issue_description, gemini_api_key):
    """
    Get step-by-step resolution advice based on past successes.

    This is like having an experienced colleague advise you.
    """
    email_kb = EmailKnowledgeAPI(gemini_api_key)

    # Determine issue type from description
    issue_types = {
        'contamination': ['contamination', 'contaminated', 'wrong bin', 'recycling'],
        'billing': ['invoice', 'charge', 'fee', 'billing', 'overcharge'],
        'service': ['missed', 'pickup', 'delay', 'service', 'truck'],
        'contract': ['contract', 'renewal', 'rate', 'agreement']
    }

    detected_type = 'general'
    for issue_type, keywords in issue_types.items():
        if any(kw in issue_description.lower() for kw in keywords):
            detected_type = issue_type
            break

    print(f"\n🔧 Issue Resolution Advisor")
    print("=" * 80)
    print(f"Issue Type: {detected_type.upper()}")
    print(f"Description: {issue_description}")
    print()

    # Get resolution history
    resolutions = email_kb.get_resolution_history(detected_type)

    print(f"📚 Historical Resolutions:")
    print(f"  Success Patterns: {resolutions.get('success_patterns', 'No patterns found')}")
    print(f"  Escalation Path: {resolutions.get('escalation_paths', 'No escalation data')}")
    print(f"  Typical Timeline: {resolutions.get('typical_timeline', 'Unknown timeline')}")

    return {
        'issue_type': detected_type,
        'recommended_steps': resolutions.get('success_patterns', ''),
        'escalation_contacts': resolutions.get('escalation_paths', ''),
        'expected_resolution_time': resolutions.get('typical_timeline', ''),
        'full_context': resolutions.get('raw_response', '')
    }


# Example 5: AI Email Composer Assistant
# ======================================

def generate_email_draft(topic, recipient, gemini_api_key):
    """
    Generate email draft in your writing style.

    Uses your past emails to match tone and phrasing.
    """
    email_kb = EmailKnowledgeAPI(gemini_api_key)

    print(f"\n✉️ Email Draft Generator")
    print("=" * 80)
    print(f"Topic: {topic}")
    print(f"To: {recipient}")
    print()

    # Get writing style examples
    style = email_kb.get_writing_style_examples(topic)

    print(f"📝 Your Writing Style for '{topic}':")
    print(f"  Tone: {style.get('tone', 'Professional')}")
    print(f"  Common Phrases: {', '.join(style.get('key_phrases', [])[:3])}")

    # In a real implementation, you'd use this context with Claude or GPT
    # to generate a draft email matching the user's style
    draft_prompt = f"""
    Write an email to {recipient} about {topic}.
    Match this writing style and tone:
    {style.get('raw_response', '')[:500]}
    """

    print(f"\n📧 Draft Context for AI:")
    print(f"  {draft_prompt[:200]}...")

    return {
        'topic': topic,
        'recipient': recipient,
        'style_context': style,
        'draft_prompt': draft_prompt
    }


# Main Test Function
# ==================

def run_integration_tests(gemini_api_key):
    """Run all integration examples with test data."""

    print("\n" + "=" * 80)
    print("WASTEWISE + EMAIL KNOWLEDGE INTEGRATION EXAMPLES")
    print("=" * 80)

    # Test 1: Invoice Processing
    print("\n\n### TEST 1: Invoice Processing ###")
    test_invoice = {
        'vendor': 'Waste Management',
        'property': 'Avana Collins Creek',
        'amount': 1250.00,
        'flags': ['contamination fee']
    }
    process_invoice_with_email_context(test_invoice, gemini_api_key)

    # Test 2: Contract Analysis
    print("\n\n### TEST 2: Contract Analysis ###")
    test_contract = {
        'vendor': 'Waste Management',
        'property': 'Multiple',
        'type': 'renewal'
    }
    analyze_contract_with_email_history(test_contract, gemini_api_key)

    # Test 3: Property Status
    print("\n\n### TEST 3: Property Status ###")
    get_property_status_with_email_context("Avana", gemini_api_key)

    # Test 4: Issue Resolution
    print("\n\n### TEST 4: Issue Resolution Advisor ###")
    get_issue_resolution_advice(
        "Property has recurring contamination fees from door-to-door valet service",
        gemini_api_key
    )

    # Test 5: Email Composer
    print("\n\n### TEST 5: Email Draft Generator ###")
    generate_email_draft(
        topic="vendor escalation",
        recipient="Waste Management",
        gemini_api_key=gemini_api_key
    )

    print("\n\n" + "=" * 80)
    print("INTEGRATION TESTS COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    import os

    # Get API key
    api_key = os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        print("ERROR: Set GOOGLE_API_KEY environment variable")
        print("Example: set GOOGLE_API_KEY=your_key_here")
        exit(1)

    # Run all tests
    run_integration_tests(api_key)
