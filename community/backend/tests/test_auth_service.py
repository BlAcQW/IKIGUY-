"""
Unit tests for authentication service in African Language Community Platform.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from services.auth_service import AuthService
from models.user_models import User, UserCreate, UserProfile
from core.exceptions import AuthenticationError, ValidationError


class TestAuthService:
    """Test AuthService functionality."""

    @pytest.fixture
    def auth_service(self):
        """Create AuthService instance for testing."""
        return AuthService()

    @pytest.fixture
    def sample_user_data(self):
        """Sample user data for testing."""
        return {
            "email": "test@example.com",
            "full_name": "Test User",
            "username": "testuser",
            "location": "Ghana",
            "bio": "Test bio",
            "languages_spoken": ["twi", "eng"]
        }

    @pytest.fixture
    def sample_user(self, sample_user_data):
        """Sample User model instance."""
        return User(
            id="507f1f77bcf86cd799439011",
            supabase_id="supabase123",
            email=sample_user_data["email"],
            full_name=sample_user_data["full_name"],
            username=sample_user_data["username"],
            location=sample_user_data["location"],
            bio=sample_user_data["bio"],
            languages_spoken=sample_user_data["languages_spoken"],
            level="newcomer",
            total_points=0,
            achievements=[],
            badges=[],
            language_expertise=[],
            verified_languages=[],
            can_validate=False,
            can_moderate=False,
            can_create_proposals=False,
            contributions_count=0,
            validations_count=0,
            quality_rating=0.0,
            reputation_score=0.0,
            is_active=True,
            member_since=datetime.utcnow().isoformat()
        )

    @patch('services.auth_service.get_supabase_user')
    @patch('services.auth_service.mongodb')
    async def test_verify_token_success(self, mock_db, mock_supabase, auth_service, sample_user):
        """Test successful token verification."""
        # Mock Supabase response
        mock_supabase.return_value = {
            "id": "supabase123",
            "email": "test@example.com"
        }

        # Mock database response
        mock_db.users.find_one.return_value = sample_user.dict()

        token = "valid_token"
        user = await auth_service.verify_token(token)

        assert user.email == "test@example.com"
        assert user.supabase_id == "supabase123"
        mock_supabase.assert_called_once_with(token)

    @patch('services.auth_service.get_supabase_user')
    async def test_verify_token_invalid(self, mock_supabase, auth_service):
        """Test token verification with invalid token."""
        mock_supabase.side_effect = Exception("Invalid token")

        with pytest.raises(AuthenticationError, match="Invalid authentication token"):
            await auth_service.verify_token("invalid_token")

    @patch('services.auth_service.mongodb')
    async def test_register_user_success(self, mock_db, auth_service, sample_user_data):
        """Test successful user registration."""
        # Mock database operations
        mock_db.users.find_one.return_value = None  # User doesn't exist
        mock_db.users.insert_one.return_value = MagicMock(inserted_id="507f1f77bcf86cd799439011")
        mock_db.users.find_one.return_value = {
            **sample_user_data,
            "_id": "507f1f77bcf86cd799439011",
            "supabase_id": "supabase123",
            "level": "newcomer",
            "total_points": 0
        }

        user_create = UserCreate(**sample_user_data)
        user = await auth_service.register_user("supabase123", user_create)

        assert user.email == sample_user_data["email"]
        assert user.level == "newcomer"
        assert user.total_points == 0
        mock_db.users.insert_one.assert_called_once()

    @patch('services.auth_service.mongodb')
    async def test_register_user_duplicate_email(self, mock_db, auth_service, sample_user_data):
        """Test user registration with duplicate email."""
        # Mock existing user
        mock_db.users.find_one.return_value = {"email": sample_user_data["email"]}

        user_create = UserCreate(**sample_user_data)
        with pytest.raises(ValidationError, match="User already exists"):
            await auth_service.register_user("supabase123", user_create)

    @patch('services.auth_service.mongodb')
    async def test_get_user_profile_success(self, mock_db, auth_service, sample_user):
        """Test successful user profile retrieval."""
        mock_db.users.find_one.return_value = sample_user.dict()

        profile = await auth_service.get_user_profile("507f1f77bcf86cd799439011")

        assert profile.email == sample_user.email
        assert profile.full_name == sample_user.full_name
        mock_db.users.find_one.assert_called_once()

    @patch('services.auth_service.mongodb')
    async def test_get_user_profile_not_found(self, mock_db, auth_service):
        """Test user profile retrieval when user doesn't exist."""
        mock_db.users.find_one.return_value = None

        with pytest.raises(ValidationError, match="User not found"):
            await auth_service.get_user_profile("nonexistent_id")

    @patch('services.auth_service.mongodb')
    async def test_update_user_profile_success(self, mock_db, auth_service, sample_user):
        """Test successful user profile update."""
        update_data = {
            "full_name": "Updated Name",
            "bio": "Updated bio",
            "languages_spoken": ["twi", "ga", "eng"]
        }

        # Mock database operations
        mock_db.users.find_one.return_value = sample_user.dict()
        mock_db.users.update_one.return_value = MagicMock(modified_count=1)
        updated_user_data = {**sample_user.dict(), **update_data}
        mock_db.users.find_one.return_value = updated_user_data

        updated_user = await auth_service.update_user_profile("507f1f77bcf86cd799439011", update_data)

        assert updated_user.full_name == "Updated Name"
        assert updated_user.bio == "Updated bio"
        assert len(updated_user.languages_spoken) == 3
        mock_db.users.update_one.assert_called_once()

    @patch('services.auth_service.mongodb')
    async def test_update_user_points(self, mock_db, auth_service, sample_user):
        """Test user points update."""
        points_to_add = 50

        # Mock database operations
        mock_db.users.find_one.return_value = sample_user.dict()
        mock_db.users.update_one.return_value = MagicMock(modified_count=1)
        updated_user_data = sample_user.dict()
        updated_user_data["total_points"] = points_to_add

        updated_user = await auth_service.update_user_points("507f1f77bcf86cd799439011", points_to_add)

        assert updated_user.total_points == points_to_add
        mock_db.users.update_one.assert_called_once()

    @patch('services.auth_service.mongodb')
    async def test_award_achievement(self, mock_db, auth_service, sample_user):
        """Test achievement awarding."""
        achievement_id = "first_contribution"

        # Mock database operations
        mock_db.users.find_one.return_value = sample_user.dict()
        mock_db.users.update_one.return_value = MagicMock(modified_count=1)
        updated_user_data = sample_user.dict()
        updated_user_data["achievements"] = [achievement_id]

        updated_user = await auth_service.award_achievement("507f1f77bcf86cd799439011", achievement_id)

        assert achievement_id in updated_user.achievements
        mock_db.users.update_one.assert_called_once()

    def test_calculate_user_level(self, auth_service):
        """Test user level calculation based on points."""
        # Test level progression
        assert auth_service.calculate_user_level(0) == "newcomer"
        assert auth_service.calculate_user_level(100) == "contributor"
        assert auth_service.calculate_user_level(500) == "validator"
        assert auth_service.calculate_user_level(1500) == "expert"
        assert auth_service.calculate_user_level(5000) == "guardian"

    def test_validate_username(self, auth_service):
        """Test username validation."""
        # Valid usernames
        assert auth_service.validate_username("testuser") is True
        assert auth_service.validate_username("test_user") is True
        assert auth_service.validate_username("test123") is True

        # Invalid usernames
        assert auth_service.validate_username("te") is False  # Too short
        assert auth_service.validate_username("test user") is False  # Contains space
        assert auth_service.validate_username("test@user") is False  # Contains @
        assert auth_service.validate_username("") is False  # Empty

    @patch('services.auth_service.mongodb')
    async def test_check_username_availability(self, mock_db, auth_service):
        """Test username availability checking."""
        # Username available
        mock_db.users.find_one.return_value = None
        available = await auth_service.check_username_availability("newuser")
        assert available is True

        # Username taken
        mock_db.users.find_one.return_value = {"username": "existinguser"}
        available = await auth_service.check_username_availability("existinguser")
        assert available is False

    def test_sanitize_user_input(self, auth_service):
        """Test user input sanitization."""
        # Test basic sanitization
        clean_text = auth_service.sanitize_user_input("  Clean Text  ")
        assert clean_text == "Clean Text"

        # Test HTML removal
        html_text = auth_service.sanitize_user_input("<script>alert('test')</script>Hello")
        assert "<script>" not in html_text
        assert "Hello" in html_text

        # Test length limitation
        long_text = "a" * 1000
        short_text = auth_service.sanitize_user_input(long_text, max_length=100)
        assert len(short_text) <= 100