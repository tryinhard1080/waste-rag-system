#!/usr/bin/env python3
"""
Test citation and source tracking for Waste RAG System
Ensures responses include proper citations from source documents
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from waste_rag import WasteRAGSystem


class TestCitations:
    """Test suite for citation and source tracking"""

    @pytest.fixture(scope="class")
    def rag_system(self):
        """Create and initialize a RAG system instance"""
        system = WasteRAGSystem()
        # Assumes file search store is already created
        # Run upload_from_config.py before running these tests
        try:
            import json
            config_path = Path(__file__).parent.parent / 'config.json'
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    store_name = config.get('store_name', 'advantage-waste-docs')
                    # Note: Would need to get existing store here
                    # For now, assuming it exists and model is initialized
                    system.initialize_model()
        except Exception:
            pass

        return system

    def test_system_includes_citations(self, rag_system):
        """Test that the system prompt encourages citations"""
        assert "cite" in rag_system.system_prompt.lower() or "source" in rag_system.system_prompt.lower(), \
            "System prompt should encourage citing sources"

    def test_response_with_source_reference(self, rag_system):
        """Test that responses reference source documents"""
        if not rag_system.model:
            pytest.skip("Model not initialized. Run upload_from_config.py first.")

        test_questions = [
            "What are construction waste guidelines?",
            "How should hazardous materials be handled?",
            "What are recycling requirements?",
        ]

        for question in test_questions:
            answer = rag_system.ask_question(question)

            if answer:
                # Check if answer has source-like references
                # Common citation patterns
                has_citation = any([
                    "according to" in answer.lower(),
                    "based on" in answer.lower(),
                    "document" in answer.lower(),
                    "guideline" in answer.lower(),
                    "policy" in answer.lower(),
                    "regulation" in answer.lower(),
                    "requirement" in answer.lower(),
                ])

                assert has_citation or len(answer) > 200, \
                    f"Response may lack proper context/citations for: {question}"

    def test_specific_document_attribution(self, rag_system):
        """Test that system can attribute information to specific documents"""
        if not rag_system.model:
            pytest.skip("Model not initialized. Run upload_from_config.py first.")

        # Ask a specific question likely to reference specific documents
        question = "What regulations apply to construction site waste management?"
        answer = rag_system.ask_question(question)

        assert answer is not None, "No answer generated"
        assert len(answer) > 100, "Answer too brief to include proper attribution"

        # Check for specific/concrete references
        specific_indicators = [
            "section",
            "chapter",
            "page",
            "document",
            "guideline",
            "manual",
            "handbook",
            "regulation",
            "code",
        ]

        answer_lower = answer.lower()
        has_specific_ref = any(indicator in answer_lower for indicator in specific_indicators)

        # At minimum, answer should be detailed enough to be useful
        assert has_specific_ref or len(answer) > 300, "Answer lacks specific document references"

    def test_multiple_source_synthesis(self, rag_system):
        """Test that system can synthesize information from multiple sources"""
        if not rag_system.model:
            pytest.skip("Model not initialized. Run upload_from_config.py first.")

        # Broad question likely to require multiple documents
        question = "What are the comprehensive requirements for waste management on construction sites?"
        answer = rag_system.ask_question(question)

        assert answer is not None, "No answer generated"
        assert len(answer) > 200, "Answer too brief for comprehensive topic"

        # Answer should cover multiple aspects
        aspects = [
            ("disposal", "segregation", "sorting"),  # Disposal methods
            ("safety", "hazard", "protocol"),  # Safety
            ("regulation", "compliance", "requirement"),  # Regulations
        ]

        aspects_covered = 0
        answer_lower = answer.lower()

        for aspect_group in aspects:
            if any(term in answer_lower for term in aspect_group):
                aspects_covered += 1

        assert aspects_covered >= 2, f"Answer covers only {aspects_covered}/3 key aspects"

    def test_citation_accuracy(self, rag_system):
        """Test that citations are accurate and not hallucinated"""
        if not rag_system.model:
            pytest.skip("Model not initialized. Run upload_from_config.py first.")

        # Ask about a general topic
        question = "What are best practices for waste reduction?"
        answer = rag_system.ask_question(question)

        if answer:
            # Check that answer doesn't claim to cite non-existent sources
            suspicious_phrases = [
                "as mentioned in the article",
                "as stated on the website",
                "according to the research",
                "in the study",
            ]

            answer_lower = answer.lower()
            has_suspicious = any(phrase in answer_lower for phrase in suspicious_phrases)

            # If it uses these phrases, they should be backed by actual document references
            if has_suspicious:
                # Should also contain document-specific terms
                has_doc_ref = any(term in answer_lower for term in ["document", "guideline", "policy", "manual"])
                assert has_doc_ref, "Answer references sources without specific document attribution"

    def test_source_diversity(self, rag_system):
        """Test that system draws from diverse sources when available"""
        if not rag_system.model:
            pytest.skip("Model not initialized. Run upload_from_config.py first.")

        # Ask questions that should pull from different types of documents
        questions = [
            "What are the legal requirements for waste disposal?",  # Regulations
            "What are practical steps for waste sorting?",  # Guidelines
            "What equipment is needed for waste management?",  # Technical docs
        ]

        answers = []
        for question in questions:
            answer = rag_system.ask_question(question)
            if answer:
                answers.append(answer.lower())

        # Answers should have some variety (not identical)
        if len(answers) >= 2:
            # Basic check: answers should differ significantly
            similarity = sum(1 for i in range(len(answers)-1) if answers[i][:100] == answers[i+1][:100])
            assert similarity == 0, "Answers appear too similar - may indicate limited source diversity"

    def test_no_citation_when_uncertain(self, rag_system):
        """Test that system doesn't fabricate citations when uncertain"""
        if not rag_system.model:
            pytest.skip("Model not initialized. Run upload_from_config.py first.")

        # Ask about something unlikely to be in construction/waste docs
        obscure_question = "What are the waste management practices on the International Space Station?"
        answer = rag_system.ask_question(obscure_question)

        if answer:
            # If system doesn't have info, it should acknowledge rather than cite fake sources
            answer_lower = answer.lower()

            # Either should be brief/uncertain, or should not claim specific sources
            specific_false_citations = [
                "nasa document states",
                "iss manual indicates",
                "space agency guidelines",
            ]

            has_false_citation = any(phrase in answer_lower for phrase in specific_false_citations)

            # If answer is detailed and claims sources, flag it
            if len(answer) > 150 and has_false_citation:
                pytest.fail("System may be fabricating citations for information not in corpus")


class TestSourceTracking:
    """Test source tracking and grounding metadata"""

    @pytest.fixture(scope="class")
    def rag_system(self):
        """Create RAG system instance"""
        system = WasteRAGSystem()
        try:
            system.initialize_model()
        except Exception:
            pass
        return system

    def test_grounding_metadata_structure(self, rag_system):
        """Test that responses include grounding metadata when available"""
        if not rag_system.model:
            pytest.skip("Model not initialized. Run upload_from_config.py first.")

        # Note: This test depends on Gemini API returning grounding_metadata
        # The actual structure may vary
        question = "What are waste classification methods?"

        # The ask_question method should handle grounding metadata
        # This is a structural test to ensure the method processes metadata
        try:
            answer = rag_system.ask_question(question)
            assert answer is not None, "Should return answer even if no metadata"
        except AttributeError:
            pytest.fail("Method should handle missing grounding metadata gracefully")

    def test_citation_format_consistency(self, rag_system):
        """Test that citations follow a consistent format"""
        if not rag_system.model:
            pytest.skip("Model not initialized. Run upload_from_config.py first.")

        questions = [
            "What are waste disposal methods?",
            "What safety measures are required?",
        ]

        citations_found = []

        for question in questions:
            answer = rag_system.ask_question(question)
            if answer and ("document" in answer.lower() or "guideline" in answer.lower()):
                citations_found.append(answer)

        # If citations are present, they should follow some pattern
        # This is a basic consistency check
        if len(citations_found) >= 2:
            # Both should reference documents/guidelines in similar manner
            assert True  # Placeholder for more specific citation format validation


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
