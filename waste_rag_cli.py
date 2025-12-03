#!/usr/bin/env python3
"""
Waste Management RAG System CLI - File Ingestion and Management
"""

import os
import sys
import argparse
import glob
from pathlib import Path
from waste_rag import WasteRAGSystem

def list_supported_formats():
    """List all supported file formats"""
    formats = {
        'Documents': ['.pdf', '.docx', '.doc', '.txt', '.rtf'],
        'Spreadsheets': ['.xlsx', '.xls', '.csv'],
        'Data': ['.json', '.xml'],
        'Code': ['.py', '.js', '.html', '.css'],
        'Markdown': ['.md'],
    }
    
    print("\nSupported File Formats:")
    print("-" * 40)
    for category, extensions in formats.items():
        print(f"{category}: {', '.join(extensions)}")
    print()

def find_files_by_pattern(pattern):
    """Find files matching a glob pattern"""
    files = glob.glob(pattern, recursive=True)
    return [f for f in files if os.path.isfile(f)]

def main():
    parser = argparse.ArgumentParser(
        description='Waste Management RAG System - File Ingestion Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Upload a single file
  python waste_rag_cli.py --file "path/to/document.pdf"
  
  # Upload multiple specific files
  python waste_rag_cli.py --files "doc1.pdf" "doc2.xlsx" "regulations.txt"
  
  # Upload all PDFs in a directory
  python waste_rag_cli.py --pattern "documents/*.pdf"
  
  # Upload all files from a directory recursively
  python waste_rag_cli.py --directory "waste_documents" --recursive
  
  # Upload files and start Q&A session
  python waste_rag_cli.py --directory "docs" --interactive
  
  # List supported formats
  python waste_rag_cli.py --list-formats
        """
    )
    
    parser.add_argument('--file', '-f', 
                       help='Upload a single file')
    
    parser.add_argument('--files', nargs='+',
                       help='Upload multiple specific files')
    
    parser.add_argument('--directory', '-d',
                       help='Upload all supported files from a directory')
    
    parser.add_argument('--pattern', '-p',
                       help='Upload files matching a glob pattern (e.g., "**/*.pdf")')
    
    parser.add_argument('--recursive', '-r', action='store_true',
                       help='Include subdirectories when using --directory')
    
    parser.add_argument('--extensions', '-e', nargs='+',
                       help='Specific file extensions to include (e.g., .pdf .txt)')
    
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Start interactive Q&A session after uploading')
    
    parser.add_argument('--list-formats', action='store_true',
                       help='List all supported file formats')
    
    parser.add_argument('--store-name', default='waste-management-docs',
                       help='Name for the file search store (default: waste-management-docs)')
    
    args = parser.parse_args()
    
    # Handle list formats
    if args.list_formats:
        list_supported_formats()
        return
    
    # Check if any input method was specified
    if not any([args.file, args.files, args.directory, args.pattern]):
        print("No files specified. Use --help to see usage examples.")
        return
    
    # Initialize the RAG system
    print("Initializing Waste RAG System...")
    rag_system = WasteRAGSystem()
    
    # Create file search store
    print(f"Creating file search store: {args.store_name}")
    if not rag_system.create_file_search_store(args.store_name):
        print("Failed to create file search store. Check your API key.")
        return
    
    # Collect files to upload
    files_to_upload = []
    
    # Single file
    if args.file:
        if os.path.exists(args.file):
            files_to_upload.append(args.file)
        else:
            print(f"File not found: {args.file}")
    
    # Multiple files
    if args.files:
        for file_path in args.files:
            if os.path.exists(file_path):
                files_to_upload.append(file_path)
            else:
                print(f"File not found: {file_path}")
    
    # Directory
    if args.directory:
        if os.path.exists(args.directory):
            supported_extensions = args.extensions or ['.pdf', '.txt', '.docx', '.xlsx', '.csv', '.json', '.md']
            
            if args.recursive:
                pattern = os.path.join(args.directory, '**', '*')
                all_files = glob.glob(pattern, recursive=True)
            else:
                pattern = os.path.join(args.directory, '*')
                all_files = glob.glob(pattern)
            
            for file_path in all_files:
                if os.path.isfile(file_path):
                    file_ext = os.path.splitext(file_path)[1].lower()
                    if file_ext in supported_extensions:
                        files_to_upload.append(file_path)
        else:
            print(f"Directory not found: {args.directory}")
    
    # Pattern matching
    if args.pattern:
        matched_files = find_files_by_pattern(args.pattern)
        files_to_upload.extend(matched_files)
    
    # Remove duplicates while preserving order
    files_to_upload = list(dict.fromkeys(files_to_upload))
    
    if not files_to_upload:
        print("No files found to upload.")
        return
    
    # Upload files
    print(f"\nFound {len(files_to_upload)} file(s) to upload:")
    for file_path in files_to_upload:
        print(f"  - {file_path}")
    
    print("\nUploading files...")
    successful_uploads = 0
    for file_path in files_to_upload:
        if rag_system.upload_file(file_path):
            successful_uploads += 1
    
    print(f"\nSuccessfully uploaded {successful_uploads}/{len(files_to_upload)} files")
    
    # Initialize model
    print("\nInitializing model...")
    if not rag_system.initialize_model():
        print("Failed to initialize model")
        return
    
    # Start interactive session if requested
    if args.interactive:
        print("\nStarting interactive session...")
        rag_system.interactive_session()
    else:
        print("\nFiles uploaded successfully! You can now run:")
        print("  python waste_rag.py")
        print("to start an interactive Q&A session.")

if __name__ == "__main__":
    main()