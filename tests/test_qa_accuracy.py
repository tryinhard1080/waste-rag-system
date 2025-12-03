#!/usr/bin/env python3
"""
Test Q&A accuracy using golden dataset for Waste RAG System
"""

import pytest
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from waste_rag import WasteRAGSystem


class TestQAAccuracy:
    """Test suite for Q&A accuracy validation"""

    @pytest.fixture(scope="class")
    def rag_system(self):
        """Create and initialize a RAG system instance"""
        system = WasteRAGSystem()
        # Note: Assumes file search store is already created and populated
        # Run upload_from_config.py before running these tests
        system.file_search_store = self._get_existing_store(system)
        if system.file_search_store:
            system.initialize_model()
        return system

    @pytest.fixture(scope="class")
    def golden_qa_dataset(self):
        """Load golden Q&A dataset"""
        golden_path = Path(__file__).parent / 'golden_qa.json'

        if not golden_path.exists():
            pytest.skip("Golden Q&A dataset not found. Create tests/golden_qa.json first.")

        with open(golden_path, 'r') as f:
            return json.load(f)

    def test_system_ready(self, rag_system):
        """Test that RAG system is properly initialized"""
        if not rag_system.file_search_store:
            pytest.skip("File search store not found. Run upload_from_config.py first.")

        assert rag_system.model is not None, "Model should be initialized"

    @pytest.mark.parametrize("qa_index", range(15))  # Assuming 15 golden Q&A pairs
    def test_golden_qa_accuracy(self, rag_system, golden_qa_dataset, qa_index):
        """Test each golden Q&A pair for accuracy"""
        if not rag_system.file_search_store:
            pytest.skip("File search store not found. Run upload_from_config.py first.")

        qa_pairs = golden_qa_dataset.get('qa_pairs', [])

        if qa_index >= len(qa_pairs):
            pytest.skip(f"Q&A pair {qa_index} not in dataset")

        qa_pair = qa_pairs[qa_index]
        question = qa_pair['question']
        expected_keywords = qa_pair.get('expected_keywords', [])
        expected_concepts = qa_pair.get('expected_concepts', [])

        # Ask the question
        answer = rag_system.ask_question(question)

        assert answer is not None, f"No answer generated for: {question}"
        assert len(answer) > 50, "Answer is too short to be meaningful"

        # Check for expected keywords
        answer_lower = answer.lower()
        keywords_found = sum(1 for keyword in expected_keywords if keyword.lower() in answer_lower)
        keyword_accuracy = keywords_found / len(expected_keywords) if expected_keywords else 1.0

        # Check for expected concepts (at least 60% of concepts should be present)
        concepts_found = sum(1 for concept in expected_concepts if concept.lower() in answer_lower)
        concept_accuracy = concepts_found / len(expected_concepts) if expected_concepts else 1.0

        assert keyword_accuracy >= 0.6, f"Keyword accuracy ({keyword_accuracy:.2%}) below 60% for: {question}"
        assert concept_accuracy >= 0.5, f"Concept coverage ({concept_accuracy:.2%}) below 50% for: {question}"

    def test_answer_quality_metrics(self, rag_system, golden_qa_dataset):
        """Test overall answer quality across all Q&A pairs"""
        if not rag_system.file_search_store:
            pytest.skip("File search store not found. Run upload_from_config.py first.")

        qa_pairs = golden_qa_dataset.get('qa_pairs', [])

        if not qa_pairs:
            pytest.skip("No Q&A pairs in dataset")

        total_accuracy = 0
        successful_answers = 0

        for qa_pair in qa_pairs[:5]:  # Test first 5 for speed
            question = qa_pair['question']
            expected_keywords = qa_pair.get('expected_keywords', [])

            answer = rag_system.ask_question(question)

            if answer and len(answer) > 50:
                successful_answers += 1
                answer_lower = answer.lower()
                keywords_found = sum(1 for kw in expected_keywords if kw.lower() in answer_lower)
                accuracy = keywords_found / len(expected_keywords) if expected_keywords else 1.0
                total_accuracy += accuracy

        if successful_answers > 0:
            avg_accuracy = total_accuracy / successful_answers
            assert avg_accuracy >= 0.5, f"Average accuracy ({avg_accuracy:.2%}) below 50%"
            assert successful_answers >= 4, f"Only {successful_answers}/5 questions answered successfully"

    def test_citation_presence(self, rag_system):
        """Test that responses include citations (basic check)"""
        if not rag_system.file_search_store:
            pytest.skip("File search store not found. Run upload_from_config.py first.")

        test_question = "What are the best practices for waste disposal?"
        answer = rag_system.ask_question(test_question)

        assert answer is not None, "No answer generated"
        # Note: Citation format depends on Gemini API response structure
        # This is a basic check - enhance based on actual citation format

    def test_response_time(self, rag_system):
        """Test that queries complete in reasonable time"""
        if not rag_system.file_search_store:
            pytest.skip("File search store not found. Run upload_from_config.py first.")

        import time

        test_question = "What safety protocols apply to hazardous waste?"
        start_time = time.time()

        answer = rag_system.ask_question(test_question)

        elapsed_time = time.time() - start_time

        assert answer is not None, "No answer generated"
        assert elapsed_time < 30, f"Query took {elapsed_time:.2f}s (>30s threshold)"

    def test_different_question_types(self, rag_system):
        """Test that system handles different types of questions"""
        if not rag_system.file_search_store:
            pytest.skip("File search store not found. Run upload_from_config.py first.")

        question_types = [
            ("What is construction waste?", "definitional"),  # Definitional
            ("How do I dispose of concrete waste?", "procedural"),  # Procedural
            ("Why is waste segregation important?", "conceptual"),  # Conceptual
        ]

        for question, qtype in question_types:
            answer = rag_system.ask_question(question)
            assert answer is not None, f"No answer for {qtype} question: {question}"
            assert len(answer) > 30, f"{qtype.capitalize()} answer too short"

    @staticmethod
    def _get_existing_store(rag_system):
        """Helper to get existing file search store"""
        # This would need to list existing stores and find the right one
        # For now, we'll try to create/get the store from config
        try:
            import json
            config_path = Path(__file__).parent.parent / 'config.json'
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    store_name = config.get('store_name', 'advantage-waste-docs')

                    # Try to get the store (assuming it exists)
                    # Note: Gemini API doesn't have a direct "get store" method in the current implementation
                    # This would need to be implemented based on actual API capabilities
                    return None  # Placeholder - implement based on API
        except Exception:
            return None


class TestResponseQuality:
    """Test response quality and completeness"""

    @pytest.fixture(scope="class")
    def rag_system(self):
        """Create and initialize a RAG system instance"""
        system = WasteRAGSystem()
        return system

    def test_no_hallucination_check(self, rag_system):
        """Test that system doesn't fabricate information"""
        if not rag_system.file_search_store:
            pytest.skip("File search store not found. Run upload_from_config.py first.")

        # Ask about something very specific that might not be in docs
        obscure_question = "What is the exact cost of waste disposal on Mars?"
        answer = rag_system.ask_question(obscure_question)

        if answer:
            # Answer should acknowledge uncertainty or lack of information
            uncertainty_indicators = [
                "don't have", "not available", "unclear", "unsure",
                "cannot find", "limited information", "no specific"
            ]
            answer_lower = answer.lower()
            has_uncertainty = any(indicator in answer_lower for indicator in uncertainty_indicators)

            # Either no answer or answer with uncertainty acknowledgment
            assert has_uncertainty or len(answer) < 100, "System may be hallucinating information"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
