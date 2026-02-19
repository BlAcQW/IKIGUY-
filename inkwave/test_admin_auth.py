#!/usr/bin/env python3
"""
Test InkWave API Authentication with Admin User

Tests:
1. Supabase authentication
2. JWT token validation
3. API endpoint access
4. User creation in MongoDB
"""

import os
import sys
import asyncio
import json
from datetime import datetime

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from supabase import create_client, Client
import httpx
from dotenv import load_dotenv

# Load environment
load_dotenv("/opt/kasaai/apps/inkwave/backend/.env")

# Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
API_BASE_URL = "http://localhost:30033/api/v1"

# Admin credentials
ADMIN_EMAIL = "admin@ailabsafrica.com"
ADMIN_PASSWORD = "Admin@2024!"


class Colors:
    """Terminal colors."""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text: str):
    """Print section header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}\n")


def print_success(text: str):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_error(text: str):
    """Print error message."""
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def print_info(text: str):
    """Print info message."""
    print(f"{Colors.YELLOW}→ {text}{Colors.END}")


async def test_supabase_auth():
    """Test Supabase authentication and get JWT token."""
    print_header("Step 1: Supabase Authentication")

    try:
        # Initialize Supabase client
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        print_info(f"Supabase URL: {SUPABASE_URL}")
        print_info(f"Admin Email: {ADMIN_EMAIL}")

        # Sign in with admin credentials
        response = supabase.auth.sign_in_with_password({
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })

        if not response.user or not response.session:
            print_error("Authentication failed: No user or session returned")
            return None

        user = response.user
        session = response.session

        print_success("Supabase authentication successful!")
        print_info(f"User ID: {user.id}")
        print_info(f"Email: {user.email}")
        print_info(f"Token expires: {datetime.fromtimestamp(session.expires_at)}")

        return {
            "user": user,
            "session": session,
            "token": session.access_token
        }

    except Exception as e:
        print_error(f"Supabase authentication failed: {str(e)}")
        return None


async def test_health_endpoint():
    """Test health endpoint (no auth required)."""
    print_header("Step 2: Test Health Endpoint (No Auth)")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL.replace('/api/v1', '')}/health")

            if response.status_code == 200:
                data = response.json()
                print_success("Health endpoint accessible")
                print_info(f"Status: {data.get('status')}")
                print_info(f"Service: {data.get('service')}")
                print_info(f"Version: {data.get('version')}")
                return True
            else:
                print_error(f"Health check failed: {response.status_code}")
                return False

    except Exception as e:
        print_error(f"Health check error: {str(e)}")
        return False


async def test_protected_endpoint(token: str):
    """Test protected endpoint with JWT token."""
    print_header("Step 3: Test Protected Endpoint (With Auth)")

    try:
        async with httpx.AsyncClient() as client:
            # Test books endpoint (should require auth after we fix it)
            headers = {"Authorization": f"Bearer {token}"}

            print_info("Testing GET /api/v1/books")
            response = await client.get(
                f"{API_BASE_URL}/books",
                headers=headers,
                timeout=10.0
            )

            print_info(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print_success("Books endpoint accessible")
                print_info(f"Total books: {data.get('total', 0)}")
                print_info(f"Books returned: {len(data.get('books', []))}")
                return True
            else:
                print_error(f"Books endpoint failed: {response.status_code}")
                print_info(f"Response: {response.text}")
                return False

    except Exception as e:
        print_error(f"Protected endpoint error: {str(e)}")
        return False


async def test_user_in_mongodb(token: str):
    """Test if user was created in MongoDB."""
    print_header("Step 4: Verify User in MongoDB")

    try:
        from motor.motor_asyncio import AsyncIOMotorClient

        mongodb_uri = os.getenv("MONGODB_URI")
        client = AsyncIOMotorClient(mongodb_uri)
        db = client.inkwave

        # Find admin user
        user_doc = await db.users.find_one({"email": ADMIN_EMAIL})

        if user_doc:
            print_success("User found in MongoDB!")
            print_info(f"User ID: {user_doc.get('user_id')}")
            print_info(f"Email: {user_doc.get('email')}")
            print_info(f"Display Name: {user_doc.get('display_name')}")
            print_info(f"Is Admin: {user_doc.get('is_admin', False)}")
            print_info(f"Credits: {user_doc.get('credits', 0)}")
            print_info(f"Created At: {user_doc.get('created_at')}")

            await client.close()
            return True
        else:
            print_error("User NOT found in MongoDB")
            print_info("User should be auto-created on first API call with auth")
            await client.close()
            return False

    except Exception as e:
        print_error(f"MongoDB check error: {str(e)}")
        return False


async def test_wallet_endpoint(token: str):
    """Test wallet endpoint."""
    print_header("Step 5: Test Wallet Endpoint")

    try:
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {token}"}

            print_info("Testing GET /api/v1/wallet")
            response = await client.get(
                f"{API_BASE_URL}/wallet",
                headers=headers,
                timeout=10.0
            )

            print_info(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print_success("Wallet endpoint accessible")
                print_info(f"Wallet data: {json.dumps(data, indent=2)}")
                return True
            else:
                print_error(f"Wallet endpoint failed: {response.status_code}")
                print_info(f"Response: {response.text}")
                return False

    except Exception as e:
        print_error(f"Wallet endpoint error: {str(e)}")
        return False


async def test_organizations_endpoint(token: str):
    """Test organizations endpoint."""
    print_header("Step 6: Test Organizations Endpoint")

    try:
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {token}"}

            print_info("Testing GET /api/v1/organizations")
            response = await client.get(
                f"{API_BASE_URL}/organizations",
                headers=headers,
                timeout=10.0
            )

            print_info(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print_success("Organizations endpoint accessible")

                if isinstance(data, list):
                    print_info(f"Organizations found: {len(data)}")
                    for org in data[:3]:  # Show first 3
                        print_info(f"  - {org.get('name')} ({org.get('id')})")
                else:
                    print_info(f"Response: {json.dumps(data, indent=2)}")
                return True
            else:
                print_error(f"Organizations endpoint failed: {response.status_code}")
                print_info(f"Response: {response.text}")
                return False

    except Exception as e:
        print_error(f"Organizations endpoint error: {str(e)}")
        return False


async def main():
    """Run all authentication tests."""
    print(f"\n{Colors.BOLD}InkWave API Authentication Test{Colors.END}")
    print(f"{Colors.BOLD}Testing with Admin User{Colors.END}")

    results = []

    # Step 1: Authenticate with Supabase
    auth_data = await test_supabase_auth()
    results.append(("Supabase Auth", auth_data is not None))

    if not auth_data:
        print_error("\n❌ Authentication failed. Cannot continue with API tests.")
        return

    token = auth_data["token"]

    # Step 2: Health check
    health_ok = await test_health_endpoint()
    results.append(("Health Endpoint", health_ok))

    # Step 3: Protected endpoint
    protected_ok = await test_protected_endpoint(token)
    results.append(("Protected Endpoint", protected_ok))

    # Step 4: MongoDB user check
    mongo_ok = await test_user_in_mongodb(token)
    results.append(("MongoDB User", mongo_ok))

    # Step 5: Wallet endpoint
    wallet_ok = await test_wallet_endpoint(token)
    results.append(("Wallet Endpoint", wallet_ok))

    # Step 6: Organizations endpoint
    orgs_ok = await test_organizations_endpoint(token)
    results.append(("Organizations Endpoint", orgs_ok))

    # Summary
    print_header("Test Summary")

    for test_name, passed in results:
        if passed:
            print_success(f"{test_name}: PASSED")
        else:
            print_error(f"{test_name}: FAILED")

    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)

    print(f"\n{Colors.BOLD}Results: {total_passed}/{total_tests} tests passed{Colors.END}\n")

    if total_passed == total_tests:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ All tests passed!{Colors.END}\n")
    else:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠ Some tests failed{Colors.END}\n")

    # Print JWT token for manual testing
    print_header("JWT Token for Manual Testing")
    print(f"{Colors.BOLD}Token (valid for 1 hour):{Colors.END}")
    print(f"{token[:50]}...")
    print(f"\n{Colors.BOLD}Usage Example:{Colors.END}")
    print(f'curl -H "Authorization: Bearer {token}" http://localhost:30033/api/v1/books')
    print()


if __name__ == "__main__":
    asyncio.run(main())
