#!/usr/bin/env python3
"""
Rebuild ChromaDB from documentation files
This script reinitializes the vector database from scratch
"""

import os
import shutil
from pathlib import Path

# Remove corrupted database
chroma_path = Path(__file__).parent / "chroma_db"
if chroma_path.exists():
    print(f"🗑️  Removing corrupted database at {chroma_path}")
    try:
        shutil.rmtree(chroma_path, ignore_errors=True)
    except Exception as e:
        print(f"Warning: Could not fully remove old database: {e}")
        print("Continuing anyway...")

# Create fresh directory
chroma_path.mkdir(exist_ok=True)
print(f"✅ Created fresh chroma_db directory")

# Now import and initialize vectorizer
print("📦 Initializing vectorizer...")
from vectorize import DocumentVectorizer

vectorizer = DocumentVectorizer(persist_directory=str(chroma_path))
print("✅ Vectorizer initialized")

# Check for existing documents
docs_path = Path(__file__).parent.parent / "docs"
if not docs_path.exists():
    print("⚠️  No docs folder found - vector database will be empty")
    print("   Add documentation and run this script again")
    exit(0)

# Find all ESP folders
esp_folders = [f for f in docs_path.iterdir() if f.is_dir() and not f.name.startswith('.')]
print(f"\n📚 Found {len(esp_folders)} ESP folders:")
for esp in esp_folders:
    doc_files = list(esp.glob("*.txt"))
    print(f"  - {esp.name}: {len(doc_files)} documents")

# Vectorize all documents
print("\n🔄 Vectorizing documents...")
total_docs = 0
for esp_folder in esp_folders:
    esp_name = esp_folder.name
    doc_files = list(esp_folder.glob("*.txt"))

    if not doc_files:
        print(f"  ⚠️  Skipping {esp_name} (no .txt files)")
        continue

    print(f"  📝 Processing {esp_name}...")
    try:
        vectorizer.refresh_esp(esp_name)
        total_docs += len(doc_files)
        print(f"     ✅ Added {len(doc_files)} documents")
    except Exception as e:
        print(f"     ❌ Error: {e}")

print(f"\n✅ Database rebuilt with {total_docs} documents")
print(f"📍 Location: {chroma_path}")
