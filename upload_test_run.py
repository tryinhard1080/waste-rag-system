#!/usr/bin/env python3
"""
Test run upload - Upload subset of files for validation
"""

import json
import os
import glob
import time
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from waste_rag import WasteRAGSystem
from tqdm import tqdm


def load_config(config_path='config.json'):
    """Load configuration from JSON file"""
    with open(config_path, 'r') as f:
        return json.load(f)


def collect_test_files(config, limit=15):
    """Collect a limited subset of files for testing"""
    files_to_upload = []

    for source in config.get('file_sources', []):
        source_type = source.get('type')

        if source_type == 'directory':
            path = source.get('path')
            recursive = source.get('recursive', False)
            extensions = source.get('extensions', config.get('supported_extensions', []))

            if os.path.exists(path):
                if recursive:
                    pattern = os.path.join(path, '**', '*')
                    all_files = glob.glob(pattern, recursive=True)
                else:
                    pattern = os.path.join(path, '*')
                    all_files = glob.glob(pattern)

                for file_path in all_files:
                    if os.path.isfile(file_path):
                        file_ext = os.path.splitext(file_path)[1].lower()
                        if file_ext in extensions:
                            files_to_upload.append(file_path)

                            # Stop if we've reached the limit
                            if len(files_to_upload) >= limit:
                                return files_to_upload

    return files_to_upload


def main():
    TEST_FILE_LIMIT = 15
    start_time = time.time()

    print(f"=== TEST RUN: Uploading {TEST_FILE_LIMIT} files for validation ===\n")

    print("Loading configuration...")
    config = load_config()

    print("Initializing Waste RAG System...")
    rag_system = WasteRAGSystem()

    store_name = f"{config.get('store_name', 'waste-management-docs')}-test"
    print(f"Creating file search store: {store_name}")
    if not rag_system.create_file_search_store(store_name):
        print("Failed to create file search store.")
        return

    print(f"Collecting {TEST_FILE_LIMIT} test files from configuration...")
    files = collect_test_files(config, limit=TEST_FILE_LIMIT)

    if not files:
        print("No files found based on configuration.")
        return

    print(f"\nFound {len(files)} file(s) to upload:")
    for i, file_path in enumerate(files, 1):
        print(f"  {i}. {Path(file_path).name} ({os.path.getsize(file_path) / 1024:.1f} KB)")

    # Initialize reporting
    report = {
        'test_run': True,
        'start_time': datetime.now().isoformat(),
        'total_files': len(files),
        'successful_uploads': 0,
        'failed_uploads': [],
        'total_retries': 0,
        'extensions_processed': set(),
        'categories': defaultdict(int),
        'total_storage_mb': 0,
        'processing_times': []
    }

    print("\nUploading files...")

    for file_path in tqdm(files, desc="Uploading", unit="file"):
        file_start = time.time()
        ext = os.path.splitext(file_path)[1].lower()
        report['extensions_processed'].add(ext)

        # Try to categorize file
        if 'agreement' in file_path.lower():
            report['categories']['Agreements'] += 1
        elif 'consultant' in file_path.lower():
            report['categories']['Consultants'] += 1
        elif 'framework' in file_path.lower():
            report['categories']['Framework'] += 1
        else:
            report['categories']['Other'] += 1

        # Track file size
        if os.path.exists(file_path):
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            report['total_storage_mb'] += file_size_mb

        # Upload with retry logic
        max_retries = config.get('processing', {}).get('retry_attempts', 3)
        retry_count = 0
        uploaded = False

        while retry_count < max_retries and not uploaded:
            result = rag_system.upload_file(file_path)
            if result:
                report['successful_uploads'] += 1
                uploaded = True
            else:
                retry_count += 1
                report['total_retries'] += 1
                if retry_count < max_retries:
                    time.sleep(1)

        if not uploaded:
            report['failed_uploads'].append({
                'file': Path(file_path).name,
                'error': 'Max retries exceeded',
                'retries': retry_count
            })

        file_time = time.time() - file_start
        report['processing_times'].append(file_time)

    # Finalize report
    report['end_time'] = datetime.now().isoformat()
    report['total_processing_time_seconds'] = time.time() - start_time
    report['extensions_processed'] = list(report['extensions_processed'])
    report['categories'] = dict(report['categories'])
    report['average_processing_time_per_file'] = sum(report['processing_times']) / len(report['processing_times']) if report['processing_times'] else 0
    report['success_rate'] = (report['successful_uploads'] / report['total_files'] * 100) if report['total_files'] > 0 else 0

    print(f"\n=== TEST RUN COMPLETE ===")
    print(f"Successfully uploaded: {report['successful_uploads']}/{report['total_files']} files")
    print(f"Success rate: {report['success_rate']:.1f}%")
    print(f"Total processing time: {report['total_processing_time_seconds']:.2f} seconds")
    print(f"Average time per file: {report['average_processing_time_per_file']:.2f} seconds")
    print(f"Total storage: {report['total_storage_mb']:.2f} MB")
    print(f"Extensions processed: {', '.join(report['extensions_processed'])}")

    if report['failed_uploads']:
        print(f"\nFailed uploads ({len(report['failed_uploads'])}):")
        for failed in report['failed_uploads']:
            print(f"  - {failed['file']}: {failed['error']}")

    # Save report
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)
    report_path = logs_dir / 'test_run_report.json'

    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\nTest run report saved to: {report_path}")

    print("\nInitializing model...")
    if rag_system.initialize_model():
        print("\n[SUCCESS] System ready for testing!")
        print("\nNext steps:")
        print("1. Test Q&A: python waste_rag.py")
        print("2. Run test suite: pytest tests/ -v")
        print("3. If tests pass, run full upload: python upload_from_config.py")


if __name__ == "__main__":
    main()
