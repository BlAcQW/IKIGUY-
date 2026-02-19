"""
Script to get registered attendees outside Ghana grouped by branches.

This script analyzes registrations and groups non-Ghana attendees by branch.
"""

import os
import sys
from pymongo import MongoClient
from collections import defaultdict
import phonenumbers
from phonenumbers import geocoder

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# MongoDB connection
MONGODB_URL = os.getenv(
    "MONGODB_URL",
    "mongodb://admin:aawwER4444%25@127.0.0.1:27017/churchflow?authSource=admin"
)


def get_country_from_phone(phone: str) -> tuple:
    """
    Extract country code and country name from phone number.

    Args:
        phone: Phone number in any format

    Returns:
        Tuple of (country_code, country_name) or ("Unknown", "Unknown") if parsing fails
    """
    try:
        parsed = phonenumbers.parse(phone, None)
        country_code = phonenumbers.region_code_for_number(parsed)
        country_name = geocoder.description_for_number(parsed, "en")
        
        if country_code and country_name:
            return (country_code, country_name)
    except Exception:
        pass
    
    return ("Unknown", "Unknown")


def get_non_ghana_attendees_by_branch(conference_id: str = None):
    """
    Get non-Ghana attendees grouped by branch.

    Args:
        conference_id: Optional conference ID to filter by

    Returns:
        Dictionary with branch statistics
    """
    client = MongoClient(MONGODB_URL)
    db = client.churchflow

    # Build filter query
    filter_query = {"status": "confirmed"}
    if conference_id:
        from bson import ObjectId
        if ObjectId.is_valid(conference_id):
            filter_query["conference_id"] = ObjectId(conference_id)

    # Get all registrations
    registrations = list(db.conference_registrations.find(filter_query))

    # Get all branches
    branches = {}
    for branch in db.branches.find({}):
        branches[str(branch["_id"])] = {
            "name": branch.get("name"),
            "location": branch.get("location", ""),
            "region": branch.get("region", "")
        }

    # Group by branch and country
    branch_stats = defaultdict(lambda: {
        "branch_name": "",
        "branch_location": "",
        "branch_region": "",
        "total_count": 0,
        "countries": defaultdict(int),
        "attendees": []
    })

    no_branch_count = 0
    no_branch_attendees = []

    for reg in registrations:
        phone = reg.get("user_phone", "")
        if not phone:
            continue

        country_code, country_name = get_country_from_phone(phone)
        
        # Skip Ghana registrations
        if country_code == "GH":
            continue

        branch_id = reg.get("branch_id")
        
        if branch_id:
            branch_str = str(branch_id)
            if branch_str in branches:
                branch_info = branches[branch_str]
                branch_stats[branch_str]["branch_name"] = branch_info["name"]
                branch_stats[branch_str]["branch_location"] = branch_info["location"]
                branch_stats[branch_str]["branch_region"] = branch_info["region"]
                branch_stats[branch_str]["total_count"] += 1
                branch_stats[branch_str]["countries"][country_name] += 1
                branch_stats[branch_str]["attendees"].append({
                    "name": reg.get("user_name"),
                    "phone": phone,
                    "country": country_name,
                    "country_code": country_code
                })
            else:
                # Branch ID exists but branch not found
                no_branch_count += 1
                no_branch_attendees.append({
                    "name": reg.get("user_name"),
                    "phone": phone,
                    "country": country_name,
                    "branch_id": branch_str
                })
        else:
            # No branch assigned
            no_branch_count += 1
            no_branch_attendees.append({
                "name": reg.get("user_name"),
                "phone": phone,
                "country": country_name,
                "church_name": reg.get("church_name")
            })

    # Format output
    result = {}
    for branch_id, stats in branch_stats.items():
        result[branch_id] = {
            "branch_name": stats["branch_name"],
            "branch_location": stats["branch_location"],
            "branch_region": stats["branch_region"],
            "total_count": stats["total_count"],
            "countries": dict(stats["countries"]),
            "attendees": stats["attendees"]
        }

    return result, no_branch_count, no_branch_attendees


def print_non_ghana_attendees_by_branch(conference_id: str = None):
    """
    Print non-Ghana attendees by branch in a formatted table.

    Args:
        conference_id: Optional conference ID to filter by
    """
    stats, no_branch_count, no_branch_attendees = get_non_ghana_attendees_by_branch(conference_id)

    # Sort by count (descending)
    sorted_branches = sorted(
        stats.items(),
        key=lambda x: x[1]["total_count"],
        reverse=True
    )

    total_non_ghana = sum(s["total_count"] for s in stats.values()) + no_branch_count

    print("\n" + "=" * 100)
    print("NON-GHANA ATTENDEES BY BRANCH")
    if conference_id:
        print(f"Conference ID: {conference_id}")
    print("=" * 100)
    print(f"{'Branch Name':<35} {'Location':<30} {'Region':<20} {'Count':<10} {'Countries':<20}")
    print("-" * 100)

    for branch_id, data in sorted_branches:
        branch_name = data["branch_name"]
        location = data["branch_location"][:28] if data["branch_location"] else "N/A"
        region = data["branch_region"][:18] if data["branch_region"] else "N/A"
        count = data["total_count"]
        countries = ", ".join(list(data["countries"].keys())[:2])
        if len(data["countries"]) > 2:
            countries += f" (+{len(data['countries']) - 2} more)"

        print(f"{branch_name:<35} {location:<30} {region:<20} {count:<10} {countries:<20}")

    print("-" * 100)
    print(f"{'TOTAL (by branch)':<35} {'':<30} {'':<20} {sum(s['total_count'] for s in stats.values()):<10}")
    
    if no_branch_count > 0:
        print(f"{'No Branch Assigned':<35} {'':<30} {'':<20} {no_branch_count:<10}")
    
    print("-" * 100)
    print(f"{'GRAND TOTAL':<35} {'':<30} {'':<20} {total_non_ghana:<10}")
    print("=" * 100)

    # Show country breakdown for each branch
    if sorted_branches:
        print("\n" + "=" * 100)
        print("DETAILED COUNTRY BREAKDOWN BY BRANCH")
        print("=" * 100)
        
        for branch_id, data in sorted_branches:
            if data["total_count"] > 0:
                print(f"\n{data['branch_name']} ({data['total_count']} attendees):")
                sorted_countries = sorted(
                    data["countries"].items(),
                    key=lambda x: x[1],
                    reverse=True
                )
                for country, count in sorted_countries:
                    print(f"  - {country}: {count}")

    if no_branch_attendees:
        print(f"\n\nNo Branch Assigned ({no_branch_count} attendees):")
        # Group by country
        no_branch_countries = defaultdict(int)
        for attendee in no_branch_attendees:
            no_branch_countries[attendee["country"]] += 1
        
        for country, count in sorted(no_branch_countries.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {country}: {count}")

    print(f"\nTotal Non-Ghana Registrations: {total_non_ghana}")
    print(f"Branches with Non-Ghana Attendees: {len(sorted_branches)}\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Get non-Ghana attendees by branch for ChurchFlow"
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

    stats, no_branch_count, no_branch_attendees = get_non_ghana_attendees_by_branch(args.conference_id)

    if args.json:
        import json
        output = {
            "total_non_ghana_registrations": sum(s["total_count"] for s in stats.values()) + no_branch_count,
            "branches": {
                k: {
                    "branch_name": v["branch_name"],
                    "branch_location": v["branch_location"],
                    "branch_region": v["branch_region"],
                    "total_count": v["total_count"],
                    "countries": v["countries"]
                }
                for k, v in stats.items()
            },
            "no_branch_count": no_branch_count
        }
        print(json.dumps(output, indent=2))
    else:
        print_non_ghana_attendees_by_branch(args.conference_id)

