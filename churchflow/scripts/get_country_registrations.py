"""
Script to get country-level registration statistics for ChurchFlow.

This script queries the MongoDB database and aggregates registrations by country
based on phone number country codes.
"""

import os
import sys
from pymongo import MongoClient
from collections import defaultdict
import phonenumbers
from phonenumbers import geocoder
from typing import Dict, List, Tuple

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# MongoDB connection
MONGODB_URL = os.getenv(
    "MONGODB_URL",
    "mongodb://admin:aawwER4444%25@127.0.0.1:27017/churchflow?authSource=admin"
)


def get_country_from_phone(phone: str) -> Tuple[str, str]:
    """
    Extract country code and country name from phone number.

    Args:
        phone: Phone number in any format

    Returns:
        Tuple of (country_code, country_name) or ("Unknown", "Unknown") if parsing fails
    """
    try:
        # Parse phone number
        parsed = phonenumbers.parse(phone, None)
        
        # Get country code (ISO 3166-1 alpha-2)
        country_code = phonenumbers.region_code_for_number(parsed)
        
        # Get country name
        country_name = geocoder.description_for_number(parsed, "en")
        
        if country_code and country_name:
            return (country_code, country_name)
        else:
            return ("Unknown", "Unknown")
    except Exception:
        # If parsing fails, try to extract country code manually
        # Check for common patterns
        phone_clean = phone.lstrip('+').strip()
        
        # Common country codes
        country_codes = {
            '233': ('GH', 'Ghana'),
            '1': ('US', 'United States'),
            '44': ('GB', 'United Kingdom'),
            '39': ('IT', 'Italy'),
            '49': ('DE', 'Germany'),
            '33': ('FR', 'France'),
            '229': ('BJ', 'Benin'),
            '228': ('TG', 'Togo'),
            '231': ('LR', 'Liberia'),
            '232': ('SL', 'Sierra Leone'),
            '225': ('CI', 'Ivory Coast'),
            '971': ('AE', 'United Arab Emirates'),
            '1': ('CA', 'Canada'),  # Note: Canada also uses +1, need to check area code
        }
        
        # Try to match country code
        for code, (iso_code, name) in country_codes.items():
            if phone_clean.startswith(code):
                return (iso_code, name)
        
        return ("Unknown", "Unknown")


def get_country_registrations(conference_id: str = None) -> Dict[str, Dict]:
    """
    Get country-level registration statistics.

    Args:
        conference_id: Optional conference ID to filter by

    Returns:
        Dictionary with country statistics
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

    # Aggregate by country
    country_stats = defaultdict(lambda: {
        "country_code": "",
        "country_name": "",
        "total_registrations": 0,
        "checked_in": 0,
        "unique_phones": set()
    })

    for reg in registrations:
        phone = reg.get("user_phone", "")
        if not phone:
            continue

        country_code, country_name = get_country_from_phone(phone)
        
        country_stats[country_code]["country_code"] = country_code
        country_stats[country_code]["country_name"] = country_name
        country_stats[country_code]["total_registrations"] += 1
        country_stats[country_code]["unique_phones"].add(phone)
        
        if reg.get("checked_in", False):
            country_stats[country_code]["checked_in"] += 1

    # Convert sets to counts and format output
    result = {}
    for country_code, stats in country_stats.items():
        result[country_code] = {
            "country_code": stats["country_code"],
            "country_name": stats["country_name"],
            "total_registrations": stats["total_registrations"],
            "unique_registrants": len(stats["unique_phones"]),
            "checked_in": stats["checked_in"],
            "check_in_rate": round(
                (stats["checked_in"] / stats["total_registrations"] * 100) 
                if stats["total_registrations"] > 0 else 0, 
                2
            )
        }

    return result


def print_country_registrations(conference_id: str = None):
    """
    Print country-level registration statistics in a formatted table.

    Args:
        conference_id: Optional conference ID to filter by
    """
    stats = get_country_registrations(conference_id)
    
    # Sort by total registrations (descending)
    sorted_stats = sorted(
        stats.items(),
        key=lambda x: x[1]["total_registrations"],
        reverse=True
    )

    print("\n" + "=" * 80)
    print("COUNTRY-LEVEL REGISTRATION STATISTICS")
    if conference_id:
        print(f"Conference ID: {conference_id}")
    print("=" * 80)
    print(f"{'Country':<25} {'Code':<8} {'Total':<10} {'Unique':<10} {'Checked In':<12} {'Check-in %':<10}")
    print("-" * 80)

    total_all = 0
    unique_all = 0
    checked_in_all = 0

    for country_code, data in sorted_stats:
        country_name = data["country_name"]
        total = data["total_registrations"]
        unique = data["unique_registrants"]
        checked_in = data["checked_in"]
        check_in_rate = data["check_in_rate"]

        print(
            f"{country_name:<25} {country_code:<8} {total:<10} {unique:<10} {checked_in:<12} {check_in_rate:<10.2f}%"
        )

        total_all += total
        unique_all += unique
        checked_in_all += checked_in

    print("-" * 80)
    print(
        f"{'TOTAL':<25} {'':<8} {total_all:<10} {unique_all:<10} {checked_in_all:<12} "
        f"{(checked_in_all / total_all * 100) if total_all > 0 else 0:<10.2f}%"
    )
    print("=" * 80)
    print(f"\nTotal Countries: {len(sorted_stats)}")
    print(f"Total Registrations: {total_all}")
    print(f"Unique Registrants: {unique_all}")
    print(f"Total Checked In: {checked_in_all}\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Get country-level registration statistics for ChurchFlow"
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

    stats = get_country_registrations(args.conference_id)

    if args.json:
        import json
        print(json.dumps(stats, indent=2))
    else:
        print_country_registrations(args.conference_id)

