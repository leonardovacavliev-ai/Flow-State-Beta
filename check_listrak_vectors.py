#!/usr/bin/env python3
"""Check if Listrak vectors exist in Pinecone with correct metadata"""

import os
from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()

pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index = pc.Index('esp-loyalty-docs1')

print("=== Searching for Listrak vectors ===\n")

# Try querying with filter
dummy_vector = [0.0] * 384
results = index.query(
    vector=dummy_vector,
    top_k=10,
    filter={"esp": {"$eq": "listrak"}},
    include_metadata=True
)

if results.matches:
    print(f"✓ Found {len(results.matches)} vectors with esp='listrak' metadata\n")
    for i, match in enumerate(results.matches[:5], 1):
        print(f"{i}. ID: {match.id}")
        print(f"   Score: {match.score}")
        print(f"   Metadata: {match.metadata}")
        print()
else:
    print("✗ No vectors found with esp='listrak' filter")
    print("\nLet's check what ESP values exist...")

    # Query without filter to see what's there
    results_all = index.query(
        vector=dummy_vector,
        top_k=20,
        include_metadata=True
    )

    esp_values = {}
    for match in results_all.matches:
        esp = match.metadata.get('esp', 'NONE')
        filename = match.metadata.get('filename', 'unknown')

        if 'listrak' in filename.lower() or 'listrak' in str(match.metadata).lower():
            print(f"\nFound Listrak-related vector:")
            print(f"  ID: {match.id}")
            print(f"  ESP metadata: {esp}")
            print(f"  Filename: {filename}")
            print(f"  Full metadata: {match.metadata}")

        if esp not in esp_values:
            esp_values[esp] = 0
        esp_values[esp] += 1

    print(f"\n=== ESP value distribution (sample of 20) ===")
    for esp, count in sorted(esp_values.items()):
        print(f"  {esp}: {count}")
