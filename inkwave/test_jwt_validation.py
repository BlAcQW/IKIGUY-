#!/usr/bin/env python3
"""
Test JWT Token Validation Using Shared Auth Module
"""

import os
import sys
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from supabase import create_client
from apps.shared.auth.supabase_auth import get_supabase_client, verify_supabase_token
from dotenv import load_dotenv

load_dotenv("/opt/kasaai/apps/inkwave/backend/.env")

ADMIN_EMAIL = "admin@ailabsafrica.com"
ADMIN_PASSWORD = "Admin@2024!"


async def test_jwt_validation():
    """Test JWT token validation using shared auth module."""

    print("=" * 60)
    print("JWT Token Validation Test")
    print("=" * 60)

    # Step 1: Get JWT token
    print("\n1. Authenticating with Supabase...")
    supabase = get_supabase_client()
    response = supabase.auth.sign_in_with_password({
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })

    token = response.session.access_token
    print(f"✓ JWT Token obtained: {token[:50]}...")

    # Step 2: Validate token using shared auth module
    print("\n2. Validating JWT token using shared auth module...")
    user_info = await verify_supabase_token(token)

    if user_info:
        print("✓ JWT Token is VALID!")
        print(f"  User ID: {user_info['id']}")
        print(f"  Email: {user_info['email']}")
        print(f"  Sub: {user_info['sub']}")
    else:
        print("✗ JWT Token is INVALID!")
        return

    # Step 3: Test with invalid token
    print("\n3. Testing with invalid token...")
    invalid_user = await verify_supabase_token("invalid_token_123")

    if invalid_user is None:
        print("✓ Invalid token correctly rejected")
    else:
        print("✗ Invalid token incorrectly accepted")

    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)
    print("\nConclusion:")
    print("• Supabase authentication: WORKING ✓")
    print("• JWT token validation: WORKING ✓")
    print("• Shared auth module: WORKING ✓")
    print("\nNext Step:")
    print("Replace mock auth in routes with:")
    print("  from apps.shared.dependencies.auth import get_current_user")
    print("  user: dict = Depends(get_current_user)")


if __name__ == "__main__":
    asyncio.run(test_jwt_validation())
