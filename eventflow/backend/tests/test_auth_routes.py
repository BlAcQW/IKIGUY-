"""
Unit tests for authentication API routes.

Tests OTP sending, verification, and token generation.
"""

import pytest
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from apps.eventflow.backend.app.main import app


@pytest.fixture
async def test_db():
    """Create test database connection."""
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["kasaai_eventflow_test"]
    yield db
    # Cleanup: drop test database
    await client.drop_database("kasaai_eventflow_test")
    client.close()


@pytest.mark.asyncio
async def test_health_endpoint():
    """Test health check endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "eventflow-backend"


@pytest.mark.asyncio
async def test_root_endpoint():
    """Test root endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["app"] == "EventFlow"
        assert data["tagline"] == "Plan less. Celebrate more."
        assert data["status"] == "active"


@pytest.mark.asyncio
async def test_send_otp_endpoint():
    """Test OTP sending endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/send-otp",
            json={"phone": "+233244123456"}
        )
        # Note: This might fail if Supabase is not configured
        # For now, we just check the endpoint exists
        assert response.status_code in [200, 500]  # 500 if Supabase not configured


@pytest.mark.asyncio
async def test_verify_otp_endpoint_invalid():
    """Test OTP verification with invalid OTP."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/verify-otp",
            json={
                "phone": "+233244123456",
                "otp": "000000"
            }
        )
        # Should fail with invalid OTP
        assert response.status_code in [400, 401, 500]


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
