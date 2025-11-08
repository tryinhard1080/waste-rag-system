#!/usr/bin/env python3
"""
Process Construction_Development folder for Waste RAG System
Handles 347 documents with metadata extraction and progress tracking
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
from waste_rag import WasteRAGSystem

class ConstructionDevProcessor:
    def __init__(self, source_folder):
        self.source_folder = Path(source_folder)
        self.rag_system = WasteRAGSystem()
        self.processed_files = []
        self.failed_files = []
        self.log_file = "construction_dev_processing.log"
        
    def extract_metadata_from_path(self, file_path):
        """Extract metadata from file path and properties"""
        path_parts = file_path.parts
        
        # Find Construction_Development in path to determine category
        try:
            cd_index = path_parts.index('Construction_Development')
            if cd_index + 1 < len(path_parts):
                category = path_parts[cd_index + 1]
            else:
                category = 'root'
        except ValueError:
            category = 'unknown'
        
        # Get file stats
        stat = file_path.stat()
        
        metadata = [
            {"key": "category", "string_value": category},
            {"key": "department", "string_value": "construction_development"},
            {"key": "file_size", "numeric_value": stat.st_size},
            {"key": "date_modified", "string_value": datetime.fromtimestamp(stat.st_mtime).isoformat()},
            {"key": "date_processed", "string_value": datetime.now().isoformat()},
            {"key": "file_extension", "string_value": file_path.suffix.lower()}
        ]
        
        # Add subcategory if available
        if cd_index + 2 < len(path_parts):
            subcategory = path_parts[cd_index + 2]
            metadata.append({"key": "subcategory", "string_value": subcategory})
            
        return metadata
    
    def scan_files(self):
        """Scan the source folder for supported files"""
        supported_extensions = {'.pdf', '.txt', '.docx', '.doc', '.xlsx', '.xls', '.csv', '.json', '.xml', '.md', '.rtf'}
        
        files = []
        print(f"Scanning {self.source_folder} for supported files...")
        
        for file_path in self.source_folder.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                files.append(file_path)
        
        print(f"Found {len(files)} supported files")
        return files
    
    def categorize_files(self, files):
        """Categorize files by type and location"""
        categories = {}
        
        for file_path in files:
            metadata = self.extract_metadata_from_path(file_path)
            category = next((m["string_value"] for m in metadata if m["key"] == "category"), "unknown")
            
            if category not in categories:
                categories[category] = []
            categories[category].append(file_path)
        
        print("\\nFile distribution by category:")
        for category, file_list in categories.items():
            print(f"  {category}: {len(file_list)} files")
        
        return categories
    
    def log_progress(self, message):
        """Log progress to file and console"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        
        print(log_entry)
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + '\\n')
    
    def process_files(self, files, batch_size=10):
        """Process files in batches with progress tracking"""
        total_files = len(files)
        
        # Create file search store
        store_name = f"construction-dev-{datetime.now().strftime('%Y%m%d')}"
        self.log_progress(f"Creating file search store: {store_name}")
        
        if not self.rag_system.create_file_search_store(store_name):
            self.log_progress("Failed to create file search store")
            return False
        
        # Process files with progress bar
        with tqdm(total=total_files, desc="Processing files") as pbar:
            for i, file_path in enumerate(files):
                try:
                    # Extract metadata
                    metadata = self.extract_metadata_from_path(file_path)
                    
                    # Create display name
                    display_name = f"{file_path.parent.name}/{file_path.name}"
                    
                    # Upload file
                    operation = self.rag_system.upload_file(
                        str(file_path),
                        metadata=metadata,
                        display_name=display_name
                    )
                    
                    if operation:
                        self.processed_files.append({
                            'file': str(file_path),
                            'metadata': metadata,
                            'timestamp': datetime.now().isoformat()
                        })
                    else:
                        self.failed_files.append(str(file_path))
                        
                except Exception as e:
                    self.log_progress(f"Error processing {file_path}: {e}")
                    self.failed_files.append(str(file_path))
                
                pbar.update(1)
                
                # Small delay to avoid rate limiting
                if (i + 1) % batch_size == 0:
                    time.sleep(1)
        
        # Save processing results
        self.save_results()
        return True
    
    def save_results(self):
        """Save processing results to JSON files"""
        results = {
            'processed_files': self.processed_files,
            'failed_files': self.failed_files,
            'total_processed': len(self.processed_files),
            'total_failed': len(self.failed_files),
            'processing_date': datetime.now().isoformat()
        }
        
        with open('construction_dev_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        self.log_progress(f"Processing complete: {len(self.processed_files)} successful, {len(self.failed_files)} failed")
    
    def run(self):
        """Main processing workflow"""
        self.log_progress("Starting Construction_Development folder processing")
        
        # Scan for files
        files = self.scan_files()
        if not files:
            self.log_progress("No files found to process")
            return
        
        # Categorize files
        categories = self.categorize_files(files)
        
        # Ask user to confirm processing
        print(f"\\nReady to process {len(files)} files from Construction_Development")
        print("Categories found:")
        for category, file_list in categories.items():
            print(f"  - {category}: {len(file_list)} files")
        
        confirm = input("\\nProceed with processing? (y/n): ").strip().lower()
        if confirm != 'y':
            print("Processing cancelled")
            return
        
        # Process files
        success = self.process_files(files)
        
        if success:
            # Initialize model
            self.log_progress("Initializing model")
            if self.rag_system.initialize_model():
                print("\\nSystem ready for questions!")
                print("You can now run: python waste_rag.py")
            else:
                self.log_progress("Failed to initialize model")
        
        print(f"\\nProcessing log saved to: {self.log_file}")
        print(f"Results saved to: construction_dev_results.json")

def main():
    source_folder = r"C:\\Users\\richard.bates\\Greystar\\AdvSol-Advantage Waste - Working Folders\\Strategy\\SOP_AWS buildout\\Construction_Development"
    
    if not os.path.exists(source_folder):
        print(f"Source folder not found: {source_folder}")
        print("Please update the path in the script")
        return
    
    processor = ConstructionDevProcessor(source_folder)
    processor.run()

if __name__ == "__main__":
    main()