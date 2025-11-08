#!/usr/bin/env python3
"""
Setup GitHub repository for Advantage Waste RAG system
"""

import os
import json
from pathlib import Path

def create_github_structure():
    """Create the recommended GitHub repository structure"""
    
    structure = {
        'src': 'Source code for the RAG system',
        'config': 'Configuration files and templates',
        'docs': 'Documentation and guides', 
        'tests': 'Test files and test data',
        'scripts': 'Utility scripts for maintenance',
        'logs': 'Processing logs and analytics',
        'results': 'Processing results and reports'
    }
    
    print("Creating GitHub repository structure...")
    
    for folder, description in structure.items():
        folder_path = Path(folder)
        folder_path.mkdir(exist_ok=True)
        
        # Create README for each folder
        readme_path = folder_path / 'README.md'
        with open(readme_path, 'w') as f:
            f.write(f"# {folder.capitalize()}\n\n{description}\n")
        
        print(f"✓ Created {folder}/")
    
    return structure

def create_project_readme():
    """Create main project README"""
    
    readme_content = """# Advantage Waste RAG System

A comprehensive knowledge base system for waste management using Google's Gemini File Search API.

## Overview

This system processes and indexes waste management documents to provide expert-level Q&A capabilities using Retrieval-Augmented Generation (RAG).

## Quick Start

1. **Setup Environment**
   ```bash
   pip install -r requirements.txt
   cp .env.example .env
   # Add your Gemini API key to .env
   ```

2. **Process Documents**
   ```bash
   python process_construction_dev.py
   ```

3. **Start Q&A Session**
   ```bash
   python waste_rag.py
   ```

## Repository Structure

- `src/` - Core RAG system code
- `config/` - Configuration files
- `docs/` - Documentation and guides
- `scripts/` - Utility scripts
- `logs/` - Processing logs
- `results/` - Processing results and reports

## Document Processing

The system automatically:
- Extracts metadata from file paths and properties
- Organizes documents by category (Agreements, Consultants, Framework, etc.)
- Handles chunking and embedding via Gemini File Search API
- Provides progress tracking and error handling

## Features

- **Automatic Document Processing**: OCR, chunking, and embedding
- **Metadata Extraction**: Category, department, file size, dates
- **Progress Tracking**: Real-time progress bars and logging
- **Error Handling**: Retry logic and failure tracking
- **Organized Storage**: Category-based organization with metadata filtering
- **Citation Support**: Automatic source tracking in responses

## Configuration

Edit `config/config.json` to customize:
- File sources and patterns
- Supported file extensions
- Chunking parameters
- Model selection

## Usage Examples

```python
from src.waste_rag import WasteRAGSystem

# Initialize system
rag = WasteRAGSystem()
rag.create_file_search_store("my-docs")
rag.upload_file("document.pdf", metadata=[...])
rag.initialize_model()

# Ask questions with metadata filtering
answer = rag.ask_question(
    "How do I dispose of construction waste?",
    metadata_filter="category=Framework"
)
```

## Processing Results

After processing, check:
- `logs/construction_dev_processing.log` - Detailed processing log
- `results/construction_dev_results.json` - Processing summary and results

## API Costs

- Storage: Free
- Embedding generation: $0.15 per 1M tokens (one-time cost)
- Query embeddings: Free
- Retrieved tokens: Standard context pricing

## Support

For issues or questions:
1. Check the logs in `logs/`
2. Review the documentation in `docs/`
3. Contact the development team
"""
    
    with open('README.md', 'w') as f:
        f.write(readme_content)
    
    print("✓ Created README.md")

def move_files_to_structure():
    """Move existing files to proper structure"""
    
    moves = {
        'waste_rag.py': 'src/',
        'waste_rag_cli.py': 'src/',
        'upload_from_config.py': 'src/',
        'process_construction_dev.py': 'scripts/',
        'config.json': 'config/',
        'CLAUDE.md': 'docs/',
        'requirements.txt': './',
        '.env': './',
        '.env.example': './',
        '.gitignore': './'
    }
    
    print("\\nMoving files to proper structure...")
    
    for file, dest in moves.items():
        if Path(file).exists():
            dest_path = Path(dest)
            dest_path.mkdir(exist_ok=True)
            
            if dest != './':
                new_path = dest_path / file
                Path(file).rename(new_path)
                print(f"  Moved {file} → {dest}")

def create_gitignore():
    """Create comprehensive .gitignore"""
    
    gitignore_content = """# Environment variables
.env

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
.venv/
venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
logs/*.log
*.log

# Results and temporary files
results/*.json
temp/
tmp/

# Large files (use Git LFS if needed)
*.pdf
*.docx
*.xlsx
*.pptx
data/
documents/

# API keys and secrets
secrets/
keys/
credentials/

# Generated documentation
docs/_build/
"""
    
    with open('.gitignore', 'w') as f:
        f.write(gitignore_content)
    
    print("✓ Created .gitignore")

def create_git_commands():
    """Create Git setup commands"""
    
    commands = """#!/bin/bash
# Git repository setup commands

echo "Setting up Git repository..."

# Initialize repository
git init

# Add all files
git add .

# First commit
git commit -m "Initial commit: Advantage Waste RAG System

🤖 Generated with Claude Code (https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

echo "Repository initialized!"
echo ""
echo "Next steps:"
echo "1. Create repository on GitHub"
echo "2. git remote add origin https://github.com/yourusername/advantage-waste-rag.git"
echo "3. git branch -M main" 
echo "4. git push -u origin main"
"""
    
    with open('setup_git.sh', 'w') as f:
        f.write(commands)
    
    # Make executable on Unix systems
    os.chmod('setup_git.sh', 0o755)
    
    print("✓ Created setup_git.sh")

def create_config_template():
    """Create enhanced configuration template"""
    
    config = {
        "file_sources": [
            {
                "name": "construction_development",
                "type": "directory", 
                "path": "C:/Users/richard.bates/Greystar/AdvSol-Advantage Waste - Working Folders/Strategy/SOP_AWS buildout/Construction_Development",
                "recursive": True,
                "extensions": [".pdf", ".docx", ".txt", ".xlsx"],
                "metadata": {
                    "department": "construction_development",
                    "priority": "high"
                }
            }
        ],
        "supported_extensions": [
            ".pdf", ".txt", ".docx", ".doc", ".xlsx", ".xls", 
            ".csv", ".json", ".xml", ".md", ".rtf", ".pptx"
        ],
        "chunking": {
            "max_tokens_per_chunk": 400,
            "max_overlap_tokens": 40
        },
        "store_name": "advantage-waste-docs",
        "model": "gemini-2.5-pro",
        "processing": {
            "batch_size": 10,
            "retry_attempts": 3,
            "delay_between_batches": 1
        }
    }
    
    config_dir = Path('config')
    config_dir.mkdir(exist_ok=True)
    
    with open(config_dir / 'config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✓ Created config/config.json")

def main():
    """Main setup function"""
    print("🚀 Setting up Advantage Waste RAG GitHub Repository")
    print("=" * 50)
    
    # Create structure
    create_github_structure()
    
    # Create documentation
    create_project_readme()
    create_gitignore()
    create_git_commands()
    create_config_template()
    
    # Move files (optional)
    move_files = input("\\nMove existing files to new structure? (y/n): ").strip().lower()
    if move_files == 'y':
        move_files_to_structure()
    
    print("\\n✅ GitHub repository setup complete!")
    print("\\nNext steps:")
    print("1. Review the created structure")
    print("2. Update config/config.json with your paths") 
    print("3. Run: bash setup_git.sh")
    print("4. Create GitHub repository and push")
    print("5. Run: python scripts/process_construction_dev.py")

if __name__ == "__main__":
    main()