"""
Geocode all ChurchFlow branches using OpenStreetMap Nominatim API.

This script batch geocodes the 150+ hardcoded branches in constants/branches.py
by querying the existing geocoding API endpoint. Results are exported to JSON
for admin review before updating the branch constants.

Usage:
    python scripts/geocode_branches.py

Output:
    geocoded_branches.json - Contains all branches with lat/lon coordinates
"""

import asyncio
import json
import time
from typing import List, Dict, Any
import aiohttp
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.constants.branches import FIXED_BRANCHES


# API Configuration
API_BASE_URL = "http://localhost:30030"  # ChurchFlow backend
GEOCODING_ENDPOINT = "/api/v1/geocoding/search"
RATE_LIMIT_DELAY = 1.2  # seconds (1 req/sec + buffer for OSM)


async def geocode_location(
    session: aiohttp.ClientSession,
    location: str,
    country_code: str = "gh"
) -> Dict[str, Any]:
    """
    Geocode a single location using the geocoding API.

    Args:
        session: Aiohttp client session
        location: Location string (e.g., "Adenta, Greater Accra, Ghana")
        country_code: ISO country code for filtering (default: Ghana)

    Returns:
        {
            "latitude": float,
            "longitude": float,
            "display_name": str,
            "accuracy": str,  # "exact", "street", "city", "approximate"
            "confidence": float  # 0-1
        }
    """
    params = {
        "q": location,
        "countrycodes": country_code,
        "limit": 5
    }

    try:
        async with session.get(
            f"{API_BASE_URL}{GEOCODING_ENDPOINT}",
            params=params,
            timeout=aiohttp.ClientTimeout(total=10)
        ) as response:
            if response.status == 200:
                data = await response.json()

                if data and len(data) > 0:
                    # Get best result (first one)
                    best_result = data[0]

                    # Determine accuracy based on result type
                    place_type = best_result.get("type", "").lower()
                    accuracy = "approximate"

                    if place_type in ["house", "building", "address"]:
                        accuracy = "exact"
                    elif place_type in ["road", "street", "neighbourhood"]:
                        accuracy = "street"
                    elif place_type in ["suburb", "town", "city"]:
                        accuracy = "city"

                    # Calculate confidence (simple heuristic)
                    confidence = 0.9 if accuracy in ["exact", "street"] else 0.7

                    return {
                        "latitude": float(best_result.get("lat", 0)),
                        "longitude": float(best_result.get("lon", 0)),
                        "display_name": best_result.get("display_name", location),
                        "accuracy": accuracy,
                        "confidence": confidence,
                        "osm_type": best_result.get("type", "unknown")
                    }
                else:
                    print(f"  ⚠️  No results found for: {location}")
                    return {
                        "latitude": None,
                        "longitude": None,
                        "display_name": location,
                        "accuracy": "failed",
                        "confidence": 0.0,
                        "osm_type": None
                    }

            else:
                print(f"  ❌ API error {response.status} for: {location}")
                return {
                    "latitude": None,
                    "longitude": None,
                    "display_name": location,
                    "accuracy": "failed",
                    "confidence": 0.0,
                    "osm_type": None,
                    "error": f"HTTP {response.status}"
                }

    except Exception as e:
        print(f"  ❌ Exception for {location}: {str(e)}")
        return {
            "latitude": None,
            "longitude": None,
            "display_name": location,
            "accuracy": "failed",
            "confidence": 0.0,
            "osm_type": None,
            "error": str(e)
        }


async def geocode_all_branches() -> List[Dict[str, Any]]:
    """
    Geocode all branches from FIXED_BRANCHES.

    Returns:
        List of branches with added GPS coordinates
    """
    geocoded_branches = []
    total = len(FIXED_BRANCHES)

    print(f"\n🌍 Starting geocoding of {total} branches...")
    print(f"⏱️  Estimated time: ~{total * RATE_LIMIT_DELAY / 60:.1f} minutes\n")

    async with aiohttp.ClientSession() as session:
        for i, branch in enumerate(FIXED_BRANCHES, 1):
            print(f"[{i}/{total}] Geocoding: {branch['name']} ({branch['location']})")

            # Geocode the branch
            geo_result = await geocode_location(session, branch["location"])

            # Merge branch data with geocoding result
            geocoded_branch = {
                **branch,  # Original branch data
                "latitude": geo_result["latitude"],
                "longitude": geo_result["longitude"],
                "checkin_radius": 500,  # Default 500m
                "auto_checkin_enabled": False,  # Disabled by default
                "geocoding_accuracy": geo_result["accuracy"],
                "geocoding_confidence": geo_result["confidence"],
                "geocoding_display_name": geo_result["display_name"],
                "geocoding_osm_type": geo_result.get("osm_type")
            }

            geocoded_branches.append(geocoded_branch)

            # Log result
            if geo_result["latitude"]:
                print(f"  ✅ Success: {geo_result['latitude']:.6f}, {geo_result['longitude']:.6f} ({geo_result['accuracy']})")
            else:
                print(f"  ❌ Failed to geocode")

            # Rate limiting
            if i < total:  # Don't wait after last request
                await asyncio.sleep(RATE_LIMIT_DELAY)

    return geocoded_branches


def calculate_statistics(branches: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate statistics about geocoding results.

    Args:
        branches: List of geocoded branches

    Returns:
        Statistics dict
    """
    total = len(branches)
    successful = sum(1 for b in branches if b["latitude"] is not None)
    failed = total - successful

    accuracy_counts = {
        "exact": sum(1 for b in branches if b.get("geocoding_accuracy") == "exact"),
        "street": sum(1 for b in branches if b.get("geocoding_accuracy") == "street"),
        "city": sum(1 for b in branches if b.get("geocoding_accuracy") == "city"),
        "approximate": sum(1 for b in branches if b.get("geocoding_accuracy") == "approximate"),
        "failed": failed
    }

    return {
        "total_branches": total,
        "successful": successful,
        "failed": failed,
        "success_rate": (successful / total * 100) if total > 0 else 0,
        "accuracy_distribution": accuracy_counts
    }


def export_to_json(branches: List[Dict[str, Any]], filename: str = "geocoded_branches.json"):
    """
    Export geocoded branches to JSON file.

    Args:
        branches: List of geocoded branches
        filename: Output filename
    """
    output = {
        "metadata": {
            "total_branches": len(branches),
            "geocoded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "source": "OpenStreetMap Nominatim",
            "rate_limit": f"{1/RATE_LIMIT_DELAY:.1f} req/sec"
        },
        "statistics": calculate_statistics(branches),
        "branches": branches
    }

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Exported results to: {filename}")


def print_summary(branches: List[Dict[str, Any]]):
    """
    Print summary of geocoding results.

    Args:
        branches: List of geocoded branches
    """
    stats = calculate_statistics(branches)

    print("\n" + "="*60)
    print("📊 GEOCODING SUMMARY")
    print("="*60)
    print(f"Total branches:      {stats['total_branches']}")
    print(f"Successfully geocoded: {stats['successful']} ({stats['success_rate']:.1f}%)")
    print(f"Failed:              {stats['failed']}")
    print("\nAccuracy Distribution:")
    print(f"  Exact:             {stats['accuracy_distribution']['exact']}")
    print(f"  Street-level:      {stats['accuracy_distribution']['street']}")
    print(f"  City-level:        {stats['accuracy_distribution']['city']}")
    print(f"  Approximate:       {stats['accuracy_distribution']['approximate']}")
    print(f"  Failed:            {stats['accuracy_distribution']['failed']}")
    print("="*60)

    # List failed branches
    failed_branches = [b for b in branches if b["latitude"] is None]
    if failed_branches:
        print("\n⚠️  Failed to geocode:")
        for branch in failed_branches:
            print(f"  - {branch['name']} ({branch['location']})")
        print("\nThese will need manual coordinate entry.")


def generate_python_code(branches: List[Dict[str, Any]]):
    """
    Generate Python code to update branches.py.

    Args:
        branches: List of geocoded branches
    """
    print("\n" + "="*60)
    print("🐍 PYTHON CODE FOR branches.py UPDATE")
    print("="*60)
    print("\nCopy the following into app/constants/branches.py:\n")

    print("FIXED_BRANCHES: List[Dict[str, Any]] = [")
    for branch in branches:
        print("    {")
        print(f'        "name": "{branch["name"]}",')
        print(f'        "location": "{branch["location"]}",')
        print(f'        "region": "{branch["region"]}",')

        if branch["latitude"] is not None:
            print(f'        "latitude": {branch["latitude"]},')
            print(f'        "longitude": {branch["longitude"]},')
            print(f'        "checkin_radius": {branch["checkin_radius"]},')
            print(f'        "auto_checkin_enabled": {str(branch["auto_checkin_enabled"]).lower()},')
            print(f'        "geocoding_accuracy": "{branch["geocoding_accuracy"]}",')
        else:
            print(f'        "latitude": None,  # NEEDS MANUAL GEOCODING')
            print(f'        "longitude": None,')
            print(f'        "checkin_radius": 500,')
            print(f'        "auto_checkin_enabled": False,')
            print(f'        "geocoding_accuracy": None,')

        print("    },")

    print("]")


async def main():
    """Main execution function."""
    print("\n" + "="*60)
    print("  ChurchFlow Branch Geocoding Script")
    print("="*60)

    # Geocode all branches
    geocoded_branches = await geocode_all_branches()

    # Export to JSON
    export_to_json(geocoded_branches)

    # Print summary
    print_summary(geocoded_branches)

    # Generate Python code
    generate_python_code(geocoded_branches)

    print("\n✅ Geocoding complete!")
    print("\nNext steps:")
    print("1. Review geocoded_branches.json for accuracy")
    print("2. Manually geocode failed branches (if any)")
    print("3. Update app/constants/branches.py with the generated code")
    print("4. Test proximity check-in functionality")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏸️  Geocoding interrupted by user.")
        print("Partial results may be incomplete.")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
