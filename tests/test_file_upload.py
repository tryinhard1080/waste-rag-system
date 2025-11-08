#!/usr/bin/env python3
"""
Test file upload functionality for Waste RAG System
"""

import pytest
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from waste_rag import WasteRAGSystem


class TestFileUpload:
    """Test suite for file upload functionality"""

    @pytest.fixture
    def rag_system(self):
        """Create a RAG system instance for testing"""
        return WasteRAGSystem()

    @pytest.fixture
    def test_store_name(self):
        """Unique store name for testing"""
        return "test-waste-docs"

    def test_initialize_system(self, rag_system):
        """Test that the RAG system initializes properly"""
        assert rag_system is not None
        assert rag_system.client is not None
        assert rag_system.system_prompt is not None

    def test_create_file_search_store(self, rag_system, test_store_name):
        """Test file search store creation"""
        store = rag_system.create_file_search_store(test_store_name)
        assert store is not None
        assert rag_system.file_search_store is not None

    def test_upload_single_file_pdf(self, rag_system, test_store_name):
        """Test uploading a single PDF file"""
        # Create store first
        rag_system.create_file_search_store(test_store_name)

        # Find a test PDF file from config
        test_file = self._find_test_file('.pdf')

        if test_file:
            result = rag_system.upload_file(test_file)
            assert result is not None
        else:
            pytest.skip("No PDF file found for testing")

    def test_upload_single_file_docx(self, rag_system, test_store_name):
        """Test uploading a single DOCX file"""
        # Create store first
        rag_system.create_file_search_store(test_store_name)

        # Find a test DOCX file from config
        test_file = self._find_test_file('.docx')

        if test_file:
            result = rag_system.upload_file(test_file)
            assert result is not None
        else:
            pytest.skip("No DOCX file found for testing")

    def test_upload_with_custom_chunking(self, rag_system, test_store_name):
        """Test uploading with custom chunking configuration"""
        # Create store first
        rag_system.create_file_search_store(test_store_name)

        # Custom chunking config
        chunking_config = {
            'white_space_config': {
                'max_tokens_per_chunk': 500,
                'max_overlap_tokens': 50
            }
        }

        # Find a test file
        test_file = self._find_test_file('.pdf')

        if test_file:
            result = rag_system.upload_file(
                test_file,
                chunking_config=chunking_config
            )
            assert result is not None
        else:
            pytest.skip("No file found for testing")

    def test_upload_without_store(self, rag_system):
        """Test that upload fails gracefully without a store"""
        test_file = self._find_test_file('.pdf')

        if test_file:
            result = rag_system.upload_file(test_file)
            assert result is None  # Should return None when no store exists
        else:
            pytest.skip("No file found for testing")

    def test_initialize_model(self, rag_system, test_store_name):
        """Test model initialization"""
        # Create store first
        rag_system.create_file_search_store(test_store_name)

        # Upload at least one file
        test_file = self._find_test_file('.pdf')
        if test_file:
            rag_system.upload_file(test_file)

        # Initialize model
        model = rag_system.initialize_model()
        assert model is not None

    def test_initialize_model_without_store(self, rag_system):
        """Test that model initialization fails without store"""
        model = rag_system.initialize_model()
        assert model is None

    @staticmethod
    def _find_test_file(extension):
        """Helper to find a test file with given extension"""
        import json

        # Load config to find file sources
        config_path = Path(__file__).parent.parent / 'config.json'
        if not config_path.exists():
            return None

        with open(config_path, 'r') as f:
            config = json.load(f)

        # Look for a file in configured sources
        for source in config.get('file_sources', []):
            if source.get('type') == 'directory':
                path = source.get('path')
                if os.path.exists(path):
                    for root, dirs, files in os.walk(path):
                        for file in files:
                            if file.endswith(extension):
                                return os.path.join(root, file)

        return None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
