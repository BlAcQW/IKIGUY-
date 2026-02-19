#!/usr/bin/env python3
"""
COMPREHENSIVE TEMPLATE MIGRATION SCRIPT
Extracts ALL templates from automation-templates.ts and creates them in the database.
Only creates templates that don't already exist.
"""

import re
import json
import requests
import time
from datetime import datetime

API_BASE = "https://api.ailabsafrica.com/automation-templates"
HEADERS = {
    "Authorization": "Bearer test",
    "Content-Type": "application/json"
}

def get_existing_templates():
    """Get all existing templates from database."""
    try:
        response = requests.get(f"{API_BASE}/list", headers=HEADERS)
        if response.status_code == 200:
            templates = response.json()
            existing = set()
            for template in templates:
                existing.add((template['template_name'], template['industry']))
            return existing
        else:
            print(f"❌ Failed to fetch existing templates: {response.status_code}")
            return set()
    except Exception as e:
        print(f"❌ Error fetching existing templates: {e}")
        return set()

def extract_templates_from_config():
    """Extract templates from automation-templates.ts file."""
    templates = []

    try:
        with open('src/config/automation-templates.ts', 'r') as f:
            content = f.read()

        # Extract the AUTOMATION_TEMPLATES array
        template_array_match = re.search(r'export const AUTOMATION_TEMPLATES[^=]*=\s*\[(.*?)\];', content, re.DOTALL)
        if not template_array_match:
            print("❌ Could not find AUTOMATION_TEMPLATES array")
            return []

        templates_content = template_array_match.group(1)

        # Split templates by finding complete objects
        # This is a simplified approach - looking for template objects
        template_objects = []
        brace_count = 0
        current_template = ""
        in_template = False

        for line in templates_content.split('\n'):
            stripped = line.strip()
            if not stripped or stripped.startswith('//'):
                continue

            # Count braces to track object boundaries
            open_braces = stripped.count('{')
            close_braces = stripped.count('}')

            if '{' in stripped and (stripped.strip().startswith('{') or ('id:' in stripped or 'name:' in stripped)):
                in_template = True
                current_template = line + '\n'
                brace_count = open_braces - close_braces
            elif in_template:
                current_template += line + '\n'
                brace_count += open_braces - close_braces

                if brace_count <= 0:
                    # End of template object
                    template_objects.append(current_template)
                    current_template = ""
                    in_template = False
                    brace_count = 0

        print(f"📋 Found {len(template_objects)} template objects to parse")

        # Parse each template object
        for i, template_str in enumerate(template_objects):
            try:
                template_data = parse_template_object(template_str)
                if template_data:
                    templates.append(template_data)
            except Exception as e:
                print(f"⚠️  Error parsing template {i+1}: {e}")
                continue

        print(f"✅ Successfully parsed {len(templates)} templates")
        return templates

    except Exception as e:
        print(f"❌ Error reading automation-templates.ts: {e}")
        return []

def parse_template_object(template_str):
    """Parse a single template object string."""
    template_data = {}

    # Extract basic fields using regex
    fields = {
        'id': r"id:\s*['\"]([^'\"]+)['\"]",
        'name': r"name:\s*['\"]([^'\"]+)['\"]",
        'description': r"description:\s*['\"]([^'\"]+)['\"]",
        'industry': r"industry:\s*['\"]([^'\"]+)['\"]",
        'category': r"category:\s*['\"]([^'\"]+)['\"]",
        'complexity': r"complexity:\s*['\"]([^'\"]+)['\"]",
        'estimatedTime': r"estimatedTime:\s*['\"]([^'\"]+)['\"]"
    }

    for field, pattern in fields.items():
        match = re.search(pattern, template_str, re.IGNORECASE)
        if match:
            template_data[field] = match.group(1)

    # Validate required fields
    required_fields = ['name', 'industry', 'description']
    for field in required_fields:
        if field not in template_data:
            print(f"⚠️  Missing required field '{field}' in template")
            return None

    # Set defaults for missing fields
    if 'category' not in template_data:
        template_data['category'] = 'automation'
    if 'complexity' not in template_data:
        template_data['complexity'] = 'Medium'
    if 'estimatedTime' not in template_data:
        template_data['estimatedTime'] = '30 min'

    return template_data

def create_template_via_api(template_data):
    """Create a template via the API."""
    # Map frontend fields to API fields
    api_data = {
        "template_name": template_data['name'],
        "industry": template_data['industry'],
        "category": template_data['category'],
        "description": template_data['description'],
        "company_name": f"{template_data['industry'].replace('_', ' ').title()} Company"
    }

    try:
        response = requests.post(f"{API_BASE}/create", headers=HEADERS, json=api_data)
        if response.status_code == 200:
            result = response.json()
            return True, result
        else:
            error_msg = f"HTTP {response.status_code}"
            if response.text:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('detail', error_msg)
                except:
                    error_msg = response.text[:100]
            return False, error_msg
    except Exception as e:
        return False, str(e)

def main():
    """Main migration function."""
    print("🚀 COMPREHENSIVE TEMPLATE MIGRATION")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Get existing templates
    print("📊 Fetching existing templates from database...")
    existing_templates = get_existing_templates()
    print(f"✅ Found {len(existing_templates)} existing templates")
    print()

    # Extract templates from config
    print("📋 Extracting templates from automation-templates.ts...")
    frontend_templates = extract_templates_from_config()
    print(f"✅ Extracted {len(frontend_templates)} templates from frontend")
    print()

    # Filter out existing templates
    new_templates = []
    skipped_templates = []

    for template in frontend_templates:
        template_key = (template['name'], template['industry'])
        if template_key in existing_templates:
            skipped_templates.append(template)
        else:
            new_templates.append(template)

    print(f"🔄 Templates to migrate: {len(new_templates)}")
    print(f"⏭️  Templates to skip (already exist): {len(skipped_templates)}")
    print()

    if not new_templates:
        print("✅ No new templates to migrate. All templates are already in the database!")
        return

    # Group by industry for better organization
    by_industry = {}
    for template in new_templates:
        industry = template['industry']
        if industry not in by_industry:
            by_industry[industry] = []
        by_industry[industry].append(template)

    print("📈 Templates to migrate by industry:")
    for industry, templates in sorted(by_industry.items()):
        print(f"   {industry.upper()}: {len(templates)} templates")
    print()

    # Start migration
    print("🔄 Starting migration...")
    print("=" * 60)

    created_count = 0
    failed_count = 0
    failed_templates = []

    for industry, templates in sorted(by_industry.items()):
        print(f"\n🏢 MIGRATING {industry.upper()} ({len(templates)} templates)")
        print("-" * 40)

        for i, template in enumerate(templates, 1):
            print(f"  {i:2d}. {template['name'][:60]}{'...' if len(template['name']) > 60 else ''}", end=" ")

            success, result = create_template_via_api(template)

            if success:
                print("✅")
                created_count += 1
            else:
                print(f"❌ ({result})")
                failed_count += 1
                failed_templates.append({
                    'name': template['name'],
                    'industry': template['industry'],
                    'error': result
                })

            # Small delay between requests
            time.sleep(0.3)

    # Final summary
    print("\n" + "=" * 60)
    print("📊 MIGRATION SUMMARY")
    print("=" * 60)
    print(f"✅ Successfully created: {created_count} templates")
    print(f"❌ Failed to create: {failed_count} templates")
    print(f"⏭️  Skipped (already exist): {len(skipped_templates)} templates")
    print(f"📋 Total processed: {len(frontend_templates)} templates")

    if failed_templates:
        print(f"\n❌ FAILED TEMPLATES:")
        for failed in failed_templates:
            print(f"   • {failed['name']} ({failed['industry']}) - {failed['error']}")

    # Get final database count
    print("\n📊 Final database status:")
    try:
        response = requests.get(f"{API_BASE}/list", headers=HEADERS)
        if response.status_code == 200:
            templates = response.json()

            final_by_industry = {}
            for template in templates:
                industry = template.get('industry', 'Unknown')
                if industry not in final_by_industry:
                    final_by_industry[industry] = 0
                final_by_industry[industry] += 1

            print(f"   Total templates in database: {len(templates)}")
            for industry, count in sorted(final_by_industry.items()):
                print(f"   {industry}: {count} templates")
    except:
        print("   Could not fetch final counts")

    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎉 Migration complete!")

if __name__ == "__main__":
    main()