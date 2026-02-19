"""
Delete deprecated VAPI tools from VAPI platform and MongoDB.

This script removes the 9 deprecated search tools that have been replaced
by superior RAG-powered query tools.
"""

import os
import httpx
import json
from datetime import datetime
from pymongo import MongoClient
from urllib.parse import quote_plus

# VAPI Configuration
VAPI_API_KEY = os.getenv("VAPI_API_KEY", "42cf1e7c-2ef9-4bd7-ba30-52f2813605a2")
VAPI_BASE_URL = os.getenv("VAPI_BASE_URL", "https://api.vapi.ai")

# MongoDB Configuration
# Properly encode the password
username = "admin"
password = quote_plus("aawwER444444")
MONGODB_URL = f"mongodb://{username}:{password}@127.0.0.1:27017/kasaai_core?authSource=admin"

# Deprecated Tool IDs
DEPRECATED_TOOLS = {
    "premier_health": [
        {
            "vapi_id": "91680cf0-fc9d-4a59-b65a-8ea2ececcac7",
            "name": "search_healthcare_providers"
        },
        {
            "vapi_id": "74e8e539-776f-4fc6-ba2f-46aa241722be",
            "name": "get_emergency_providers"
        },
        {
            "vapi_id": "f0f98b68-ade8-4a01-ae0a-d09a9dc39c6f",
            "name": "get_provider_details"
        },
        {
            "vapi_id": "271078e4-1fae-4b7c-a36d-eb810fe8724d",
            "name": "get_providers_by_area"
        },
        {
            "vapi_id": "57b96294-2181-4a44-be58-96c932f33839",
            "name": "get_providers_by_specialty"
        }
    ],
    "ghana_tourism": [
        {
            "vapi_id": "0f990d82-280c-4067-84f9-dac988fd2552",
            "name": "search_destinations"
        },
        {
            "vapi_id": "e6f657ba-f7db-4e68-908f-4066ac00b80b",
            "name": "get_destination_details"
        },
        {
            "vapi_id": "3db2b3cd-daf8-491d-8daa-b746b1d150b2",
            "name": "search_accommodation"
        },
        {
            "vapi_id": "7e50fda0-71b5-4929-8d52-32bf66caf801",
            "name": "get_accommodation_details"
        }
    ]
}


def delete_vapi_tool(tool_id: str, tool_name: str) -> dict:
    """
    Delete a tool from VAPI platform.

    Args:
        tool_id: VAPI tool ID
        tool_name: Tool name for logging

    Returns:
        dict: Deletion result
    """
    try:
        headers = {
            "Authorization": f"Bearer {VAPI_API_KEY}",
            "Content-Type": "application/json"
        }

        print(f"   Deleting: {tool_name} ({tool_id})")

        with httpx.Client(timeout=30.0) as client:
            response = client.delete(
                f"{VAPI_BASE_URL}/tool/{tool_id}",
                headers=headers
            )

            if response.status_code in [200, 204]:
                print(f"   ✅ Deleted from VAPI")
                return {"status": "success", "tool_id": tool_id}
            else:
                print(f"   ⚠️  VAPI deletion failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return {
                    "status": "failed",
                    "tool_id": tool_id,
                    "error": response.text,
                    "status_code": response.status_code
                }

    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")
        return {"status": "error", "tool_id": tool_id, "error": str(e)}


def delete_mongo_tool(collection, vapi_tool_id: str) -> dict:
    """
    Delete a tool from MongoDB custom_tools collection.

    Args:
        collection: MongoDB collection
        vapi_tool_id: VAPI tool ID

    Returns:
        dict: Deletion result
    """
    try:
        result = collection.delete_one({"vapi_tool_id": vapi_tool_id})
        if result.deleted_count > 0:
            print(f"   ✅ Deleted from MongoDB")
            return {"status": "success", "deleted_count": result.deleted_count}
        else:
            print(f"   ⚠️  Not found in MongoDB")
            return {"status": "not_found", "deleted_count": 0}
    except Exception as e:
        print(f"   ❌ MongoDB error: {str(e)}")
        return {"status": "error", "error": str(e)}


def main():
    """
    Main function to delete deprecated tools from VAPI and MongoDB.
    """
    print("=" * 80)
    print("Deprecated VAPI Tools Deletion Script")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"VAPI API: {VAPI_BASE_URL}")
    print(f"MongoDB: {MONGODB_URL.split('@')[1] if '@' in MONGODB_URL else 'localhost'}")
    print("=" * 80)

    # Connect to MongoDB
    try:
        mongo_client = MongoClient(MONGODB_URL)
        db = mongo_client.kasaai_core
        custom_tools = db.custom_tools
        print("\n✅ Connected to MongoDB")
    except Exception as e:
        print(f"\n❌ MongoDB connection failed: {str(e)}")
        return

    results = {
        "vapi_deletions": [],
        "mongo_deletions": [],
        "errors": []
    }

    # Delete Premier Health tools
    print("\n" + "=" * 80)
    print("Deleting Premier Health Deprecated Tools (5 tools)")
    print("=" * 80)

    for tool in DEPRECATED_TOOLS["premier_health"]:
        print(f"\n🗑️  Tool: {tool['name']}")

        # Delete from VAPI
        vapi_result = delete_vapi_tool(tool["vapi_id"], tool["name"])
        results["vapi_deletions"].append({
            "tool_name": tool["name"],
            "vapi_id": tool["vapi_id"],
            "result": vapi_result
        })

        # Delete from MongoDB
        mongo_result = delete_mongo_tool(custom_tools, tool["vapi_id"])
        results["mongo_deletions"].append({
            "tool_name": tool["name"],
            "vapi_id": tool["vapi_id"],
            "result": mongo_result
        })

    # Delete Ghana Tourism tools
    print("\n" + "=" * 80)
    print("Deleting Ghana Tourism Deprecated Tools (4 tools)")
    print("=" * 80)

    for tool in DEPRECATED_TOOLS["ghana_tourism"]:
        print(f"\n🗑️  Tool: {tool['name']}")

        # Delete from VAPI
        vapi_result = delete_vapi_tool(tool["vapi_id"], tool["name"])
        results["vapi_deletions"].append({
            "tool_name": tool["name"],
            "vapi_id": tool["vapi_id"],
            "result": vapi_result
        })

        # Delete from MongoDB
        mongo_result = delete_mongo_tool(custom_tools, tool["vapi_id"])
        results["mongo_deletions"].append({
            "tool_name": tool["name"],
            "vapi_id": tool["vapi_id"],
            "result": mongo_result
        })

    # Summary
    print("\n" + "=" * 80)
    print("Deletion Summary")
    print("=" * 80)

    vapi_success = sum(1 for d in results["vapi_deletions"] if d["result"]["status"] == "success")
    mongo_success = sum(1 for d in results["mongo_deletions"] if d["result"]["status"] == "success")

    print(f"\n✅ VAPI Deletions: {vapi_success}/9 successful")
    print(f"✅ MongoDB Deletions: {mongo_success}/9 successful")

    # Save results
    output_file = "/opt/kasaai/apps/automations/examples/tool_deletion_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n📄 Results saved to: {output_file}")
    print("=" * 80)
    print("✅ Deletion complete!")
    print("=" * 80)

    # Close MongoDB connection
    mongo_client.close()


if __name__ == "__main__":
    main()
