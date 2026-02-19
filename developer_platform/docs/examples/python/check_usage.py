"""
Check API Usage and Quota

This example demonstrates how to check your API usage, quota, and billing information.
"""

import os
import requests
from typing import Dict, Optional
from datetime import datetime, timedelta


# Configuration
API_KEY = os.getenv("KASAAI_API_KEY", "your_api_key_here")
BASE_URL = "https://developer.ailabsafrica.com"


def get_quota() -> Dict:
    """
    Get current API quota and usage limits.

    Returns:
        Dict: Quota information including limits and current usage

    Raises:
        requests.HTTPError: If the API request fails
    """
    endpoint = f"{BASE_URL}/api/v1/usage/quota"

    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }

    response = requests.get(endpoint, headers=headers)
    response.raise_for_status()

    return response.json()


def get_usage_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    granularity: str = "day"
) -> Dict:
    """
    Get detailed usage statistics.

    Args:
        start_date: Start date in YYYY-MM-DD format (default: 30 days ago)
        end_date: End date in YYYY-MM-DD format (default: today)
        granularity: Data granularity (hour, day, week, month)

    Returns:
        Dict: Usage statistics with breakdown by service

    Raises:
        requests.HTTPError: If the API request fails
    """
    endpoint = f"{BASE_URL}/api/v1/usage/stats"

    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }

    # Default to last 30 days if not specified
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    params = {
        "start_date": start_date,
        "end_date": end_date,
        "granularity": granularity
    }

    response = requests.get(endpoint, headers=headers, params=params)
    response.raise_for_status()

    return response.json()


def get_billing_info() -> Dict:
    """
    Get current billing information.

    Returns:
        Dict: Billing info including credits, balance, and next billing date

    Raises:
        requests.HTTPError: If the API request fails
    """
    endpoint = f"{BASE_URL}/api/v1/usage/billing"

    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }

    response = requests.get(endpoint, headers=headers)
    response.raise_for_status()

    return response.json()


def format_credits(credits: float) -> str:
    """Format credits with appropriate units."""
    if credits >= 1000000:
        return f"{credits / 1000000:.2f}M"
    elif credits >= 1000:
        return f"{credits / 1000:.2f}K"
    else:
        return f"{credits:.2f}"


def print_quota_info(quota: Dict):
    """Print formatted quota information."""
    print("📊 API Quota & Limits\n")
    print("Rate Limits:")
    print(f"   Requests per minute: {quota.get('rate_limit_minute', 'N/A')}")
    print(f"   Requests per hour:   {quota.get('rate_limit_hour', 'N/A')}")
    print(f"   Requests per day:    {quota.get('rate_limit_day', 'N/A')}")
    print()

    print("Current Usage:")
    print(f"   This minute: {quota.get('usage_minute', 0)}")
    print(f"   This hour:   {quota.get('usage_hour', 0)}")
    print(f"   This day:    {quota.get('usage_day', 0)}")
    print()


def print_usage_stats(stats: Dict):
    """Print formatted usage statistics."""
    print("📈 Usage Statistics\n")

    total_requests = stats.get('total_requests', 0)
    total_credits = stats.get('total_credits_used', 0)

    print(f"Total Requests: {total_requests:,}")
    print(f"Total Credits Used: {format_credits(total_credits)}")
    print()

    # Breakdown by service
    if 'by_service' in stats:
        print("Breakdown by Service:")
        for service, data in stats['by_service'].items():
            requests_count = data.get('requests', 0)
            credits = data.get('credits', 0)
            print(f"   {service.capitalize()}:")
            print(f"      Requests: {requests_count:,}")
            print(f"      Credits:  {format_credits(credits)}")
        print()

    # Time series data
    if 'time_series' in stats and stats['time_series']:
        print("Recent Activity:")
        for entry in stats['time_series'][-5:]:  # Last 5 entries
            date = entry.get('date', 'N/A')
            requests_count = entry.get('requests', 0)
            print(f"   {date}: {requests_count:,} requests")
        print()


def print_billing_info(billing: Dict):
    """Print formatted billing information."""
    print("💳 Billing Information\n")

    credits_remaining = billing.get('credits_remaining', 0)
    credits_used = billing.get('credits_used', 0)
    monthly_spend = billing.get('monthly_spend', 0)

    print(f"Credits Remaining: {format_credits(credits_remaining)}")
    print(f"Credits Used (This Month): {format_credits(credits_used)}")
    print(f"Monthly Spend: ${monthly_spend:.2f}")
    print()

    if 'plan' in billing:
        print(f"Plan: {billing['plan']}")

    if 'next_billing_date' in billing:
        print(f"Next Billing Date: {billing['next_billing_date']}")
    print()


def main():
    """Main function to demonstrate usage checking."""
    try:
        # Get quota information
        print("Fetching quota information...\n")
        quota = get_quota()
        print_quota_info(quota)

        # Get usage statistics
        print("Fetching usage statistics...\n")
        stats = get_usage_stats(granularity="day")
        print_usage_stats(stats)

        # Get billing information
        print("Fetching billing information...\n")
        billing = get_billing_info()
        print_billing_info(billing)

        # Check if approaching limits
        usage_percent = (quota.get('usage_day', 0) / quota.get('rate_limit_day', 1)) * 100
        if usage_percent > 80:
            print("⚠️  WARNING: You've used over 80% of your daily quota!")
            print("   Consider upgrading your plan at:")
            print("   https://developer.ailabsafrica.com/billing")

        # Check credits
        credits_remaining = billing.get('credits_remaining', 0)
        if credits_remaining < 100:
            print("⚠️  WARNING: Low credits remaining!")
            print("   Add credits at:")
            print("   https://developer.ailabsafrica.com/billing")

    except requests.HTTPError as e:
        print(f"❌ Error fetching usage information: {e}")
        if hasattr(e.response, 'json'):
            print(f"   Details: {e.response.json()}")
        exit(1)


if __name__ == "__main__":
    main()
