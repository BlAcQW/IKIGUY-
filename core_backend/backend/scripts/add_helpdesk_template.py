"""
Script to add the helpdesk automation template to the database.
"""

import asyncio
import sys
import os
from datetime import datetime, timezone

# Add the backend to the path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from mongo import get_collection
from templates.helpdesk_automation_template import create_helpdesk_automation_template

async def add_helpdesk_template():
    """Add the helpdesk automation template to the database."""
    try:
        # Get the automation templates collection
        templates_collection = get_collection("automation_templates")

        # Create the template
        template = create_helpdesk_automation_template()

        # Check if template already exists
        existing = templates_collection.find_one({"id": template["id"]})
        if existing:
            print(f"Template {template['id']} already exists. Updating...")
            result = templates_collection.update_one(
                {"id": template["id"]},
                {"$set": template}
            )
            print(f"Updated template. Modified count: {result.modified_count}")
        else:
            print(f"Adding new template: {template['template_name']}")
            result = templates_collection.insert_one(template)
            print(f"Inserted template with ID: {result.inserted_id}")

        # Verify the template was added/updated
        saved_template = templates_collection.find_one({"id": template["id"]})
        if saved_template:
            print(f"✅ Template successfully saved:")
            print(f"   - Name: {saved_template['template_name']}")
            print(f"   - Industry: {saved_template['industry_name']}")
            print(f"   - Category: {saved_template['category']}")
            print(f"   - Version: {saved_template['version']}")
            print(f"   - Tools: {len(saved_template['tools'])}")
            print(f"   - Integrations: {len(saved_template['integrations'])}")
        else:
            print("❌ Failed to save template")

    except Exception as e:
        print(f"Error adding template: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(add_helpdesk_template())