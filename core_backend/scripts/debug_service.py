#!/usr/bin/env python3
"""Debug the assistant service directly."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set environment variables
os.environ["MONGODB_URL"] = "mongodb://admin:aawwER4444%25@127.0.0.1:27017/kasaai_core?authSource=admin"
os.environ["MONGO_CORE_DATABASE"] = "kasaai_core"

from backend.services.assistant_service import assistant_service

print("Testing assistant_service.get_all_assistants()...")
try:
    assistants = assistant_service.get_all_assistants()
    print(f"Found {len(assistants)} assistants")
    
    for i, assistant in enumerate(assistants[:3], 1):
        print(f"\n{i}. {assistant.name}")
        print(f"   ID: {assistant.id}")
        print(f"   Status: {assistant.status}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n\nTesting direct MongoDB query...")
from pymongo import MongoClient

client = MongoClient(os.environ["MONGODB_URL"])
db = client[os.environ["MONGO_CORE_DATABASE"]]
collection = db["assistants"]

docs = list(collection.find().limit(3))
print(f"Direct MongoDB query found {len(docs)} documents")
for doc in docs:
    print(f"  - {doc.get('name')}: {doc.get('id')}")