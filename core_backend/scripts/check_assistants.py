#!/usr/bin/env python3
"""Check assistants in MongoDB directly."""

import os
from pymongo import MongoClient
import json

# MongoDB connection
mongodb_url = os.getenv("MONGODB_URL", "mongodb://admin:aawwER4444%25@127.0.0.1:27017/kasaai_core?authSource=admin")
database_name = os.getenv("MONGO_CORE_DATABASE", "kasaai_core")

print(f"Connecting to MongoDB...")
print(f"Database: {database_name}")

try:
    client = MongoClient(mongodb_url)
    db = client[database_name]
    collection = db["assistants"]
    
    # Count documents
    count = collection.count_documents({})
    print(f"\nTotal assistants in database: {count}")
    
    # Get first few assistants
    assistants = list(collection.find().limit(3))
    
    if assistants:
        print("\nSample assistants:")
        for i, assistant in enumerate(assistants, 1):
            print(f"\n{i}. {assistant.get('name', 'No name')}")
            print(f"   ID: {assistant.get('id', assistant.get('_id', 'No ID'))}")
            print(f"   Status: {assistant.get('status', 'No status')}")
            print(f"   User ID: {assistant.get('user_id', 'No user_id')}")
            print(f"   Language: {assistant.get('language', 'No language')}")
    else:
        print("\nNo assistants found in database!")
        
    # Check collection names
    print(f"\nAvailable collections in {database_name}:")
    for coll_name in db.list_collection_names():
        doc_count = db[coll_name].count_documents({})
        print(f"  - {coll_name}: {doc_count} documents")
        
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    import traceback
    traceback.print_exc()
finally:
    if 'client' in locals():
        client.close()