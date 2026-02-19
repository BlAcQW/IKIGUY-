"""
Basic functionality test for African Language Community Platform.

Tests database connection, API endpoints, and core functionality.
"""

import asyncio
import httpx
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_database_connection():
    """Test MongoDB connection and initialization."""
    try:
        from database import connect_to_mongo, get_database

        logger.info("Testing database connection...")
        await connect_to_mongo()

        db = get_database()

        # Test basic operations
        families_count = await db.language_families.count_documents({})
        languages_count = await db.languages.count_documents({})

        logger.info(f"✅ Database connected successfully")
        logger.info(f"   - Language families: {families_count}")
        logger.info(f"   - Languages: {languages_count}")

        return True

    except Exception as e:
        logger.error(f"❌ Database connection failed: {str(e)}")
        return False


async def test_api_endpoints():
    """Test basic API endpoints."""
    base_url = "http://localhost:8001"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Test health endpoint
            logger.info("Testing API health endpoint...")
            response = await client.get(f"{base_url}/health")

            if response.status_code == 200:
                logger.info("✅ Health endpoint working")
            else:
                logger.error(f"❌ Health endpoint failed: {response.status_code}")
                return False

            # Test root endpoint
            logger.info("Testing root endpoint...")
            response = await client.get(f"{base_url}/")

            if response.status_code == 200:
                data = response.json()
                logger.info("✅ Root endpoint working")
                logger.info(f"   - Supported languages: {len(data.get('supported_languages', []))}")
            else:
                logger.error(f"❌ Root endpoint failed: {response.status_code}")
                return False

            # Test language families endpoint
            logger.info("Testing language families endpoint...")
            response = await client.get(f"{base_url}/api/v1/languages/families")

            if response.status_code == 200:
                data = response.json()
                logger.info("✅ Language families endpoint working")
                logger.info(f"   - Total families: {data.get('total_count', 0)}")
            else:
                logger.error(f"❌ Language families endpoint failed: {response.status_code}")
                return False

            # Test language search endpoint
            logger.info("Testing language search endpoint...")
            response = await client.get(f"{base_url}/api/v1/languages/search?query=twi")

            if response.status_code == 200:
                data = response.json()
                logger.info("✅ Language search endpoint working")
                logger.info(f"   - Search results: {data.get('total_count', 0)}")
            else:
                logger.error(f"❌ Language search endpoint failed: {response.status_code}")

            return True

    except Exception as e:
        logger.error(f"❌ API testing failed: {str(e)}")
        return False


async def test_language_data():
    """Test that language data was properly initialized."""
    try:
        from database import get_database

        logger.info("Testing language data initialization...")
        db = get_database()

        # Test specific languages exist
        test_languages = ["twi", "yor", "swa", "gaa", "ewe"]

        for lang_code in test_languages:
            language = await db.languages.find_one({"code": lang_code})
            if language:
                logger.info(f"✅ {lang_code.upper()}: {language['name']} - {language.get('speaker_count', 'Unknown')} speakers")
            else:
                logger.warning(f"⚠️  {lang_code.upper()}: Not found in database")

        # Test family structure
        niger_congo = await db.language_families.find_one({"name": "niger-congo"})
        if niger_congo:
            subfamilies_count = await db.language_subfamilies.count_documents(
                {"family_id": niger_congo["_id"]}
            )
            logger.info(f"✅ Niger-Congo family has {subfamilies_count} subfamilies")

        return True

    except Exception as e:
        logger.error(f"❌ Language data test failed: {str(e)}")
        return False


async def main():
    """Run all basic tests."""
    logger.info("🚀 Starting African Language Community Platform Basic Tests")
    logger.info("=" * 60)

    tests_passed = 0
    total_tests = 3

    # Test database connection
    if await test_database_connection():
        tests_passed += 1

    # Test language data
    if await test_language_data():
        tests_passed += 1

    # Test API endpoints (only if server is running)
    logger.info("\n📡 Testing API endpoints (requires server to be running)...")
    if await test_api_endpoints():
        tests_passed += 1
    else:
        logger.info("💡 To test API endpoints, start the server with: python main.py")

    # Summary
    logger.info("=" * 60)
    logger.info(f"🎯 Tests Summary: {tests_passed}/{total_tests} passed")

    if tests_passed == total_tests:
        logger.info("🎉 All tests passed! Platform is ready to use.")
    elif tests_passed >= 2:
        logger.info("✨ Core functionality working. Start the API server to test endpoints.")
    else:
        logger.info("⚠️  Some critical tests failed. Check configuration and dependencies.")

    return tests_passed == total_tests


if __name__ == "__main__":
    success = asyncio.run(main())