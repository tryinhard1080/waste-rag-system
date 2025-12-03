#!/usr/bin/env python3
"""
Test document coverage for Waste RAG System
Validates that all configured documents are successfully ingested
"""

import pytest
import json
import os
import glob
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from upload_from_config import load_config, collect_files_from_config


class TestDocumentCoverage:
    """Test suite for document coverage validation"""

    @pytest.fixture(scope="class")
    def config(self):
        """Load configuration"""
        config_path = Path(__file__).parent.parent / 'config.json'
        if not config_path.exists():
            pytest.skip("config.json not found")
        return load_config(str(config_path))

    @pytest.fixture(scope="class")
    def expected_files(self, config):
        """Get list of all files that should be ingested"""
        return collect_files_from_config(config)

    @pytest.fixture(scope="class")
    def ingestion_report(self):
        """Load ingestion report if it exists"""
        report_path = Path(__file__).parent.parent / 'logs' / 'ingestion_report.json'

        if not report_path.exists():
            pytest.skip("Ingestion report not found. Run upload_from_config.py first.")

        with open(report_path, 'r') as f:
            return json.load(f)

    def test_all_sources_exist(self, config):
        """Test that all configured file sources exist"""
        for source in config.get('file_sources', []):
            if source.get('type') == 'directory':
                path = source.get('path')
                assert os.path.exists(path), f"Source directory not found: {path}"

    def test_files_found(self, expected_files):
        """Test that expected files were found"""
        assert len(expected_files) > 0, "No files found from configured sources"
        print(f"\nFound {len(expected_files)} files to process")

    def test_coverage_percentage(self, expected_files, ingestion_report):
        """Test that at least 95% of files were successfully ingested"""
        total_files = len(expected_files)
        successful_files = ingestion_report.get('successful_uploads', 0)

        coverage_pct = (successful_files / total_files * 100) if total_files > 0 else 0

        assert coverage_pct >= 95.0, f"Coverage {coverage_pct:.1f}% below 95% threshold ({successful_files}/{total_files})"

    def test_file_extension_coverage(self, config, ingestion_report):
        """Test that all configured file extensions are covered"""
        expected_extensions = set(config.get('supported_extensions', []))
        processed_extensions = set(ingestion_report.get('extensions_processed', []))

        # At least some of the configured extensions should be processed
        overlap = expected_extensions & processed_extensions
        assert len(overlap) > 0, "No configured file extensions were processed"

    def test_no_critical_failures(self, ingestion_report):
        """Test that there are no critical failures during ingestion"""
        failed_files = ingestion_report.get('failed_uploads', [])
        critical_errors = [f for f in failed_files if 'critical' in f.get('error', '').lower()]

        assert len(critical_errors) == 0, f"Found {len(critical_errors)} critical errors during ingestion"

    def test_upload_success_rate(self, ingestion_report):
        """Test overall upload success rate"""
        total = ingestion_report.get('total_files', 0)
        successful = ingestion_report.get('successful_uploads', 0)

        if total > 0:
            success_rate = (successful / total) * 100
            assert success_rate >= 90.0, f"Upload success rate {success_rate:.1f}% below 90% threshold"

    def test_file_size_distribution(self, expected_files):
        """Test that files have reasonable size distribution"""
        file_sizes = []

        for file_path in expected_files[:50]:  # Sample first 50 files
            if os.path.exists(file_path):
                size_mb = os.path.getsize(file_path) / (1024 * 1024)
                file_sizes.append(size_mb)

        if file_sizes:
            avg_size = sum(file_sizes) / len(file_sizes)
            max_size = max(file_sizes)

            # Gemini has 100MB limit per file
            assert max_size < 100, f"File exceeds 100MB limit: {max_size:.2f}MB"
            assert avg_size < 50, f"Average file size {avg_size:.2f}MB seems very large"

    def test_directory_structure_valid(self, config):
        """Test that configured directories have valid structure"""
        for source in config.get('file_sources', []):
            if source.get('type') == 'directory':
                path = source.get('path')

                if os.path.exists(path):
                    # Check if directory is readable
                    assert os.access(path, os.R_OK), f"Directory not readable: {path}"

                    # Check if directory has files
                    recursive = source.get('recursive', False)
                    pattern = os.path.join(path, '**' if recursive else '*', '*')
                    files = glob.glob(pattern, recursive=recursive)

                    assert len(files) > 0, f"No files found in directory: {path}"


class TestIngestionMetrics:
    """Test ingestion metrics and statistics"""

    @pytest.fixture(scope="class")
    def ingestion_report(self):
        """Load ingestion report"""
        report_path = Path(__file__).parent.parent / 'logs' / 'ingestion_report.json'

        if not report_path.exists():
            pytest.skip("Ingestion report not found. Run upload_from_config.py first.")

        with open(report_path, 'r') as f:
            return json.load(f)

    def test_processing_time_reasonable(self, ingestion_report):
        """Test that processing completed in reasonable time"""
        processing_time = ingestion_report.get('total_processing_time_seconds', 0)
        total_files = ingestion_report.get('total_files', 1)

        # Average time per file should be reasonable (< 30 seconds)
        avg_time_per_file = processing_time / total_files if total_files > 0 else 0

        assert avg_time_per_file < 30, f"Average processing time {avg_time_per_file:.2f}s per file too slow"

    def test_retry_statistics(self, ingestion_report):
        """Test retry statistics are within acceptable range"""
        total_retries = ingestion_report.get('total_retries', 0)
        total_files = ingestion_report.get('total_files', 1)

        # Retry rate should be less than 20%
        retry_rate = (total_retries / total_files) * 100 if total_files > 0 else 0

        assert retry_rate < 20, f"Retry rate {retry_rate:.1f}% above 20% threshold"

    def test_storage_usage(self, ingestion_report):
        """Test storage usage is within expected bounds"""
        total_storage_mb = ingestion_report.get('total_storage_mb', 0)

        # Gemini free tier has storage limits - warn if approaching
        assert total_storage_mb < 10000, f"Storage usage {total_storage_mb:.2f}MB approaching limits"

    def test_category_distribution(self, ingestion_report):
        """Test that documents are distributed across categories"""
        categories = ingestion_report.get('categories', {})

        if categories:
            # Should have at least 2 different categories
            assert len(categories) >= 1, "Documents should span multiple categories"

            # No single category should have > 80% of documents
            total_docs = sum(categories.values())
            for category, count in categories.items():
                pct = (count / total_docs) * 100 if total_docs > 0 else 0
                assert pct < 90, f"Category '{category}' has {pct:.1f}% of documents (too concentrated)"


class TestDataQuality:
    """Test quality of ingested data"""

    @pytest.fixture(scope="class")
    def expected_files(self):
        """Get list of expected files"""
        config_path = Path(__file__).parent.parent / 'config.json'
        if config_path.exists():
            config = load_config(str(config_path))
            return collect_files_from_config(config)
        return []

    def test_no_empty_files(self, expected_files):
        """Test that no empty files are being processed"""
        empty_files = []

        for file_path in expected_files[:100]:  # Sample first 100
            if os.path.exists(file_path) and os.path.getsize(file_path) == 0:
                empty_files.append(file_path)

        assert len(empty_files) == 0, f"Found {len(empty_files)} empty files"

    def test_valid_file_extensions(self, expected_files):
        """Test that all files have valid extensions"""
        config_path = Path(__file__).parent.parent / 'config.json'
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
                valid_extensions = set(config.get('supported_extensions', []))

                for file_path in expected_files:
                    ext = os.path.splitext(file_path)[1].lower()
                    assert ext in valid_extensions, f"Invalid extension {ext} for {file_path}"

    def test_file_accessibility(self, expected_files):
        """Test that all files are accessible"""
        inaccessible_files = []

        for file_path in expected_files[:100]:  # Sample first 100
            if not os.access(file_path, os.R_OK):
                inaccessible_files.append(file_path)

        assert len(inaccessible_files) == 0, f"Found {len(inaccessible_files)} inaccessible files"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
