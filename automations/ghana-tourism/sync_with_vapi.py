#!/usr/bin/env python3
"""
Sync Ghana Tourism Board tools with VAPI platform.
This will register each tool with VAPI and get vapi_tool_id for each.
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from apps.core_backend.backend.services.custom_tools_service import CustomToolsService


async def sync_ghana_tourism_tools():
    """Sync Ghana Tourism Board tools with VAPI platform."""
    service = CustomToolsService()

    client_id = "ghana-tourism-board"

    print("="*70)
    print("🇬🇭 Syncing Ghana Tourism Board Tools with VAPI Platform")
    print("="*70)
    print()
    print(f"📦 Client ID: {client_id}")
    print()

    try:
        # First, check how many tools we have
        filter_query = {"active": True, "client_id": client_id}
        tools = await service.tools_collection.find(filter_query).to_list(None)
        print(f"🔍 Found {len(tools)} active tools for {client_id}")
        for tool in tools:
            print(f"   - {tool['name']}")
        print()

        # Bulk sync all tools for this client
        print("🔄 Starting VAPI sync...")
        result = await service.bulk_sync_tools_with_vapi(client_id=client_id)
        print(f"📦 Sync result type: {type(result)}")
        print(f"📦 Sync result keys: {result.keys() if result else 'None'}")
        print(f"📦 Full result: {result}")
        print()

        print("✅ VAPI Sync Complete!")
        print()
        print(f"📊 Results:")
        print(f"   Successful: {len(result.get('successful', []))}")
        print(f"   Failed: {len(result.get('failed', []))}")
        print()

        if result.get('successful'):
            print(f"🎉 Successfully synced tools ({len(result['successful'])}):")
            for tool in result['successful']:
                print(f"   ✓ {tool['name']}")
                print(f"     - MongoDB ID: {tool['tool_id']}")
                print(f"     - VAPI Tool ID: {tool.get('vapi_tool_id', 'N/A')}")
                print()

        if result.get('failed'):
            print(f"❌ Failed to sync tools ({len(result['failed'])}):")
            for tool in result['failed']:
                print(f"   ✗ {tool['name']}")
                print(f"     - MongoDB ID: {tool['tool_id']}")
                print(f"     - Error: {tool.get('error', 'Unknown error')}")
                print()

        return result

    except Exception as e:
        print(f"❌ Sync failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = asyncio.run(sync_ghana_tourism_tools())

    if result and len(result.get('successful', [])) > 0:
        print("="*70)
        print("✅ Ghana Tourism Board tools are now registered with VAPI!")
        print("="*70)
        print()
        print("🎯 Next steps:")
        print("1. Create system prompt for tourism voice agent")
        print("2. Test tools with sample inputs")
        print("3. Deploy in QuickAutomationDeployment UI")
        sys.exit(0)
    else:
        print("❌ Sync failed or no tools were synced")
        sys.exit(1)
