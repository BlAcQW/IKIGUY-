"""
Update existing Premier Health and Ghana Tourism RAG VAPI tools with fixed response handling.

This script updates the tool configurations to remove the hardcoded request-complete message
that was blocking the actual tool response data.

Usage:
    python update_rag_vapi_tools.py
"""

import os
import httpx
import json
from datetime import datetime

# VAPI Configuration
VAPI_API_KEY = os.getenv("VAPI_API_KEY", "42cf1e7c-2ef9-4bd7-ba30-52f2813605a2")
VAPI_BASE_URL = os.getenv("VAPI_BASE_URL", "https://api.vapi.ai")

# RAG API Configuration
FLOW_API_BASE_URL = "https://flow-api.ailabsafrica.com"

# Tool IDs from registration
PREMIER_HEALTH_TOOL_ID = "560adfee-43bf-4614-baa8-0d5ccfbe9769"
GHANA_TOURISM_TOOL_ID = "2bac26dc-5f8e-4d3d-82b2-ca55286ddf36"


def update_vapi_tool(tool_id: str, tool_config: dict) -> dict:
    """
    Update an existing tool on VAPI platform.

    Args:
        tool_id: Existing tool ID
        tool_config: Updated tool configuration dictionary

    Returns:
        VAPI tool update response
    """
    try:
        headers = {
            "Authorization": f"Bearer {VAPI_API_KEY}",
            "Content-Type": "application/json"
        }

        print(f"\n🔧 Updating tool: {tool_id}")
        print(f"   Function: {tool_config['function']['name']}")
        print(f"   Server URL: {tool_config['server']['url']}")

        with httpx.Client(timeout=30.0) as client:
            response = client.patch(
                f"{VAPI_BASE_URL}/tool/{tool_id}",
                headers=headers,
                json=tool_config
            )

            if response.status_code in [200, 201]:
                result = response.json()
                print(f"   ✅ Success! Tool updated")
                return result
            else:
                print(f"   ❌ Error: {response.status_code}")
                print(f"   Response: {response.text}")
                return {"error": response.text, "status_code": response.status_code}

    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")
        return {"error": str(e)}


def get_premier_health_tool_config():
    """Get fixed Premier Health tool configuration."""
    return {
        "async": False,
        "messages": [
            {
                "type": "request-start",
                "content": "Let me search for that information..."
            },
            {
                "type": "request-failed",
                "content": "I couldn't access the Premier Health database. Let me try to help you another way."
            }
            # NOTE: request-complete message REMOVED to allow tool response to pass through
        ],
        "function": {
            "name": "query_premier_health_knowledge_base",
            "description": "Query the Premier Health Insurance knowledge base for comprehensive information about healthcare providers, medical services, insurance coverage, and facilities in Ghana. Use this when customers ask about doctors, hospitals, clinics, medical specialists, provider locations, or insurance coverage details. This tool uses advanced RAG (Retrieval Augmented Generation) to provide accurate, up-to-date information from the Premier Health provider network. Supports filtering by insurance plan type.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language search query. Examples: 'doctors in madina', 'pediatricians near me', 'emergency hospitals in accra', 'what specialties are available', 'providers in east legon'"
                    },
                    "company_name": {
                        "type": "string",
                        "description": "Company identifier for the knowledge base",
                        "default": "premier_health_production"
                    },
                    "plan_type": {
                        "type": "string",
                        "description": "Optional insurance plan type filter. Valid values: 'PLATINUM PLUS', 'PLATINUM', 'MERCURY', 'REGULAR'. Use this when users mention their insurance plan or ask about facilities accepting specific coverage tiers. Examples: 'plat plus', 'platinum', 'mercury plan', 'regular plan', 'standard coverage'",
                        "enum": ["PLATINUM PLUS", "PLATINUM", "MERCURY", "REGULAR"]
                    }
                },
                "required": ["query"]
            }
        },
        "server": {
            "url": f"{FLOW_API_BASE_URL}/knowledge-base/premier_health_production/query",
            "timeoutSeconds": 20
        }
    }


def get_ghana_tourism_tool_config():
    """Get fixed Ghana Tourism tool configuration."""
    return {
        "async": False,
        "messages": [
            {
                "type": "request-start",
                "content": "Let me search for that information..."
            },
            {
                "type": "request-failed",
                "content": "I couldn't access the tourism database right now. Let me provide general information instead."
            }
            # NOTE: request-complete message REMOVED to allow tool response to pass through
        ],
        "function": {
            "name": "query_ghana_tourism_knowledge_base",
            "description": "Query the Ghana Tourism Board knowledge base for comprehensive travel information including tourist destinations, attractions, accommodations, cultural sites, travel requirements, safety information, and practical travel tips for Ghana. Use this when travelers ask about places to visit, hotels, tourist attractions, visa requirements, local customs, safety tips, or general travel information about Ghana. This tool uses RAG technology to provide accurate, detailed tourism information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language search query. Examples: 'tourist attractions in ghana', 'hotels in accra', 'visa requirements for ghana', 'what to do in cape coast', 'best time to visit ghana', 'cultural sites near kumasi'"
                    },
                    "company_name": {
                        "type": "string",
                        "description": "Company identifier for the knowledge base",
                        "default": "ghana_tourism_board"
                    }
                },
                "required": ["query"]
            }
        },
        "server": {
            "url": f"{FLOW_API_BASE_URL}/knowledge-base/ghana_tourism_board/query",
            "timeoutSeconds": 20
        }
    }


def main():
    """
    Main function to update both RAG tools on VAPI platform.
    """
    print("=" * 80)
    print("VAPI RAG Tools Update Script - Fix Response Handling")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"VAPI API: {VAPI_BASE_URL}")
    print(f"Flow API: {FLOW_API_BASE_URL}")
    print()
    print("🔍 ISSUE IDENTIFIED:")
    print("   The hardcoded 'request-complete' message was blocking tool responses.")
    print("   Fix: Remove request-complete to let actual RAG data pass through.")
    print("=" * 80)

    # Update Premier Health RAG tool
    print("\n📋 Updating Premier Health RAG Tool")
    premier_config = get_premier_health_tool_config()
    premier_result = update_vapi_tool(PREMIER_HEALTH_TOOL_ID, premier_config)

    # Update Ghana Tourism RAG tool
    print("\n📋 Updating Ghana Tourism RAG Tool")
    tourism_config = get_ghana_tourism_tool_config()
    tourism_result = update_vapi_tool(GHANA_TOURISM_TOOL_ID, tourism_config)

    # Summary
    print("\n" + "=" * 80)
    print("Update Summary")
    print("=" * 80)

    results = {
        "premier_health_rag": {
            "tool_id": PREMIER_HEALTH_TOOL_ID,
            "status": "success" if "id" in premier_result else "failed",
            "error": premier_result.get("error")
        },
        "ghana_tourism_rag": {
            "tool_id": GHANA_TOURISM_TOOL_ID,
            "status": "success" if "id" in tourism_result else "failed",
            "error": tourism_result.get("error")
        }
    }

    # Print results
    for tool_name, result in results.items():
        print(f"\n{tool_name}:")
        print(f"  Tool ID: {result['tool_id']}")
        print(f"  Status: {result['status']}")
        if result['status'] != 'success':
            print(f"  Error: {result['error']}")

    # Save results to file
    output_file = "/opt/kasaai/apps/automations/examples/rag_tools_update_result.json"
    with open(output_file, 'w') as f:
        json.dump({
            "updated_at": datetime.now().isoformat(),
            "results": results
        }, f, indent=2)

    print(f"\n📄 Results saved to: {output_file}")
    print("=" * 80)

    # Test the fix
    print("\n🧪 Testing the fix:")
    print("\nExpected behavior BEFORE fix:")
    print("   User: 'Find doctors in Madina'")
    print("   Assistant: 'Let me search... Found relevant information from Premier Health.' ❌ STOPS HERE")
    print()
    print("Expected behavior AFTER fix:")
    print("   User: 'Find doctors in Madina'")
    print("   Assistant: 'Let me search...'")
    print("   Assistant: 'Here are the facilities in the MADINA region that offer General Practice:'")
    print("              '- ESIDEM HOSPITAL'")
    print("              '- CROWN MEDICAL CENTRE'")
    print("              '- ADENTA CLINIC'")
    print("              '... etc' ✅ ACTUALLY SPEAKS THE RESULTS")

    print("\n" + "=" * 80)
    print("✅ Update complete!")
    print("\n⚠️  IMPORTANT: Test with a call to verify the fix works")
    print("=" * 80)


if __name__ == "__main__":
    main()
