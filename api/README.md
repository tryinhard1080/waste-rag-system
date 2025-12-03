# Email Knowledge API Integration Guide

**Connect your email RAG system to WasteWise for intelligent decision-making**

---

## 🎯 What This Does

The Email Knowledge API provides a clean interface for WasteWise to query your 50K+ email corpus and get:
- Historical vendor insights
- Similar past invoice scenarios
- Proven issue resolutions
- Contract negotiation patterns
- Your writing style for AI-assisted composition

## 🚀 Quick Start

### 1. Install (if not already done)
```bash
pip install google-generativeai
```

### 2. Set API Key
```powershell
# Windows
set GOOGLE_API_KEY=your_gemini_api_key_here

# Or in Python
import os
os.environ['GOOGLE_API_KEY'] = 'your_key'
```

### 3. Use in Your Code
```python
from api.email_knowledge_api import EmailKnowledgeAPI

# Initialize
email_kb = EmailKnowledgeAPI(gemini_api_key="YOUR_KEY")

# Get vendor insights
insights = email_kb.get_vendor_insights("Waste Management")
print(insights['common_issues'])

# Find similar invoices
similar = email_kb.get_similar_invoices({
    'vendor': 'WM',
    'property': 'Avana',
    'issue_type': 'contamination'
})
print(similar['recommendations'])
```

---

## 📚 API Reference

### Core Methods

#### `get_vendor_insights(vendor_name: str) -> Dict`
Get comprehensive vendor history from emails.

**Returns:**
- `key_contacts`: List of main contacts
- `common_issues`: Frequent problems
- `recent_activity`: Latest interactions
- `raw_response`: Full Gemini analysis

**Example:**
```python
insights = email_kb.get_vendor_insights("Waste Management")
print(f"Main contact: {insights['key_contacts'][0]}")
print(f"Issues: {insights['common_issues']}")
```

---

#### `get_similar_invoices(invoice_details: Dict) -> Dict`
Find similar past invoices and their outcomes.

**Parameters:**
```python
{
    'vendor': str,
    'property': str,
    'amount': float (optional),
    'issue_type': str
}
```

**Returns:**
- `patterns`: Common patterns identified
- `recommendations`: What worked in the past
- `similar_count`: Number of similar cases

**Example:**
```python
similar = email_kb.get_similar_invoices({
    'vendor': 'Waste Management',
    'property': 'Avana Collins Creek',
    'issue_type': 'contamination fee'
})

if similar['recommendations']:
    print(f"Based on past cases: {similar['recommendations']}")
```

---

#### `get_resolution_history(issue_type: str) -> Dict`
Get how similar issues were resolved historically.

**Common Issue Types:**
- `"contamination"`
- `"billing dispute"`
- `"service interruption"`
- `"contract renewal"`
- `"rate increase"`

**Returns:**
- `success_patterns`: What typically works
- `escalation_paths`: Who to contact
- `typical_timeline`: Expected resolution time

**Example:**
```python
resolutions = email_kb.get_resolution_history("contamination")
print(f"Success pattern: {resolutions['success_patterns']}")
print(f"Escalate to: {resolutions['escalation_paths']}")
print(f"Timeline: {resolutions['typical_timeline']}")
```

---

#### `get_property_communication_history(property_name: str) -> Dict`
Get all recent emails about a property.

**Returns:**
- `active_issues`: Current problems
- `vendor_interactions`: Who you've been talking to
- `summary`: Recent activity overview

**Example:**
```python
history = email_kb.get_property_communication_history("Avana Collins Creek")
print(f"Active issues: {history['active_issues']}")
print(f"Vendors involved: {list(history['vendor_interactions'].keys())}")
```

---

#### `get_writing_style_examples(topic: str) -> Dict`
Get examples of your writing for AI-assisted composition.

**Returns:**
- `tone`: Your communication style
- `key_phrases`: Phrases you commonly use
- Examples of your actual emails

**Example:**
```python
style = email_kb.get_writing_style_examples("vendor escalation")
print(f"Your tone: {style['tone']}")
print(f"Common phrases: {style['key_phrases']}")

# Use this context with Claude/GPT to generate emails in your style
```

---

#### `get_contract_negotiation_insights(vendor: str) -> Dict`
Get contract negotiation history and tactics.

**Returns:**
- `negotiation_tactics`: What worked before
- `pricing_insights`: Rate trends over time

---

## 🔌 Integration Patterns

### Pattern 1: Enhanced Invoice Review

```python
# In your invoice_processor.py or similar

def review_invoice(invoice):
    # Your existing validation logic
    basic_checks = validate_invoice_format(invoice)

    # NEW: Add email context
    from api.email_knowledge_api import EmailKnowledgeAPI
    email_kb = EmailKnowledgeAPI(gemini_api_key)

    # Check vendor history
    vendor_insights = email_kb.get_vendor_insights(invoice['vendor'])

    # Look for similar past invoices
    similar = email_kb.get_similar_invoices({
        'vendor': invoice['vendor'],
        'property': invoice['property'],
        'issue_type': invoice.get('flagged_issue', '')
    })

    # Make informed decision
    recommendation = {
        'approve': basic_checks['valid'],
        'confidence': calculate_confidence(similar),
        'notes': similar['recommendations'],
        'historical_context': similar['raw_response']
    }

    return recommendation
```

---

### Pattern 2: Smart Issue Resolution Assistant

```python
# When property reports an issue

def handle_property_issue(issue_description, property_name):
    from api.email_knowledge_api import EmailKnowledgeAPI
    email_kb = EmailKnowledgeAPI(gemini_api_key)

    # Get resolution advice based on past successes
    advice = email_kb.get_resolution_history(
        determine_issue_type(issue_description)
    )

    # Get property-specific context
    prop_history = email_kb.get_property_communication_history(property_name)

    # Provide comprehensive guidance
    return {
        'recommended_steps': advice['success_patterns'],
        'escalation_contact': advice['escalation_paths'],
        'expected_timeline': advice['typical_timeline'],
        'property_context': prop_history['active_issues']
    }
```

---

### Pattern 3: Contract Negotiation Prep

```python
# Before negotiating contract renewal

def prepare_contract_negotiation(vendor):
    from api.email_knowledge_api import EmailKnowledgeAPI
    email_kb = EmailKnowledgeAPI(gemini_api_key)

    # Get negotiation insights
    insights = email_kb.get_contract_negotiation_insights(vendor)

    # Get vendor relationship history
    relationship = email_kb.get_vendor_insights(vendor)

    # Build negotiation strategy
    return {
        'leverage_points': insights['negotiation_tactics'],
        'pricing_baseline': insights['pricing_insights'],
        'relationship_strength': len(relationship['key_contacts']),
        'known_issues': relationship['common_issues']
    }
```

---

## 🧪 Testing the Integration

Run the test suite to see all integration examples:

```powershell
cd api
python integration_examples.py
```

This will demonstrate:
1. ✅ Invoice processing with email context
2. ✅ Contract analysis with historical data
3. ✅ Property status with communication history
4. ✅ Issue resolution advisor
5. ✅ Email draft generator (your writing style)

---

## 🎨 Customization

### Add Custom Query Methods

```python
# Extend the EmailKnowledgeAPI class

class CustomEmailAPI(EmailKnowledgeAPI):
    def get_quarterly_vendor_summary(self, vendor, quarter):
        """Custom method for quarterly reports"""
        query = f"Summarize {vendor} interactions in Q{quarter}"
        return self._query_rag(query, max_chunks=20)
```

### Adjust Search Sensitivity

```python
# In email_knowledge_api.py, modify _search_markdown_files
# to tune keyword matching or scoring
```

---

## 🐛 Troubleshooting

**"No relevant information found"**
- Make sure emails are extracted and converted to Gemini format
- Check that gemini_config.json has file URIs
- Verify API key is valid

**Token limit errors**
- The API automatically limits context to 10 chunks
- Increase/decrease with `max_chunks` parameter

**Slow queries**
- First query is slowest (no cache)
- Enable caching: `email_kb.cache` is automatic
- Clear cache if needed: `email_kb.clear_cache()`

---

## 📊 Performance

- **Query time**: 2-5 seconds (keyword search + Gemini)
- **Caching**: Results cached in memory (cleared on restart)
- **Cost**: ~$0.001-0.003 per query (Gemini API)

---

## 🔐 Security Notes

- API key should be in environment variables, not hardcoded
- Email content is sent to Gemini API (Google servers)
- No data is permanently stored by Gemini (per their policy)
- Consider data sanitization for highly sensitive content

---

## 📈 Next Steps

1. **Test with real WasteWise code**: Try one integration pattern
2. **Measure impact**: Track decision quality improvements
3. **Expand coverage**: Add more custom query methods
4. **Feedback loop**: Update email corpus with new learnings

---

## 🤝 Support

For questions or issues:
1. Check integration_examples.py for reference
2. Review CLAUDE.md in project root
3. Test with smaller queries first

**Happy integrating! 🚀**
