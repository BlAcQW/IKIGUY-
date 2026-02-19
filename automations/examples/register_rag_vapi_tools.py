"""
Register Premier Health and Ghana Tourism RAG query tools on VAPI platform.

This script creates two VAPI tools that call the Knowledge Base RAG query endpoints:
1. query_premier_health_knowledge_base - For Premier Health provider queries
2. query_ghana_tourism_knowledge_base - For Ghana Tourism destination queries

Usage:
    python register_rag_vapi_tools.py
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


def create_vapi_tool(tool_config: dict) -> dict:
    """
    Create a tool on VAPI platform.

    Args:
        tool_config: Tool configuration dictionary

    Returns:
        VAPI tool creation response
    """
    try:
        headers = {
            "Authorization": f"Bearer {VAPI_API_KEY}",
            "Content-Type": "application/json"
        }

        print(f"\n🔧 Creating tool: {tool_config['function']['name']}")
        print(f"   Description: {tool_config['function']['description']}")
        print(f"   Server URL: {tool_config['server']['url']}")

        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{VAPI_BASE_URL}/tool",
                headers=headers,
                json=tool_config
            )

            if response.status_code in [200, 201]:
                result = response.json()
                print(f"   ✅ Success! Tool ID: {result.get('id')}")
                return result
            else:
                print(f"   ❌ Error: {response.status_code}")
                print(f"   Response: {response.text}")
                return {"error": response.text, "status_code": response.status_code}

    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")
        return {"error": str(e)}


def create_premier_health_rag_tool():
    """
    Create Premier Health RAG query tool.

    This tool allows VAPI assistants to query the Premier Health knowledge base
    for provider information, services, and general healthcare queries.
    """
    tool_config = {
        "type": "function",
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
        ],
        "function": {
            "name": "query_premier_health_knowledge_base",
            "description": "Query the Premier Health Insurance knowledge base for comprehensive information about healthcare providers, medical services, insurance coverage, and facilities in Ghana. Use this when customers ask about doctors, hospitals, clinics, medical specialists, provider locations, or insurance coverage details. This tool uses advanced RAG (Retrieval Augmented Generation) to provide accurate, up-to-date information from the Premier Health provider network.",
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

    return create_vapi_tool(tool_config)


def create_ghana_tourism_rag_tool():
    """
    Create Ghana Tourism Board RAG query tool.

    This tool allows VAPI assistants to query the Ghana Tourism Board knowledge base
    for destination information, attractions, accommodations, and travel tips.
    """
    tool_config = {
        "type": "function",
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

    return create_vapi_tool(tool_config)


def main():
    """
    Main function to register both RAG tools on VAPI platform.
    """
    print("=" * 80)
    print("VAPI RAG Tools Registration Script")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"VAPI API: {VAPI_BASE_URL}")
    print(f"Flow API: {FLOW_API_BASE_URL}")
    print(f"API Key: {VAPI_API_KEY[:20]}...")
    print("=" * 80)

    # Create Premier Health RAG tool
    print("\n📋 Creating Premier Health RAG Tool")
    premier_result = create_premier_health_rag_tool()

    # Create Ghana Tourism RAG tool
    print("\n📋 Creating Ghana Tourism RAG Tool")
    tourism_result = create_ghana_tourism_rag_tool()

    # Summary
    print("\n" + "=" * 80)
    print("Registration Summary")
    print("=" * 80)

    results = {
        "premier_health_rag": {
            "status": "success" if "id" in premier_result else "failed",
            "tool_id": premier_result.get("id"),
            "error": premier_result.get("error")
        },
        "ghana_tourism_rag": {
            "status": "success" if "id" in tourism_result else "failed",
            "tool_id": tourism_result.get("id"),
            "error": tourism_result.get("error")
        }
    }

    # Print results
    for tool_name, result in results.items():
        print(f"\n{tool_name}:")
        print(f"  Status: {result['status']}")
        if result['status'] == 'success':
            print(f"  Tool ID: {result['tool_id']}")
        else:
            print(f"  Error: {result['error']}")

    # Save results to file
    output_file = "/opt/kasaai/apps/automations/examples/rag_tools_registration_result.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n📄 Results saved to: {output_file}")
    print("=" * 80)

    # Print usage examples
    print("\n📚 Usage Examples:")
    print("\n1. Premier Health RAG Tool:")
    print("   - 'Find me doctors in Madina'")
    print("   - 'Are there pediatricians near East Legon?'")
    print("   - 'Emergency hospitals in Accra'")
    print("   - 'What specialties does Premier Health cover?'")

    print("\n2. Ghana Tourism RAG Tool:")
    print("   - 'What are the best tourist attractions in Ghana?'")
    print("   - 'Tell me about hotels in Cape Coast'")
    print("   - 'What are the visa requirements for Ghana?'")
    print("   - 'Cultural sites to visit in Kumasi'")

    print("\n" + "=" * 80)
    print("✅ Registration complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
