"""
Unit tests for BusService.

Tests bus route management and registration functionality.
"""

import pytest
from datetime import datetime
from bson import ObjectId
from unittest.mock import patch, MagicMock

from app.services.bus_service import BusService


@pytest.mark.asyncio
class TestBusService:
    """Test cases for BusService."""

    async def test_create_bus_route_success(self, test_db):
        """
        Test successful bus route creation.

        Expected: Route created with all fields populated.
        """
        # Mock database connection
        with patch('app.services.bus_service.get_database', return_value=test_db):
            service = BusService()

            route_data = {
                "route_name": "Test Route",
                "pickup_location": "Test Location",
                "departure_time": datetime(2025, 12, 25, 7, 0),
                "capacity": 40,
                "conference_id": ObjectId(),
                "driver_name": "Test Driver",
                "driver_phone": "+233200000001",
                "status": "scheduled",
                "gate_number": "Gate 1"
            }

            result = await service.create_bus_route(route_data)

            # Assertions
            assert result is not None
            assert result.route_name == "Test Route"
            assert result.capacity == 40
            assert result.registered_count == 0
            assert result.created_at is not None

    async def test_create_bus_route_with_invalid_data(self, test_db):
        """
        Test bus route creation with missing required fields.

        Expected: Exception raised for invalid data.
        """
        with patch('app.services.bus_service.get_database', return_value=test_db):
            service = BusService()

            route_data = {
                "route_name": "Test Route"
                # Missing required fields
            }

            with pytest.raises(Exception):
                await service.create_bus_route(route_data)

    async def test_get_bus_route_success(self, test_db, sample_bus_route):
        """
        Test retrieving bus route by ID.

        Expected: Route retrieved successfully.
        """
        with patch('app.services.bus_service.get_database', return_value=test_db):
            service = BusService()

            result = await service.get_bus_route(str(sample_bus_route["_id"]))

            # Assertions
            assert result is not None
            assert result.route_name == sample_bus_route["route_name"]
            assert result.capacity == sample_bus_route["capacity"]

    async def test_get_bus_route_invalid_id(self, test_db):
        """
        Test retrieving bus route with invalid ID.

        Expected: None returned.
        """
        with patch('app.services.bus_service.get_database', return_value=test_db):
            service = BusService()

            result = await service.get_bus_route("invalid_id")

            # Assertions
            assert result is None

    async def test_get_bus_route_not_found(self, test_db):
        """
        Test retrieving non-existent bus route.

        Expected: None returned.
        """
        with patch('app.services.bus_service.get_database', return_value=test_db):
            service = BusService()

            result = await service.get_bus_route(str(ObjectId()))

            # Assertions
            assert result is None

    async def test_list_bus_routes_no_filters(self, test_db, sample_bus_route):
        """
        Test listing all bus routes without filters.

        Expected: All routes returned.
        """
        with patch('app.services.bus_service.get_database', return_value=test_db):
            service = BusService()

            results = await service.list_bus_routes()

            # Assertions
            assert len(results) >= 1
            assert any(r.route_name == sample_bus_route["route_name"] for r in results)

    async def test_list_bus_routes_with_conference_filter(
        self, test_db, sample_bus_route, sample_conference
    ):
        """
        Test listing bus routes filtered by conference.

        Expected: Only routes for specified conference returned.
        """
        with patch('app.services.bus_service.get_database', return_value=test_db):
            service = BusService()

            results = await service.list_bus_routes(
                conference_id=str(sample_conference["_id"])
            )

            # Assertions
            assert len(results) >= 1
            assert all(str(r.conference_id) == str(sample_conference["_id"]) for r in results)

    async def test_list_bus_routes_with_status_filter(self, test_db, sample_bus_route):
        """
        Test listing bus routes filtered by status.

        Expected: Only routes with specified status returned.
        """
        with patch('app.services.bus_service.get_database', return_value=test_db):
            service = BusService()

            results = await service.list_bus_routes(status="scheduled")

            # Assertions
            assert len(results) >= 1
            assert all(r.status == "scheduled" for r in results)

    async def test_update_bus_route_success(self, test_db, sample_bus_route):
        """
        Test updating bus route.

        Expected: Route updated successfully.
        """
        with patch('app.services.bus_service.get_database', return_value=test_db):
            service = BusService()

            update_data = {
                "status": "delayed",
                "driver_name": "Updated Driver"
            }

            result = await service.update_bus_route(
                str(sample_bus_route["_id"]), update_data
            )

            # Assertions
            assert result is not None
            assert result.status == "delayed"
            assert result.driver_name == "Updated Driver"
            assert result.updated_at is not None

    async def test_update_bus_route_invalid_id(self, test_db):
        """
        Test updating bus route with invalid ID.

        Expected: None returned.
        """
        with patch('app.services.bus_service.get_database', return_value=test_db):
            service = BusService()

            result = await service.update_bus_route("invalid_id", {"status": "delayed"})

            # Assertions
            assert result is None

    async def test_delete_bus_route_success(self, test_db, sample_bus_route):
        """
        Test deleting bus route.

        Expected: Route and associated registrations deleted.
        """
        with patch('app.services.bus_service.get_database', return_value=test_db):
            service = BusService()

            result = await service.delete_bus_route(str(sample_bus_route["_id"]))

            # Assertions
            assert result is True

            # Verify route is deleted
            deleted_route = await service.get_bus_route(str(sample_bus_route["_id"]))
            assert deleted_route is None

    async def test_delete_bus_route_invalid_id(self, test_db):
        """
        Test deleting bus route with invalid ID.

        Expected: False returned.
        """
        with patch('app.services.bus_service.get_database', return_value=test_db):
            service = BusService()

            result = await service.delete_bus_route("invalid_id")

            # Assertions
            assert result is False

    async def test_register_for_bus_success(
        self, test_db, sample_user, sample_bus_route, sample_conference
    ):
        """
        Test successful bus registration.

        Expected: User registered and capacity updated.
        """
        with patch('app.services.bus_service.get_database', return_value=test_db):
            service = BusService()

            result = await service.register_for_bus(
                user_id=str(sample_user["_id"]),
                bus_route_id=str(sample_bus_route["_id"]),
                conference_id=str(sample_conference["_id"])
            )

            # Assertions
            assert result is not None
            assert result.user_id == sample_user["_id"]
            assert result.bus_route_id == sample_bus_route["_id"]
            assert result.status == "confirmed"

            # Verify registered count updated
            updated_route = await service.get_bus_route(str(sample_bus_route["_id"]))
            assert updated_route.registered_count == 1

    async def test_register_for_bus_route_not_found(
        self, test_db, sample_user, sample_conference
    ):
        """
        Test registering for non-existent bus route.

        Expected: Exception raised.
        """
        with patch('app.services.bus_service.get_database', return_value=test_db):
            service = BusService()

            with pytest.raises(Exception, match="Bus route not found"):
                await service.register_for_bus(
                    user_id=str(sample_user["_id"]),
                    bus_route_id=str(ObjectId()),
                    conference_id=str(sample_conference["_id"])
                )

    async def test_register_for_bus_already_full(
        self, test_db, sample_user, sample_bus_route, sample_conference
    ):
        """
        Test registering for full bus.

        Expected: Exception raised.
        """
        with patch('app.services.bus_service.get_database', return_value=test_db):
            service = BusService()

            # Update route to be full
            await test_db.bus_routes.update_one(
                {"_id": sample_bus_route["_id"]},
                {"$set": {"registered_count": sample_bus_route["capacity"]}}
            )

            with pytest.raises(Exception, match="Bus is full"):
                await service.register_for_bus(
                    user_id=str(sample_user["_id"]),
                    bus_route_id=str(sample_bus_route["_id"]),
                    conference_id=str(sample_conference["_id"])
                )

    async def test_register_for_bus_duplicate_registration(
        self, test_db, sample_user, sample_bus_route, sample_conference
    ):
        """
        Test duplicate registration for same conference.

        Expected: Exception raised.
        """
        with patch('app.services.bus_service.get_database', return_value=test_db):
            service = BusService()

            # First registration
            await service.register_for_bus(
                user_id=str(sample_user["_id"]),
                bus_route_id=str(sample_bus_route["_id"]),
                conference_id=str(sample_conference["_id"])
            )

            # Second registration attempt
            with pytest.raises(Exception, match="User already registered for a bus"):
                await service.register_for_bus(
                    user_id=str(sample_user["_id"]),
                    bus_route_id=str(sample_bus_route["_id"]),
                    conference_id=str(sample_conference["_id"])
                )

    async def test_register_for_bus_updates_status_when_full(
        self, test_db, sample_user, sample_bus_route, sample_conference
    ):
        """
        Test bus status changes to 'full' when capacity reached.

        Expected: Status updated to 'full'.
        """
        with patch('app.services.bus_service.get_database', return_value=test_db):
            service = BusService()

            # Set capacity to 1
            await test_db.bus_routes.update_one(
                {"_id": sample_bus_route["_id"]},
                {"$set": {"capacity": 1}}
            )

            # Register user (should fill the bus)
            await service.register_for_bus(
                user_id=str(sample_user["_id"]),
                bus_route_id=str(sample_bus_route["_id"]),
                conference_id=str(sample_conference["_id"])
            )

            # Verify status changed to full
            updated_route = await service.get_bus_route(str(sample_bus_route["_id"]))
            assert updated_route.status == "full"
