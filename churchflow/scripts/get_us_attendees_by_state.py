"""
Script to get US attendees by state for ChurchFlow.

This script analyzes registrations and groups US attendees by state
based on branch location or church name.
"""

import os
import sys
from pymongo import MongoClient
from collections import defaultdict
import re

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# MongoDB connection
MONGODB_URL = os.getenv(
    "MONGODB_URL",
    "mongodb://admin:aawwER4444%25@127.0.0.1:27017/churchflow?authSource=admin"
)

# US state abbreviations and names
US_STATES = {
    'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California',
    'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware', 'FL': 'Florida', 'GA': 'Georgia',
    'HI': 'Hawaii', 'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa',
    'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
    'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi', 'MO': 'Missouri',
    'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada', 'NH': 'New Hampshire', 'NJ': 'New Jersey',
    'NM': 'New Mexico', 'NY': 'New York', 'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio',
    'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
    'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont',
    'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming'
}


def extract_state_from_location(location: str) -> tuple:
    """
    Extract state code and name from location string.

    Args:
        location: Location string (e.g., "New York, NY, USA")

    Returns:
        Tuple of (state_code, state_name) or (None, None)
    """
    if not location:
        return (None, None)

    # Try to find state abbreviation first (more reliable)
    for abbr, name in US_STATES.items():
        # Check for patterns like ", NY," or ", NY " or ending with ", NY"
        if f', {abbr},' in location or f', {abbr} ' in location or location.endswith(f', {abbr}'):
            return (abbr, name)
        # Also check for full state name
        if f', {name}' in location or location.endswith(f', {name}'):
            return (abbr, name)

    return (None, None)


def get_us_attendees_by_state(conference_id: str = None):
    """
    Get US attendees grouped by state.

    Args:
        conference_id: Optional conference ID to filter by

    Returns:
        Dictionary with state statistics
    """
    client = MongoClient(MONGODB_URL)
    db = client.churchflow

    # Build filter query
    filter_query = {
        "user_phone": {"$regex": r"^\+1"},
        "status": "confirmed"
    }
    if conference_id:
        from bson import ObjectId
        if ObjectId.is_valid(conference_id):
            filter_query["conference_id"] = ObjectId(conference_id)

    # Get all US registrations
    registrations = list(db.conference_registrations.find(filter_query))

    # Get all branches to map branch_id to location
    branches = {}
    for branch in db.branches.find({}):
        location = branch.get("location") or ""
        if location and ("USA" in location or "United States" in location):
            state_code, state_name = extract_state_from_location(location)
            if state_code:
                branches[str(branch["_id"])] = {
                    "name": branch.get("name"),
                    "location": location,
                    "state_code": state_code,
                    "state_name": state_name
                }

    # Group by state
    state_stats = defaultdict(lambda: {
        "state_code": "",
        "state_name": "",
        "count": 0,
        "attendees": []
    })

    unknown_state = []

    for reg in registrations:
        branch_id = reg.get("branch_id")
        church_name = reg.get("church_name", "")

        state_code = None
        state_name = None
        source = None

        # Try to get state from branch
        if branch_id:
            branch_str = str(branch_id)
            if branch_str in branches:
                state_code = branches[branch_str]["state_code"]
                state_name = branches[branch_str]["state_name"]
                source = "branch"

        # Try to extract from church name if no branch
        if not state_code and church_name:
            state_code, state_name = extract_state_from_location(church_name)
            if state_code:
                source = "church_name"

        if state_code:
            state_stats[state_code]["state_code"] = state_code
            state_stats[state_code]["state_name"] = state_name
            state_stats[state_code]["count"] += 1
            state_stats[state_code]["attendees"].append({
                "name": reg.get("user_name"),
                "phone": reg.get("user_phone"),
                "branch": branches.get(str(branch_id), {}).get("name") if branch_id else None,
                "church": church_name,
                "source": source
            })
        else:
            unknown_state.append({
                "name": reg.get("user_name"),
                "phone": reg.get("user_phone"),
                "branch_id": str(branch_id) if branch_id else None,
                "church": church_name
            })

    # Format output
    result = {}
    for state_code, stats in state_stats.items():
        result[state_code] = {
            "state_code": stats["state_code"],
            "state_name": stats["state_name"],
            "count": stats["count"],
            "attendees": stats["attendees"]
        }

    return result, unknown_state, len(registrations)


def print_us_attendees_by_state(conference_id: str = None):
    """
    Print US attendees by state in a formatted table.

    Args:
        conference_id: Optional conference ID to filter by
    """
    stats, unknown, total = get_us_attendees_by_state(conference_id)

    # Sort by count (descending)
    sorted_states = sorted(
        stats.items(),
        key=lambda x: x[1]["count"],
        reverse=True
    )

    print("\n" + "=" * 80)
    print("US ATTENDEES BY STATE")
    if conference_id:
        print(f"Conference ID: {conference_id}")
    print("=" * 80)
    print(f"{'State':<25} {'Code':<8} {'Count':<10} {'Percentage':<12}")
    print("-" * 80)

    for state_code, data in sorted_states:
        state_name = data["state_name"]
        count = data["count"]
        percentage = (count / total * 100) if total > 0 else 0

        print(f"{state_name:<25} {state_code:<8} {count:<10} {percentage:.2f}%")

    print("-" * 80)
    print(f"{'TOTAL':<25} {'':<8} {total:<10} {100.0:.2f}%")
    print("=" * 80)

    if unknown:
        print(f"\nUnknown State ({len(unknown)} registrations):")
        for reg in unknown[:10]:
            print(f"  - {reg['name']}: Branch={reg['branch_id']}, Church={reg['church']}")
        if len(unknown) > 10:
            print(f"  ... and {len(unknown) - 10} more")

    print(f"\nTotal US Registrations: {total}")
    print(f"States Represented: {len(sorted_states)}\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Get US attendees by state for ChurchFlow"
    )
    parser.add_argument(
        "--conference-id",
        type=str,
        help="Optional conference ID to filter by"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON instead of formatted table"
    )

    args = parser.parse_args()

    stats, unknown, total = get_us_attendees_by_state(args.conference_id)

    if args.json:
        import json
        output = {
            "total_us_registrations": total,
            "states": {k: {"state_name": v["state_name"], "count": v["count"]} for k, v in stats.items()},
            "unknown_state_count": len(unknown)
        }
        print(json.dumps(output, indent=2))
    else:
        print_us_attendees_by_state(args.conference_id)

