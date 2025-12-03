#!/usr/bin/env python3
"""
Waste Management RAG System using Gemini File Search API
"""

import os
import time
import json
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class WasteRAGSystem:
    def __init__(self):
        """Initialize the Waste RAG System with Gemini API"""
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        self.client = genai
        self.file_search_store = None
        self.model = None
        
        # System prompt for waste management
        self.system_prompt = """You are a waste management expert assistant with access to comprehensive waste management documentation, regulations, and best practices. Your role is to provide accurate, actionable guidance on:

- Waste classification and categorization
- Proper disposal methods for different waste types
- Local and federal waste management regulations
- Recycling guidelines and procedures
- Hazardous waste handling protocols
- Cost-effective waste reduction strategies
- Environmental compliance requirements

When answering questions:
1. Always cite specific sources from the uploaded documentation
2. Provide step-by-step instructions when applicable
3. Include relevant safety warnings for hazardous materials
4. Mention any regulatory compliance requirements
5. Suggest alternative disposal methods when available
6. Consider environmental impact in your recommendations

If you're unsure about specific regulations or procedures, clearly state the limitations and recommend consulting with local authorities or waste management professionals."""

    def create_file_search_store(self, store_name="waste-management-docs"):
        """Initialize file list for waste management documents"""
        try:
            # Note: Gemini uses individual file uploads rather than a 'store'
            # We'll track uploaded files in a list
            self.file_search_store = {
                'name': store_name,
                'files': []
            }
            print(f"Initialized file tracking for: {store_name}")
            return self.file_search_store
        except Exception as e:
            print(f"Error initializing file tracking: {e}")
            return None

    def upload_file(self, file_path, metadata=None, chunking_config=None, display_name=None):
        """Upload a file using Gemini File API"""
        if not self.file_search_store:
            print("No file tracking initialized. Create one first.")
            return None

        # Check if file type is supported by Gemini
        file_ext = Path(file_path).suffix.lower()
        supported_types = {'.pdf', '.txt', '.html', '.css', '.js', '.py', '.md', '.csv', '.xml', '.rtf'}

        if file_ext not in supported_types:
            print(f"[SKIP] Unsupported file type {file_ext}: {Path(file_path).name}")
            return None

        try:
            # Upload file using genai.upload_file()
            uploaded_file = self.client.upload_file(
                path=file_path,
                display_name=display_name or Path(file_path).name
            )

            # Wait for file to be processed
            while uploaded_file.state.name == "PROCESSING":
                time.sleep(2)
                uploaded_file = self.client.get_file(uploaded_file.name)

            if uploaded_file.state.name == "FAILED":
                print(f"[FAIL] Failed to process: {Path(file_path).name}")
                return None

            # Add to our tracked files
            self.file_search_store['files'].append(uploaded_file)

            print(f"[OK] Uploaded: {Path(file_path).name}")
            return uploaded_file
        except Exception as e:
            print(f"[ERROR] Error uploading {Path(file_path).name}: {str(e)[:100]}")
            return None

    def upload_directory(self, directory_path):
        """Upload all supported files from a directory"""
        if not os.path.exists(directory_path):
            print(f"Directory not found: {directory_path}")
            return
            
        supported_extensions = {'.pdf', '.txt', '.docx', '.xlsx', '.csv', '.json', '.py', '.js', '.md'}
        
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                file_ext = os.path.splitext(file)[1].lower()
                
                if file_ext in supported_extensions:
                    self.upload_file(file_path)

    def initialize_model(self):
        """Initialize the Gemini model with uploaded files"""
        if not self.file_search_store:
            print("No file tracking initialized. Create and populate one first.")
            return None

        try:
            self.model_name = "gemini-2.0-flash-exp"
            uploaded_files = self.file_search_store.get('files', [])

            if not uploaded_files:
                print("Warning: No files uploaded yet. Upload files before asking questions.")

            print(f"Using model: {self.model_name}")
            print(f"Files available: {len(uploaded_files)}")
            self.model = True  # Flag to indicate model is ready
            print("Model initialized successfully")
            return self.model
        except Exception as e:
            print(f"Error initializing model: {e}")
            return None

    def ask_question(self, question, metadata_filter=None):
        """Ask a question about waste management using uploaded files"""
        if not self.model:
            print("Model not initialized. Call initialize_model() first.")
            return None

        try:
            # Get uploaded files
            uploaded_files = self.file_search_store.get('files', [])

            # Limit files to avoid API limits (max 20 files per request for gemini-2.0-flash-exp)
            # For large document sets, this samples a subset.
            # Future enhancement: implement semantic search to select relevant files
            max_files_per_query = 20
            files_to_use = uploaded_files[:max_files_per_query] if len(uploaded_files) > max_files_per_query else uploaded_files

            # Create model with system instruction
            model = self.client.GenerativeModel(
                model_name=self.model_name,
                system_instruction=self.system_prompt
            )

            # Create prompt with context
            prompt_parts = [question]

            # Add limited files as context if available
            if files_to_use:
                prompt_parts.extend(files_to_use)

            response = model.generate_content(prompt_parts)

            # Print citations/sources if available
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                    print("\nSources:")
                    for source in candidate.grounding_metadata.grounding_chunks:
                        if hasattr(source, 'web'):
                            print(f"- {source.web.title}: {source.web.uri}")

            return response.text
        except Exception as e:
            print(f"Error generating response: {e}")
            import traceback
            traceback.print_exc()
            return None

    def interactive_session(self):
        """Start an interactive Q&A session"""
        print("Waste Management RAG System - Interactive Session")
        print("Type 'quit' to exit")
        print("-" * 50)
        
        while True:
            question = input("\nYour question: ").strip()
            if question.lower() in ['quit', 'exit', 'q']:
                break
                
            if not question:
                continue
                
            print("\nThinking...")
            answer = self.ask_question(question)
            if answer:
                print(f"\nAnswer:\n{answer}")

if __name__ == "__main__":
    # Example usage
    rag_system = WasteRAGSystem()
    
    # Create file search store
    rag_system.create_file_search_store("waste-management-docs")
    
    # Upload files (uncomment and modify path as needed)
    # rag_system.upload_directory("./waste_documents")
    
    # Initialize model
    rag_system.initialize_model()
    
    # Start interactive session
    rag_system.interactive_session()