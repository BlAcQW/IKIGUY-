#!/usr/bin/env python3
"""Test materials API directly"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import MongoDB
from app.services.material_service import MaterialService


async def main():
    """Test fetching materials."""
    try:
        # Connect to database
        print("Connecting to database...")
        await MongoDB.connect()
        print("✅ Connected!")

        # Fetch materials
        print("\nFetching materials...")
        materials = await MaterialService.list_materials(limit=10)

        print(f"\n✅ Found {len(materials)} materials")

        if materials:
            print("\n📚 Materials:")
            for m in materials:
                print(f"   • {m.title} - Grade {m.grade} {m.subject}")
                print(f"     Status: {m.status}, Type: {m.file_type}")
        else:
            print("\n⚠️  No materials found!")

            # Let's check the raw database
            print("\nChecking raw database...")
            collection = MongoDB.get_collection("learning_materials")
            count = await collection.count_documents({})
            print(f"Total documents in collection: {count}")

            if count > 0:
                doc = await collection.find_one({})
                print(f"\nSample document fields: {list(doc.keys())}")
                print(f"Sample file_type: {doc.get('file_type')}")
                print(f"Sample status: {doc.get('status')}")

        # Disconnect
        await MongoDB.disconnect()

    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
