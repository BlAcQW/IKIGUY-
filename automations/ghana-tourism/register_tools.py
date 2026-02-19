#!/usr/bin/env python3
"""
Script to register Ghana Tourism Board custom tools with VAPI.
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from apps.core_backend.backend.services.custom_tools_service import CustomToolsService


async def register_ghana_tourism_tools():
    """Register Ghana Tourism Board tools with VAPI."""
    service = CustomToolsService()

    file_path = "/opt/kasaai/apps/automations/ghana-tourism/voice_agent_tools.py"
    client_id = "ghana-tourism-board"
    industry = "tourism"
    category = "tourist_information"
    description = "Tourist information and assistance tools for Ghana Tourism Board"

    print(f"🚀 Registering Ghana Tourism Board tools...")
    print(f"   File: {file_path}")
    print(f"   Client: {client_id}")
    print(f"   Industry: {industry}")
    print(f"   Category: {category}")
    print()

    try:
        result = await service.register_tool_from_file(
            file_path=file_path,
            client_id=client_id,
            industry=industry,
            category=category,
            description=description
        )

        print("✅ Registration successful!")
        print()
        print(f"📊 Results:")
        print(f"   Success: {result.get('success', False)}")
        print(f"   Tools registered: {result.get('tools_registered', 0)}")
        print()

        if result.get('tools'):
            print(f"🎉 Registered tools ({len(result['tools'])}):")
            for tool in result['tools']:
                print(f"   ✓ {tool['name']}")
                print(f"     - Endpoint: {tool.get('endpoint', 'N/A')}")
                print()

        if result.get('error'):
            print(f"⚠️ Error: {result['error']}")
            print()

        return result

    except Exception as e:
        print(f"❌ Registration failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = asyncio.run(register_ghana_tourism_tools())

    if result and result.get('tools_registered', 0) > 0:
        print("✅ Ghana Tourism Board tools are now ready to use!")
        sys.exit(0)
    else:
        print("❌ Registration failed or no tools were registered")
        sys.exit(1)
