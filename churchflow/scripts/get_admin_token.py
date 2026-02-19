#!/usr/bin/env python3
"""
Helper script to get admin token for testing.

Usage:
    python3 get_admin_token.py [admin_email] [admin_password]
    
Or set environment variables:
    export ADMIN_EMAIL=admin@example.com
    export ADMIN_PASSWORD=password
"""

import sys
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv("/opt/kasaai/.env")

# Try multiple possible env var names
SUPABASE_URL = os.getenv("CHURCHFLOW_SUPABASE_URL") or os.getenv("SUPABASE_URL") or "https://supabase-api.ailabsafrica.com"
SUPABASE_ANON_KEY = os.getenv("CHURCHFLOW_SUPABASE_ANON_KEY") or os.getenv("SUPABASE_ANON_KEY")
API_BASE_URL = os.getenv("API_BASE_URL") or os.getenv("CHURCHFLOW_API_URL") or "https://churchflow.ailabsafrica.com/api/v1"

# Debug: print configuration
if not SUPABASE_ANON_KEY:
    print(f"⚠️  Warning: SUPABASE_ANON_KEY not found in environment")

def get_token_from_supabase(email: str, password: str) -> str:
    """Get token by logging in via Supabase."""
    print(f"🔐 Logging in as {email}...")
    
    login_url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "email": email,
        "password": password
    }
    
    response = requests.post(login_url, headers=headers, json=data)
    
    if response.status_code == 200:
        supabase_token = response.json()["access_token"]
        print(f"✅ Successfully logged in to Supabase")
        
        # Exchange for backend token
        print("🔄 Exchanging Supabase token for backend token...")
        exchange_url = f"{API_BASE_URL}/auth/exchange-token"
        exchange_headers = {
            "Authorization": f"Bearer {supabase_token}",
            "Content-Type": "application/json"
        }
        
        exchange_response = requests.post(exchange_url, headers=exchange_headers)
        
        if exchange_response.status_code == 200:
            backend_token = exchange_response.json()["access_token"]
            print(f"✅ Successfully obtained backend token")
            return backend_token
        else:
            print(f"❌ Token exchange failed: {exchange_response.status_code} - {exchange_response.text}")
            return None
    else:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        return None


def main():
    """Main function."""
    # Get credentials from args or environment
    email = sys.argv[1] if len(sys.argv) > 1 else os.getenv("ADMIN_EMAIL")
    password = sys.argv[2] if len(sys.argv) > 2 else os.getenv("ADMIN_PASSWORD")
    
    if not email or not password:
        print("❌ No credentials provided.")
        print("\nUsage:")
        print("  python3 get_admin_token.py [email] [password]")
        print("\nOr set environment variables:")
        print("  export ADMIN_EMAIL=admin@example.com")
        print("  export ADMIN_PASSWORD=password")
        print("\nOr use from command line:")
        print("  ADMIN_EMAIL=admin@example.com ADMIN_PASSWORD=password python3 get_admin_token.py")
        sys.exit(1)
    
    token = get_token_from_supabase(email, password)
    
    if token:
        print(f"\n{'='*60}")
        print("Admin Token:")
        print(f"{'='*60}")
        print(token)
        print(f"{'='*60}")
        print("\nTo use with test script:")
        print(f"  export ADMIN_TOKEN='{token}'")
        print(f"  python3 test_member_creation_flows.py")
        print("\nOr pass directly:")
        print(f"  python3 test_member_creation_flows.py '{token}'")
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())

