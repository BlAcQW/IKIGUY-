"""
Upload Initial Impact 2025 Brochure.

This script uploads the ACI Impact 2025 brochure to the database
and makes it available for download on the landing page.
"""

import asyncio
import os
import sys
from datetime import datetime
from bson import ObjectId
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), "../../../../.env")
load_dotenv(env_path)

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import connect_to_mongodb, close_mongodb_connection, get_database


async def upload_brochure():
    """Upload the ACI Impact 2025 brochure."""

    print("🚀 Starting brochure upload...")

    # Connect to database
    await connect_to_mongodb()
    db = get_database()

    try:
        # Find the Impact 2025 conference
        conference = await db.conferences.find_one({"name": {"$regex": "impact.*2025", "$options": "i"}})

        if not conference:
            print("❌ Impact 2025 conference not found in database")
            print("   Please create the conference first")
            return

        conference_id = conference["_id"]
        conference_name = conference["name"]
        print(f"✅ Found conference: {conference_name} ({conference_id})")

        # Get default organization
        org = await db.organizations.find_one({"name": "ai-labs-ltd"})
        if not org:
            print("❌ Default organization not found")
            return

        org_id = org["_id"]
        print(f"✅ Found organization: {org['display_name']} ({org_id})")

        # Get admin user
        admin_user = await db.users.find_one({"email": "admin@ailabsafrica.com"})
        if not admin_user:
            print("❌ Admin user not found")
            return

        admin_id = admin_user["_id"]
        print(f"✅ Found admin user: {admin_user['email']} ({admin_id})")

        # Check if brochure file exists
        brochure_path = "aci-impact-2025-brochure.pdf"
        storage_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "storage", "conference_materials"
        )
        full_path = os.path.join(storage_dir, brochure_path)

        if not os.path.exists(full_path):
            print(f"❌ Brochure file not found: {full_path}")
            return

        file_size = os.path.getsize(full_path)
        print(f"✅ Found brochure file: {full_path} ({file_size} bytes)")

        # Check if material already exists
        existing = await db.conference_materials.find_one({
            "conference_id": conference_id,
            "file_path": brochure_path
        })

        if existing:
            print(f"ℹ️  Brochure already uploaded (ID: {existing['_id']})")
            print("   Updating to display on landing page...")

            # Update to show on landing page
            await db.conference_materials.update_one(
                {"_id": existing["_id"]},
                {"$set": {
                    "display_on_landing": True,
                    "is_public": True,
                    "display_order": 1,
                    "updated_at": datetime.utcnow()
                }}
            )

            print("✅ Updated brochure settings")
            return

        # Create material document
        material = {
            "conference_id": conference_id,
            "organization_id": org_id,
            "title": "ACI Impact 2025 Conference Brochure",
            "description": "Official conference brochure with schedule, speakers, and event information",
            "file_name": "ACI IMPACT 2025 BROCHURE 2.pdf",
            "file_path": brochure_path,
            "file_size": file_size,
            "file_type": "application/pdf",
            "material_type": "brochure",
            "is_public": True,
            "display_on_landing": True,
            "display_order": 1,
            "uploaded_by": admin_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        result = await db.conference_materials.insert_one(material)

        print(f"✅ Uploaded brochure successfully!")
        print(f"   Material ID: {result.inserted_id}")
        print(f"   Download URL: /api/v1/conference-materials/{result.inserted_id}/download")
        print(f"   Will be displayed on landing page for {conference_name}")

    except Exception as e:
        print(f"❌ Error uploading brochure: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await close_mongodb_connection()
        print("✅ Database connection closed")


if __name__ == "__main__":
    asyncio.run(upload_brochure())
