"""
Real integration tests for Ghana Tourism Board tools.
Tests against actual JSON data files, no mocks.
"""
import pytest
import sys
import os

# Add parent to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

# Import from the actual file location
import importlib.util
spec = importlib.util.spec_from_file_location(
    "voice_agent_tools",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../voice_agent_tools.py"))
)
voice_agent_tools = importlib.util.module_from_spec(spec)
spec.loader.exec_module(voice_agent_tools)
GhanaTourismTools = voice_agent_tools.GhanaTourismTools


@pytest.fixture(scope="module")
def tools():
    """Initialize tools once for all tests."""
    return GhanaTourismTools()


class TestDestinationSearch:
    """Test destination search with real data."""

    def test_search_destinations_by_query(self, tools):
        """Test searching destinations by natural language query."""
        result = tools.search_destinations(query="beach", max_results=3)

        assert result["success"] is True
        assert len(result["destinations"]) > 0
        assert "voice_response" in result

        # Check that beach destinations are returned
        beach_found = any("beach" in dest["name"].lower() or
                         "beach" in dest["description"].lower()
                         for dest in result["destinations"])
        assert beach_found, "Should find beach-related destinations"

    def test_search_destinations_by_region(self, tools):
        """Test searching destinations by specific region."""
        result = tools.search_destinations(query="accra", region="Greater Accra")

        assert result["success"] is True
        assert len(result["destinations"]) > 0

        # All results should be in Greater Accra region
        for dest in result["destinations"]:
            assert dest["region"] == "Greater Accra"

    def test_search_destinations_by_category(self, tools):
        """Test searching destinations by category."""
        result = tools.search_destinations(query="historical sites", category="historical")

        assert result["success"] is True
        assert len(result["destinations"]) > 0

        # Check that historical sites are returned
        for dest in result["destinations"]:
            assert "historical" in dest["category"]

    def test_search_destinations_returns_voice_response(self, tools):
        """Test that voice response is properly formatted."""
        result = tools.search_destinations(query="park", max_results=2)

        assert result["success"] is True
        assert "voice_response" in result
        assert len(result["voice_response"]) > 50  # Should be descriptive


class TestDestinationDetails:
    """Test getting detailed destination information."""

    def test_get_kakum_details(self, tools):
        """Test getting Kakum National Park details."""
        result = tools.get_destination_details(destination_name="Kakum National Park")

        assert result["success"] is True
        assert result["destination"] is not None
        assert result["destination"]["name"] == "Kakum National Park"
        assert "canopy" in result["destination"]["description"].lower()
        assert result["destination"]["region"] == "Central"
        assert "activities" in result["destination"]
        assert len(result["destination"]["activities"]) > 0

    def test_get_cape_coast_castle_details(self, tools):
        """Test getting Cape Coast Castle details."""
        result = tools.get_destination_details(destination_name="Cape Coast Castle")

        assert result["success"] is True
        assert result["destination"]["name"] == "Cape Coast Castle"
        assert "UNESCO" in result["destination"]["description"]
        assert "historical" in result["destination"]["category"]
        assert result["destination"]["entry_fee"] is not None

    def test_get_nonexistent_destination(self, tools):
        """Test handling of non-existent destination."""
        result = tools.get_destination_details(destination_name="Nonexistent Place")

        assert result["success"] is False
        assert ("not found" in result["voice_response"].lower() or
                "couldn't find" in result["voice_response"].lower())


class TestAccommodationSearch:
    """Test accommodation search with real data."""

    def test_search_accommodation_in_accra(self, tools):
        """Test searching accommodations in Accra."""
        result = tools.search_accommodation(location="Accra", max_results=5)

        assert result["success"] is True
        assert len(result["accommodations"]) > 0

        # All should be in Accra or Greater Accra region
        for acc in result["accommodations"]:
            assert "Accra" in acc["city"] or "Accra" in acc["region"]

    def test_search_accommodation_by_type(self, tools):
        """Test searching accommodations by type."""
        result = tools.search_accommodation(location="Ghana", accommodation_type="hotel")

        assert result["success"] is True

        # All should be hotels
        for acc in result["accommodations"]:
            assert acc["type"] == "hotel"

    def test_search_accommodation_with_budget_filter(self, tools):
        """Test budget filtering."""
        result = tools.search_accommodation(location="Accra", budget_max_ghs=800)

        assert result["success"] is True
        assert len(result["accommodations"]) > 0

        # Check that price ranges respect budget
        for acc in result["accommodations"]:
            # Get minimum price from room types
            prices = [int(rt["price_range_ghs"].split("-")[0])
                     for rt in acc["room_types"]]
            assert min(prices) <= 800

    def test_search_resort_accommodation(self, tools):
        """Test searching for resorts."""
        result = tools.search_accommodation(location="Ghana", accommodation_type="resort")

        assert result["success"] is True

        # Should find resorts
        for acc in result["accommodations"]:
            assert acc["type"] == "resort"


class TestAccommodationDetails:
    """Test getting detailed accommodation information."""

    def test_get_kempinski_details(self, tools):
        """Test getting Kempinski Hotel details."""
        result = tools.get_accommodation_details(
            accommodation_name="Kempinski Hotel Gold Coast City"
        )

        assert result["success"] is True
        assert result["accommodation"]["name"] == "Kempinski Hotel Gold Coast City"
        assert result["accommodation"]["star_rating"] == 5
        assert result["accommodation"]["city"] == "Accra"
        assert len(result["accommodation"]["amenities"]) > 0
        assert len(result["accommodation"]["room_types"]) > 0

    def test_get_zaina_lodge_details(self, tools):
        """Test getting Zaina Lodge details."""
        result = tools.get_accommodation_details(accommodation_name="Zaina Lodge")

        assert result["success"] is True
        assert result["accommodation"]["name"] == "Zaina Lodge"
        assert result["accommodation"]["type"] == "lodge"
        assert "Mole" in result["accommodation"]["city"]

    def test_get_nonexistent_accommodation(self, tools):
        """Test handling of non-existent accommodation."""
        result = tools.get_accommodation_details(
            accommodation_name="Nonexistent Hotel"
        )

        assert result["success"] is False
        assert ("not found" in result["voice_response"].lower() or
                "couldn't find" in result["voice_response"].lower())


class TestVisaRequirements:
    """Test visa requirements retrieval."""

    def test_get_general_visa_info(self, tools):
        """Test getting general visa information."""
        result = tools.get_visa_requirements()

        assert result["success"] is True
        assert "visa_info" in result  # Response uses visa_info not visa_requirements

        # Check voice response
        assert "visa" in result["voice_response"].lower()
        assert "$150" in result["voice_response"] or "150" in result["voice_response"]

    def test_get_visa_info_for_ecowas(self, tools):
        """Test visa info for ECOWAS countries."""
        result = tools.get_visa_requirements(nationality="Nigeria")

        assert result["success"] is True
        assert "voice_response" in result
        assert len(result["voice_response"]) > 50  # Should provide information

    def test_get_visa_info_for_us(self, tools):
        """Test visa info for United States."""
        result = tools.get_visa_requirements(nationality="United States")

        assert result["success"] is True
        assert "e-visa" in result["voice_response"].lower() or \
               "evisa" in result["voice_response"].lower()


class TestSIMCardInfo:
    """Test SIM card information retrieval."""

    def test_get_all_sim_card_providers(self, tools):
        """Test getting info for all providers."""
        result = tools.get_sim_card_info()

        assert result["success"] is True
        assert "providers" in result
        assert len(result["providers"]) == 3

        provider_names = [p["name"] for p in result["providers"]]
        assert "MTN Ghana" in provider_names
        assert "Vodafone Ghana" in provider_names
        assert "AirtelTigo" in provider_names

    def test_get_mtn_sim_card_info(self, tools):
        """Test getting MTN-specific information."""
        result = tools.get_sim_card_info(preferred_provider="MTN")

        assert result["success"] is True
        assert "providers" in result

        # Should prioritize MTN
        assert result["providers"][0]["name"] == "MTN Ghana"
        assert "MTN" in result["voice_response"]

        # Check data plans exist
        assert len(result["providers"][0]["data_plans"]) > 0

    def test_sim_card_has_tourist_packages(self, tools):
        """Test that tourist packages are included."""
        result = tools.get_sim_card_info()

        assert result["success"] is True

        # Check that providers have tourist packages
        for provider in result["providers"]:
            assert "tourist_package" in provider
            assert "price_ghs" in provider["tourist_package"]


class TestSafetySecurity:
    """Test safety and security information."""

    def test_get_general_safety_tips(self, tools):
        """Test getting general safety information."""
        result = tools.get_safety_security_tips(category="general")

        assert result["success"] is True
        assert "safety_info" in result
        assert "voice_response" in result
        assert "safe" in result["voice_response"].lower()

    def test_get_health_safety_tips(self, tools):
        """Test getting health safety information."""
        result = tools.get_safety_security_tips(category="health")

        assert result["success"] is True
        assert "safety_info" in result
        assert "vaccinations" in result["voice_response"].lower() or \
               "malaria" in result["voice_response"].lower()

    def test_get_road_safety_tips(self, tools):
        """Test getting road safety information."""
        result = tools.get_safety_security_tips(category="road")

        assert result["success"] is True
        assert "voice_response" in result
        assert len(result["voice_response"]) > 50

    def test_get_scam_awareness_tips(self, tools):
        """Test getting scam awareness information."""
        result = tools.get_safety_security_tips(category="scams")

        assert result["success"] is True
        assert "voice_response" in result
        assert len(result["voice_response"]) > 50


class TestEmergencyContacts:
    """Test emergency contact information."""

    def test_get_emergency_contacts(self, tools):
        """Test retrieving emergency contacts."""
        result = tools.get_emergency_contacts()

        assert result["success"] is True
        assert "emergency_contacts" in result
        assert "police" in result["emergency_contacts"]
        assert "ambulance" in result["emergency_contacts"]
        assert "fire_service" in result["emergency_contacts"]

        # Check actual numbers
        assert result["emergency_contacts"]["police"] == "191 or 18555"
        assert result["emergency_contacts"]["ambulance"] == "193"
        assert result["emergency_contacts"]["fire_service"] == "192"

        # Check voice response includes numbers
        assert "191" in result["voice_response"]
        assert "193" in result["voice_response"]


class TestCurrencyExchange:
    """Test currency exchange information."""

    def test_get_currency_info(self, tools):
        """Test retrieving currency information."""
        result = tools.get_currency_exchange_info()

        assert result["success"] is True
        assert "currency_info" in result
        assert "currency" in result["currency_info"]
        assert result["currency_info"]["currency"] == "Ghana Cedi (GHS)"

        # Check exchange rate info exists
        assert "exchange_rate_approximation" in result["currency_info"]
        assert "where_to_exchange" in result["currency_info"]

    def test_currency_voice_response(self, tools):
        """Test currency voice response formatting."""
        result = tools.get_currency_exchange_info()

        assert result["success"] is True
        assert "cedi" in result["voice_response"].lower()
        assert "exchange" in result["voice_response"].lower()


class TestEscalation:
    """Test escalation functionality."""

    def test_escalate_booking_request(self, tools):
        """Test escalating a booking request."""
        result = tools.escalate_to_tourism_officer(
            issue_type="booking",
            description="Need to book 5-star hotel in Accra for 5 nights",
            contact_info="john@example.com"
        )

        assert result["success"] is True
        assert "escalation_id" in result
        assert "tourism officer" in result["voice_response"].lower()

    def test_escalate_custom_itinerary(self, tools):
        """Test escalating custom itinerary request."""
        result = tools.escalate_to_tourism_officer(
            issue_type="custom_itinerary",
            description="10-day Ghana cultural tour for family of 4",
            contact_info="+1-555-123-4567"
        )

        assert result["success"] is True
        assert result["escalation"]["issue_type"] == "custom_itinerary"
        assert result["escalation"]["contact_info"] == "+1-555-123-4567"


class TestDataIntegrity:
    """Test data file integrity and structure."""

    def test_all_destinations_have_required_fields(self, tools):
        """Test that all destinations have complete data."""
        result = tools.search_destinations(query="", max_results=20)

        for dest in result["destinations"]:
            assert "id" in dest
            assert "name" in dest
            assert "region" in dest
            assert "category" in dest
            assert "description" in dest
            assert "highlights" in dest
            assert "activities" in dest
            assert len(dest["activities"]) > 0

    def test_all_accommodations_have_required_fields(self, tools):
        """Test that all accommodations have complete data."""
        result = tools.search_accommodation(location="Ghana", max_results=20)

        for acc in result["accommodations"]:
            assert "id" in acc
            assert "name" in acc
            assert "region" in acc
            assert "city" in acc
            assert "type" in acc
            assert "description" in acc
            assert "amenities" in acc
            assert "room_types" in acc
            assert len(acc["room_types"]) > 0

            # Check room types have prices
            for room in acc["room_types"]:
                assert "type" in room
                assert "price_range_ghs" in room

    def test_practical_info_completeness(self, tools):
        """Test that practical info is complete."""
        # Test visa
        visa_result = tools.get_visa_requirements()
        assert visa_result["success"] is True

        # Test SIM cards
        sim_result = tools.get_sim_card_info()
        assert sim_result["success"] is True

        # Test currency
        currency_result = tools.get_currency_exchange_info()
        assert currency_result["success"] is True

        # Test emergency
        emergency_result = tools.get_emergency_contacts()
        assert emergency_result["success"] is True


class TestVoiceResponses:
    """Test that voice responses are properly formatted."""

    def test_voice_responses_are_conversational(self, tools):
        """Test that voice responses sound natural."""
        result = tools.search_destinations(query="beaches", max_results=2)

        voice = result["voice_response"]

        # Should be substantial
        assert len(voice) > 100

        # Should mention beaches
        assert "beach" in voice.lower()

        # Should have natural language markers
        natural_markers = ["i", "found", "recommend", "you", "here", "let me"]
        has_natural_language = any(marker in voice.lower() for marker in natural_markers)
        assert has_natural_language

    def test_voice_responses_avoid_json_structure(self, tools):
        """Test that voice responses don't leak JSON structure."""
        result = tools.get_destination_details("Kakum National Park")

        voice = result["voice_response"]

        # Should not contain JSON artifacts
        assert "{" not in voice
        assert "[" not in voice
        assert "null" not in voice.lower()

    def test_all_tools_return_voice_response(self, tools):
        """Test that all tools return voice_response field."""
        test_calls = [
            ("search_destinations", {"query": "beach"}),
            ("get_destination_details", {"destination_name": "Kakum National Park"}),
            ("search_accommodation", {"location": "Accra"}),
            ("get_visa_requirements", {}),
            ("get_sim_card_info", {}),
            ("get_safety_security_tips", {"category": "general"}),
            ("get_emergency_contacts", {}),
            ("get_currency_exchange_info", {}),
        ]

        for tool_name, params in test_calls:
            tool_method = getattr(tools, tool_name)
            result = tool_method(**params)

            assert "voice_response" in result, \
                f"{tool_name} should return voice_response"
            assert isinstance(result["voice_response"], str), \
                f"{tool_name} voice_response should be string"
            assert len(result["voice_response"]) > 0, \
                f"{tool_name} voice_response should not be empty"
