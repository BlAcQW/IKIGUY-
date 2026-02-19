"""
Seed devotionals via API instead of direct DB insertion.
Uses the devotional creation API endpoint.
"""

import requests
import json
import re
from datetime import datetime

API_BASE_URL = "http://127.0.0.1:30042/api/v1"
ADMIN_EMAIL = "pastor@freshmanna.com"
ADMIN_PASSWORD = "Pastor@123"

# Categories mapping based on content keywords
CATEGORY_KEYWORDS = {
    "faith": ["faith", "believe", "trust", "confidence"],
    "prayer": ["prayer", "pray", "praying", "intercession"],
    "hope": ["hope", "hopeful", "expectation"],
    "love": ["love", "loving", "beloved", "charity"],
    "purpose": ["purpose", "calling", "mission", "destiny"],
    "healing": ["healing", "heal", "restore", "recovery"],
    "wisdom": ["wisdom", "wise", "understanding", "discernment"],
    "courage": ["courage", "courageous", "brave", "boldness"],
    "gratitude": ["gratitude", "grateful", "thankful", "thanks", "thanksgiving"],
    "forgiveness": ["forgiveness", "forgive", "mercy", "pardon"],
    "patience": ["patience", "patient", "endurance", "perseverance"],
    "peace": ["peace", "peaceful", "calm", "tranquility"],
    "joy": ["joy", "joyful", "rejoice", "happiness"],
    "strength": ["strength", "strong", "power", "mighty"],
    "grace": ["grace", "gracious", "favor", "mercy"],
    "obedience": ["obedience", "obey", "submit", "surrender"],
    "worship": ["worship", "praise", "adoration", "glorify"],
    "family": ["family", "marriage", "children", "parenting"],
    "service": ["service", "serve", "ministry", "help"],
    "spiritual-growth": ["growth", "maturity", "transformation", "sanctification"],
}


def get_auth_token():
    """Get authentication token."""
    print("🔐 Authenticating...")
    response = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    response.raise_for_status()
    token = response.json()["access_token"]
    print("✓ Authentication successful")
    return token


def parse_devotionals_from_file(file_path: str) -> list:
    """Parse devotionals from Fresh Manna text file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by devotional numbers
    devotionals_raw = re.split(r'\n(\d+)\s*\n', content)

    devotionals = []

    for i in range(1, len(devotionals_raw), 2):
        if i + 1 >= len(devotionals_raw):
            break

        number = devotionals_raw[i].strip()
        devotional_text = devotionals_raw[i + 1].strip()

        if not devotional_text:
            continue

        devotional = parse_single_devotional(number, devotional_text)
        if devotional:
            devotionals.append(devotional)

    return devotionals


def parse_single_devotional(number: str, text: str) -> dict:
    """Parse a single devotional from text."""
    lines = text.split('\n')

    # Extract title
    title = ""
    content_start = 0

    for i, line in enumerate(lines):
        line_clean = line.strip()
        if line_clean.startswith("Title:"):
            title = line_clean.replace("Title:", "").strip()
            content_start = i + 1
            break
        elif i == 0 and line_clean and len(line_clean) < 100:
            title = line_clean
            content_start = 1
            break

    if not title:
        title = f"Daily Devotional #{number}"

    # Clean title
    title = re.sub(r'^["\']|["\']$', '', title).strip()
    if not title:
        title = f"Faith Devotional #{number}"

    # Extract scripture references
    scripture_refs = []
    scripture_pattern = r'([A-Z][a-z]+(?: [A-Z][a-z]+)*) (\d+):(\d+(?:-\d+)?)'

    for line in lines[:10]:
        matches = re.findall(scripture_pattern, line)
        for match in matches:
            ref = f"{match[0]} {match[1]}:{match[2]}"
            if ref not in scripture_refs:
                scripture_refs.append(ref)

    # Extract content paragraphs
    content_blocks = []
    current_paragraph = []
    in_prayer = False

    for line in lines[content_start:]:
        line_clean = line.strip()

        if not line_clean:
            if current_paragraph:
                para_text = ' '.join(current_paragraph)
                if len(para_text) > 10:  # Skip very short paragraphs
                    if in_prayer:
                        content_blocks.append({
                            "type": "prayer",
                            "text": para_text
                        })
                        in_prayer = False
                    else:
                        content_blocks.append({
                            "type": "paragraph",
                            "text": para_text
                        })
                current_paragraph = []
            continue

        if line_clean.lower().startswith("prayer"):
            in_prayer = True
            continue

        current_paragraph.append(line_clean)

    # Add last paragraph
    if current_paragraph:
        para_text = ' '.join(current_paragraph)
        if len(para_text) > 10:
            if in_prayer:
                content_blocks.append({
                    "type": "prayer",
                    "text": para_text
                })
            else:
                content_blocks.append({
                    "type": "paragraph",
                    "text": para_text
                })

    # Detect categories
    categories = detect_categories(title + " " + text)
    if not categories:
        categories = ["faith"]

    # Ensure we have at least some content
    if not content_blocks:
        content_blocks = [{
            "type": "paragraph",
            "text": "May God bless you today with His word and presence."
        }]

    return {
        "title": title,
        "content": content_blocks,
        "scripture_references": scripture_refs if scripture_refs else [],
        "categories": categories,
        "status": "published"
    }


def detect_categories(text: str) -> list:
    """Detect categories based on keyword matching."""
    text_lower = text.lower()
    detected = []

    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                detected.append(category)
                break

    return detected[:3]  # Max 3 categories


def create_devotional(token: str, devotional_data: dict) -> bool:
    """Create a devotional via API."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/devotionals",
            json=devotional_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        response.raise_for_status()
        return True
    except requests.exceptions.HTTPError as e:
        print(f"  ✗ API Error: {e.response.status_code}")
        print(f"    Response: {e.response.text}")
        return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def main():
    """Main seeding function."""
    print("=" * 60)
    print("FRESH MANNA DEVOTIONALS SEEDING (via API)")
    print("=" * 60)

    # Get auth token
    try:
        token = get_auth_token()
    except Exception as e:
        print(f"✗ Authentication failed: {e}")
        return

    # Parse devotionals
    file_path = "/tmp/fresh_manna_content.txt"
    print(f"\n📖 Parsing devotionals from {file_path}...")
    devotionals = parse_devotionals_from_file(file_path)
    print(f"✓ Parsed {len(devotionals)} devotionals")

    # Seed devotionals
    print(f"\n💾 Creating devotionals via API...")
    print(f"   This may take a few minutes...\n")

    success_count = 0
    failed_count = 0

    # Seed first 50 devotionals (to avoid overwhelming)
    for i, dev_data in enumerate(devotionals[:50], 1):
        print(f"  [{i}/50] {dev_data['title'][:50]}...", end=" ")

        if create_devotional(token, dev_data):
            print("✓")
            success_count += 1
        else:
            print("✗")
            failed_count += 1

        # Rate limiting
        if i % 10 == 0:
            print(f"    → Progress: {success_count} successful, {failed_count} failed")

    # Summary
    print(f"\n" + "=" * 60)
    print("SEEDING COMPLETE")
    print("=" * 60)
    print(f"✓ Successfully created: {success_count}")
    print(f"✗ Failed: {failed_count}")
    print(f"📊 Total: {success_count + failed_count}")
    print("=" * 60)


if __name__ == "__main__":
    main()
