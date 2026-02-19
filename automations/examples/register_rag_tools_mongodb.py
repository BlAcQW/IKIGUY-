"""
Register Premier Health and Ghana Tourism RAG tools in MongoDB custom_tools collection.

This script registers the RAG tools in MongoDB so they appear in the custom tools UI
and are properly integrated with tool call logging.

Usage:
    python register_rag_tools_mongodb.py
"""

import os
import sys
from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId

# Add parent directory to path for imports
sys.path.insert(0, '/opt/kasaai/apps/core_backend')

# MongoDB Configuration
MONGODB_URL = os.getenv('MONGODB_URL', 'mongodb://admin:aawwER444444@127.0.0.1:27017/?authSource=admin')

# VAPI Tool IDs (these tools are already registered on VAPI platform)
PREMIER_HEALTH_VAPI_TOOL_ID = '560adfee-43bf-4614-baa8-0d5ccfbe9769'
GHANA_TOURISM_VAPI_TOOL_ID = '2bac26dc-5f8e-4d3d-82b2-ca55286ddf36'

# RAG API Configuration
FLOW_API_BASE_URL = "https://flow-api.ailabsafrica.com"


def get_premier_health_tool_doc():
    """Get Premier Health RAG tool document for MongoDB."""
    return {
        "name": "query_premier_health_knowledge_base",
        "description": "Query the Premier Health Insurance knowledge base for comprehensive information about healthcare providers, medical services, insurance coverage, and facilities in Ghana. Supports filtering by insurance plan type (PLATINUM PLUS, PLATINUM, MERCURY, REGULAR).",
        "tool_type": "rag_query",
        "client_id": "premier_health_production",
        "industry": "healthcare",
        "category": "provider_search",
        "is_active": True,
        "vapi_tool_id": PREMIER_HEALTH_VAPI_TOOL_ID,
        "config": {
            "server_url": f"{FLOW_API_BASE_URL}/knowledge-base/premier_health_production/query",
            "timeout_seconds": 20,
            "knowledge_base": "premier_health_production",
            "function_name": "query_premier_health_knowledge_base",
            "parameters_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language search query. Examples: 'doctors in madina', 'pediatricians near me', 'emergency hospitals in accra'"
                    },
                    "company_name": {
                        "type": "string",
                        "description": "Company identifier for the knowledge base",
                        "default": "premier_health_production"
                    },
                    "plan_type": {
                        "type": "string",
                        "description": "Optional insurance plan type filter",
                        "enum": ["PLATINUM PLUS", "PLATINUM", "MERCURY", "REGULAR"]
                    }
                },
                "required": ["query"]
            },
            "messages": {
                "request_start": "Let me search for that information...",
                "request_failed": "I couldn't access the Premier Health database. Let me try to help you another way."
            }
        },
        "metadata": {
            "company": "Premier Health Insurance Ghana",
            "total_facilities": 755,
            "total_documents": 403,
            "regions_covered": [
                "Greater Accra", "Ashanti", "Western", "Central", "Eastern", "Volta",
                "Northern", "Upper East", "Upper West", "Bono", "Bono East", "Ahafo"
            ],
            "features": [
                "Healthcare provider search",
                "Insurance plan filtering",
                "City/location normalization",
                "Specialty filtering",
                "Voice recognition support"
            ],
            "integration_type": "VAPI Function Tool",
            "rag_technology": "LangChain + PGVector + Gemini 2.5 Flash"
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "created_by": "system",
        "tags": [
            "rag",
            "healthcare",
            "premier-health",
            "knowledge-base",
            "vapi",
            "insurance",
            "provider-search"
        ]
    }


def get_ghana_tourism_tool_doc():
    """Get Ghana Tourism RAG tool document for MongoDB."""
    return {
        "name": "query_ghana_tourism_knowledge_base",
        "description": "Query the Ghana Tourism Board knowledge base for comprehensive travel information including tourist destinations, attractions, accommodations, cultural sites, travel requirements, safety information, and practical travel tips for Ghana.",
        "tool_type": "rag_query",
        "client_id": "ghana_tourism_board",
        "industry": "tourism",
        "category": "travel_information",
        "is_active": True,
        "vapi_tool_id": GHANA_TOURISM_VAPI_TOOL_ID,
        "config": {
            "server_url": f"{FLOW_API_BASE_URL}/knowledge-base/ghana_tourism_board/query",
            "timeout_seconds": 20,
            "knowledge_base": "ghana_tourism_board",
            "function_name": "query_ghana_tourism_knowledge_base",
            "parameters_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language search query. Examples: 'tourist attractions in ghana', 'hotels in accra', 'visa requirements for ghana'"
                    },
                    "company_name": {
                        "type": "string",
                        "description": "Company identifier for the knowledge base",
                        "default": "ghana_tourism_board"
                    }
                },
                "required": ["query"]
            },
            "messages": {
                "request_start": "Let me search for that information...",
                "request_failed": "I couldn't access the tourism database right now. Let me provide general information instead."
            }
        },
        "metadata": {
            "company": "Ghana Tourism Board",
            "features": [
                "Tourist destination search",
                "Hotel and accommodation info",
                "Cultural sites and attractions",
                "Travel requirements",
                "Safety information",
                "Local customs and tips"
            ],
            "integration_type": "VAPI Function Tool",
            "rag_technology": "LangChain + PGVector + Gemini 2.5 Flash"
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "created_by": "system",
        "tags": [
            "rag",
            "tourism",
            "ghana-tourism",
            "knowledge-base",
            "vapi",
            "travel",
            "destinations"
        ]
    }


def register_tools_in_mongodb():
    """
    Register both RAG tools in MongoDB custom_tools collection.
    """
    print("=" * 80)
    print("MongoDB RAG Tools Registration Script")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"MongoDB: {MONGODB_URL.split('@')[1] if '@' in MONGODB_URL else MONGODB_URL}")
    print("=" * 80)

    try:
        # Connect to MongoDB
        print("\n🔌 Connecting to MongoDB...")
        client = MongoClient(MONGODB_URL)
        db = client['kasaai_core']
        custom_tools_collection = db['custom_tools']

        # Check if tools already exist
        print("\n🔍 Checking for existing tools...")

        premier_exists = custom_tools_collection.find_one({
            "name": "query_premier_health_knowledge_base"
        })

        tourism_exists = custom_tools_collection.find_one({
            "name": "query_ghana_tourism_knowledge_base"
        })

        results = {
            "premier_health": {"status": "skipped", "action": "none"},
            "ghana_tourism": {"status": "skipped", "action": "none"}
        }

        # Register or update Premier Health tool
        print("\n📋 Processing Premier Health RAG Tool...")
        premier_doc = get_premier_health_tool_doc()

        if premier_exists:
            print(f"   ⚠️  Tool already exists (ID: {premier_exists['_id']})")
            print("   🔄 Updating existing document...")
            result = custom_tools_collection.update_one(
                {"_id": premier_exists['_id']},
                {"$set": {**premier_doc, "_id": premier_exists['_id']}}
            )
            results["premier_health"] = {
                "status": "updated",
                "action": "updated",
                "id": str(premier_exists['_id']),
                "matched": result.matched_count,
                "modified": result.modified_count
            }
            print(f"   ✅ Updated (matched: {result.matched_count}, modified: {result.modified_count})")
        else:
            print("   ➕ Inserting new document...")
            result = custom_tools_collection.insert_one(premier_doc)
            results["premier_health"] = {
                "status": "created",
                "action": "inserted",
                "id": str(result.inserted_id)
            }
            print(f"   ✅ Created (ID: {result.inserted_id})")

        # Register or update Ghana Tourism tool
        print("\n📋 Processing Ghana Tourism RAG Tool...")
        tourism_doc = get_ghana_tourism_tool_doc()

        if tourism_exists:
            print(f"   ⚠️  Tool already exists (ID: {tourism_exists['_id']})")
            print("   🔄 Updating existing document...")
            result = custom_tools_collection.update_one(
                {"_id": tourism_exists['_id']},
                {"$set": {**tourism_doc, "_id": tourism_exists['_id']}}
            )
            results["ghana_tourism"] = {
                "status": "updated",
                "action": "updated",
                "id": str(tourism_exists['_id']),
                "matched": result.matched_count,
                "modified": result.modified_count
            }
            print(f"   ✅ Updated (matched: {result.matched_count}, modified: {result.modified_count})")
        else:
            print("   ➕ Inserting new document...")
            result = custom_tools_collection.insert_one(tourism_doc)
            results["ghana_tourism"] = {
                "status": "created",
                "action": "inserted",
                "id": str(result.inserted_id)
            }
            print(f"   ✅ Created (ID: {result.inserted_id})")

        # Summary
        print("\n" + "=" * 80)
        print("Registration Summary")
        print("=" * 80)

        for tool_name, result in results.items():
            print(f"\n{tool_name}:")
            print(f"  Status: {result['status']}")
            print(f"  Action: {result['action']}")
            print(f"  MongoDB ID: {result.get('id', 'N/A')}")

        print("\n" + "=" * 80)
        print("✅ Registration complete!")
        print("\n📍 Tools are now visible at: https://flow.ailabsafrica.com/custom-tools")
        print("📊 Tool call logs will be properly integrated with the UI")
        print("=" * 80)

        return True

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'client' in locals():
            client.close()


if __name__ == "__main__":
    success = register_tools_in_mongodb()
    sys.exit(0 if success else 1)
