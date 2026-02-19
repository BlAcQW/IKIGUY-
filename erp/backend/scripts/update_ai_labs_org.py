"""
Update AI Labs Organization Settings

Sets the organization address, logo, and other letterhead information.
Run this script to update the AI Labs organization in the database.

Usage:
    python -m scripts.update_ai_labs_org
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv


async def update_ai_labs_organization():
    """Update AI Labs organization with correct address and logo."""

    # Load environment variables
    load_dotenv("/opt/kasaai/.env")

    # Connect to MongoDB
    mongo_uri = os.getenv("MONGO_URI", "mongodb://admin:aawwER4444%25@127.0.0.1:27017/")
    client = AsyncIOMotorClient(mongo_uri)
    db = client["erp"]

    # AI Labs organization details
    org_update = {
        "display_name": "AI Labs Africa",
        "name": "ai-labs-africa",
        "description": "Artificial Intelligence Solutions for Africa",
        "industry": "Technology / Artificial Intelligence",
        "website": "https://ailabsafrica.com",
        "phone": "+233 (0) XXX XXX XXX",  # Update with actual phone
        "email": "info@ailabsafrica.com",

        # Legacy address (for backwards compatibility)
        "address": "HNO DA701, Cloverleaf St., Accra, Ghana",

        # Structured billing address
        "billing_address": {
            "street": "HNO DA701, Cloverleaf St.",
            "street2": "",
            "city": "Accra",
            "state": "Greater Accra Region",
            "postal_code": "",
            "country": "Ghana"
        },

        # Branding - logo from shared/branding
        # Using local path for now - TODO: Upload to CDN/public storage
        "logo_url": "/shared/branding/ailabsafrica_logo.png",  # Served via backend static files

        "primary_color": "#0066CC",
        "secondary_color": "#333333",
        "accent_color": "#00CC66",

        # Invoice settings
        "invoice_settings": {
            "invoice_prefix": "AILAB",
            "invoice_number_start": 1000,
            "next_invoice_number": 1000,
            "default_payment_terms": "Net 30",
            "tax_id": "",  # Add VAT/Tax ID if applicable
            "tax_label": "VAT",
            "header_text": "AI Labs Africa",
            "footer_text": "Thank you for your business!",
            "show_logo": True,
            "show_payment_instructions": True
        }
    }

    # Find AI Labs organization (assume it exists or create it)
    org = await db.organizations.find_one({"name": "ai-labs-africa"})

    if org:
        # Update existing organization
        result = await db.organizations.update_one(
            {"id": org["id"]},
            {"$set": org_update}
        )
        print(f"✅ Updated AI Labs Africa organization (ID: {org['id']})")
        print(f"   Matched: {result.matched_count}, Modified: {result.modified_count}")
    else:
        # Create new organization
        import uuid
        org_update["id"] = str(uuid.uuid4())
        org_update["is_active"] = True
        org_update["created_at"] = datetime.utcnow()
        org_update["updated_at"] = datetime.utcnow()
        org_update["settings"] = {}

        await db.organizations.insert_one(org_update)
        print(f"✅ Created AI Labs Africa organization (ID: {org_update['id']})")

    # Display current settings
    updated_org = await db.organizations.find_one({"name": "ai-labs-africa"})
    print("\n📄 Current Organization Settings:")
    print(f"   Name: {updated_org['display_name']}")
    print(f"   Address: {updated_org['address']}")
    print(f"   Email: {updated_org['email']}")
    print(f"   Logo URL: {updated_org.get('logo_url', 'Not set')}")

    if updated_org.get("billing_address"):
        addr = updated_org["billing_address"]
        print(f"   Billing Address:")
        print(f"      {addr.get('street', '')}")
        if addr.get('street2'):
            print(f"      {addr.get('street2')}")
        print(f"      {addr.get('city', '')}, {addr.get('state', '')}")
        print(f"      {addr.get('country', '')}")

    client.close()
    print("\n✅ Done!")


if __name__ == "__main__":
    from datetime import datetime
    asyncio.run(update_ai_labs_organization())
