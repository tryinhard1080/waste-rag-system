#!/usr/bin/env python3
"""
Upload files to Waste RAG System using configuration file
"""

import json
import os
import glob
import time
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from waste_rag import WasteRAGSystem

def load_config(config_path='config.json'):
    """Load configuration from JSON file"""
    with open(config_path, 'r') as f:
        return json.load(f)

def collect_files_from_config(config):
    """Collect all files specified in the configuration"""
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
                            
        elif source_type == 'pattern':
            pattern = source.get('pattern')
            matched_files = glob.glob(pattern, recursive=True)
            files_to_upload.extend([f for f in matched_files if os.path.isfile(f)])
            
        elif source_type == 'files':
            for file_path in source.get('files', []):
                if os.path.exists(file_path):
                    files_to_upload.append(file_path)
    
    # Remove duplicates
    return list(dict.fromkeys(files_to_upload))

def main():
    start_time = time.time()

    print("Loading configuration...")
    config = load_config()

    print("Initializing Waste RAG System...")
    rag_system = WasteRAGSystem()

    store_name = config.get('store_name', 'waste-management-docs')
    print(f"Creating file search store: {store_name}")
    if not rag_system.create_file_search_store(store_name):
        print("Failed to create file search store.")
        return

    print("Collecting files from configuration...")
    files = collect_files_from_config(config)

    if not files:
        print("No files found based on configuration.")
        return

    print(f"\nFound {len(files)} file(s) to upload:")
    for file_path in files[:10]:  # Show first 10 files
        print(f"  - {file_path}")
    if len(files) > 10:
        print(f"  ... and {len(files) - 10} more")

    # Initialize reporting
    report = {
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
    from tqdm import tqdm

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
            if rag_system.upload_file(file_path):
                report['successful_uploads'] += 1
                uploaded = True
            else:
                retry_count += 1
                report['total_retries'] += 1
                if retry_count < max_retries:
                    time.sleep(1)  # Brief delay before retry

        if not uploaded:
            report['failed_uploads'].append({
                'file': file_path,
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

    print(f"\nSuccessfully uploaded {report['successful_uploads']}/{report['total_files']} files")
    print(f"Success rate: {report['success_rate']:.1f}%")
    print(f"Total processing time: {report['total_processing_time_seconds']:.2f} seconds")
    print(f"Total storage: {report['total_storage_mb']:.2f} MB")

    # Save report
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)
    report_path = logs_dir / 'ingestion_report.json'

    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\nIngestion report saved to: {report_path}")

    print("\nInitializing model...")
    if rag_system.initialize_model():
        print("System ready! Run 'python waste_rag.py' to start Q&A session.")

if __name__ == "__main__":
    main()