"""
Additional unit tests for email authentication in African Language Community Platform.

Tests specific email signup and signin flows.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime
from bson import ObjectId

from services.auth_service import AuthService
from models.user_models import UserCreate, User
from core.exceptions import AuthenticationError, ValidationError


class TestEmailAuthentication:
    """Test email-specific authentication functionality."""

    @pytest.fixture
    def auth_service(self):
        """Create AuthService instance for testing."""
        return AuthService()

    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client for testing."""
        mock_client = AsyncMock()
        mock_client.auth.sign_up.return_value = Mock(
            user=Mock(id="supabase123", email="test@example.com"),
            error=None
        )
        mock_client.auth.sign_in_with_password.return_value = Mock(
            user=Mock(id="supabase123", email="test@example.com"),
            session=Mock(access_token="token123"),
            error=None
        )
        return mock_client

    @pytest.fixture
    def valid_email_data(self):
        """Valid email authentication data."""
        return {
            "email": "test@example.com",
            "password": "SecurePassword123!",
            "full_name": "Test User",
            "username": "testuser123",
            "location": "Accra, Ghana",
            "languages_spoken": ["twi", "eng"]
        }

    @pytest.fixture
    def invalid_email_data(self):
        """Invalid email authentication data."""
        return {
            "email": "invalid-email",
            "password": "123",
            "full_name": "",
            "username": ""
        }

    @pytest.mark.asyncio
    async def test_email_signup_success(self, auth_service, mock_db, valid_email_data):
        """
        Test successful email signup.

        Expected use: User provides valid email and password, account created successfully.
        """
        # Mock database operations
        mock_db.users.find_one.return_value = None  # Email not exists
        mock_result = Mock()
        mock_result.inserted_id = ObjectId()
        mock_db.users.insert_one.return_value = mock_result

        user_create = UserCreate(**valid_email_data)

        with patch.object(auth_service, '_get_db', return_value=mock_db):
            with patch.object(auth_service, 'supabase_client') as mock_supabase:
                mock_supabase.auth.sign_up.return_value = Mock(
                    user=Mock(id="supabase123", email=valid_email_data["email"]),
                    error=None
                )

                user = await auth_service.register_user("supabase123", user_create)

                assert user.email == valid_email_data["email"]
                assert user.full_name == valid_email_data["full_name"]
                assert user.username == valid_email_data["username"]
                assert user.supabase_id == "supabase123"

    @pytest.mark.asyncio
    async def test_email_signup_duplicate_email(self, auth_service, mock_db, valid_email_data):
        """
        Test email signup with duplicate email.

        Failure case: User tries to register with email that already exists.
        """
        # Mock existing user
        existing_user = {
            "_id": ObjectId(),
            "email": valid_email_data["email"],
            "supabase_id": "existing123"
        }
        mock_db.users.find_one.return_value = existing_user

        user_create = UserCreate(**valid_email_data)

        with patch.object(auth_service, '_get_db', return_value=mock_db):
            with pytest.raises(ValidationError, match="Email already registered"):
                await auth_service.register_user("supabase123", user_create)

    @pytest.mark.asyncio
    async def test_email_signup_invalid_email_format(self, auth_service):
        """
        Test email signup with invalid email format.

        Failure case: User provides malformed email address.
        """
        with pytest.raises(ValidationError):
            UserCreate(
                email="not-an-email",
                password="ValidPassword123!",
                full_name="Test User",
                username="testuser"
            )

    @pytest.mark.asyncio
    async def test_email_signup_weak_password(self, auth_service):
        """
        Test email signup with weak password.

        Edge case: User provides password that doesn't meet strength requirements.
        """
        # Test short password
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                password="123",
                full_name="Test User",
                username="testuser"
            )

        # Test password without complexity (if implemented)
        # This would depend on your password validation rules

    @pytest.mark.asyncio
    async def test_email_signin_success(self, auth_service, mock_db, valid_email_data):
        """
        Test successful email signin.

        Expected use: User provides correct email and password, gets authenticated.
        """
        # Mock existing user in database
        existing_user = {
            "_id": ObjectId(),
            "email": valid_email_data["email"],
            "supabase_id": "supabase123",
            "full_name": valid_email_data["full_name"],
            "active": True
        }
        mock_db.users.find_one.return_value = existing_user

        with patch.object(auth_service, '_get_db', return_value=mock_db):
            with patch.object(auth_service, 'supabase_client') as mock_supabase:
                mock_supabase.auth.sign_in_with_password.return_value = Mock(
                    user=Mock(id="supabase123", email=valid_email_data["email"]),
                    session=Mock(access_token="token123"),
                    error=None
                )

                user = await auth_service.authenticate_user(
                    valid_email_data["email"],
                    valid_email_data["password"]
                )

                assert user.email == valid_email_data["email"]
                assert user.supabase_id == "supabase123"

    @pytest.mark.asyncio
    async def test_email_signin_invalid_credentials(self, auth_service, mock_db):
        """
        Test email signin with invalid credentials.

        Failure case: User provides wrong email or password.
        """
        with patch.object(auth_service, '_get_db', return_value=mock_db):
            with patch.object(auth_service, 'supabase_client') as mock_supabase:
                mock_supabase.auth.sign_in_with_password.return_value = Mock(
                    user=None,
                    session=None,
                    error=Mock(message="Invalid credentials")
                )

                with pytest.raises(AuthenticationError, match="Invalid credentials"):
                    await auth_service.authenticate_user("wrong@example.com", "wrongpass")

    @pytest.mark.asyncio
    async def test_email_signin_nonexistent_user(self, auth_service, mock_db):
        """
        Test email signin for user that doesn't exist in our database.

        Edge case: User exists in Supabase but not in our MongoDB.
        """
        # Mock user not found in our database
        mock_db.users.find_one.return_value = None

        with patch.object(auth_service, '_get_db', return_value=mock_db):
            with patch.object(auth_service, 'supabase_client') as mock_supabase:
                mock_supabase.auth.sign_in_with_password.return_value = Mock(
                    user=Mock(id="supabase123", email="test@example.com"),
                    session=Mock(access_token="token123"),
                    error=None
                )

                with pytest.raises(AuthenticationError, match="User not found"):
                    await auth_service.authenticate_user("test@example.com", "password123")

    @pytest.mark.asyncio
    async def test_email_signin_inactive_user(self, auth_service, mock_db):
        """
        Test email signin for inactive/banned user.

        Edge case: User account exists but is deactivated.
        """
        # Mock inactive user
        inactive_user = {
            "_id": ObjectId(),
            "email": "test@example.com",
            "supabase_id": "supabase123",
            "active": False,
            "banned": True
        }
        mock_db.users.find_one.return_value = inactive_user

        with patch.object(auth_service, '_get_db', return_value=mock_db):
            with pytest.raises(AuthenticationError, match="Account is deactivated"):
                await auth_service.authenticate_user("test@example.com", "password123")

    @pytest.mark.asyncio
    async def test_email_validation_edge_cases(self, auth_service):
        """
        Test various email validation edge cases.

        Edge case: Test boundary conditions for email validation.
        """
        invalid_emails = [
            "",  # Empty email
            "plainaddress",  # No @ symbol
            "@domain.com",  # Missing local part
            "user@",  # Missing domain
            "user@.com",  # Invalid domain
            "user@domain",  # Missing TLD
            "user..user@domain.com",  # Double dots
            "user@domain..com",  # Double dots in domain
            "user name@domain.com",  # Space in local part
            "user@domain .com",  # Space in domain
        ]

        for email in invalid_emails:
            with pytest.raises(ValidationError):
                UserCreate(
                    email=email,
                    password="ValidPassword123!",
                    full_name="Test User",
                    username="testuser"
                )

    @pytest.mark.asyncio
    async def test_password_validation_edge_cases(self, auth_service):
        """
        Test various password validation edge cases.

        Edge case: Test boundary conditions for password validation.
        """
        invalid_passwords = [
            "",  # Empty password
            "12345",  # Too short
            "password",  # Common password (if implemented)
            "PASSWORD",  # No lowercase (if complexity required)
            "password123",  # No uppercase (if complexity required)
            "PasswordABC",  # No numbers (if complexity required)
        ]

        for password in invalid_passwords:
            with pytest.raises(ValidationError):
                UserCreate(
                    email="test@example.com",
                    password=password,
                    full_name="Test User",
                    username="testuser"
                )

    @pytest.mark.asyncio
    async def test_username_validation(self, auth_service, mock_db):
        """
        Test username validation during signup.

        Edge case: Test username uniqueness and format validation.
        """
        # Test duplicate username
        existing_user = {
            "_id": ObjectId(),
            "username": "testuser",
            "email": "other@example.com"
        }
        mock_db.users.find_one.return_value = existing_user

        user_create = UserCreate(
            email="new@example.com",
            password="ValidPassword123!",
            full_name="New User",
            username="testuser"  # Duplicate username
        )

        with patch.object(auth_service, '_get_db', return_value=mock_db):
            with pytest.raises(ValidationError, match="Username already taken"):
                await auth_service.register_user("supabase123", user_create)

    @pytest.mark.asyncio
    async def test_email_verification_workflow(self, auth_service, mock_db):
        """
        Test email verification workflow integration.

        Expected use: User signs up, receives verification email, verifies account.
        """
        user_create = UserCreate(
            email="test@example.com",
            password="ValidPassword123!",
            full_name="Test User",
            username="testuser"
        )

        mock_db.users.find_one.return_value = None
        mock_result = Mock()
        mock_result.inserted_id = ObjectId()
        mock_db.users.insert_one.return_value = mock_result

        with patch.object(auth_service, '_get_db', return_value=mock_db):
            with patch.object(auth_service, 'supabase_client') as mock_supabase:
                # Mock Supabase signup with email confirmation required
                mock_supabase.auth.sign_up.return_value = Mock(
                    user=Mock(
                        id="supabase123",
                        email="test@example.com",
                        email_confirmed_at=None  # Not yet confirmed
                    ),
                    error=None
                )

                user = await auth_service.register_user("supabase123", user_create)

                # User should be created but not yet verified
                assert user.email == "test@example.com"
                # Additional verification logic would be tested here
                # depending on your implementation

    @pytest.mark.asyncio
    async def test_rate_limiting_email_auth(self, auth_service, mock_db):
        """
        Test rate limiting for email authentication attempts.

        Edge case: Prevent brute force attacks on email authentication.
        """
        # This test would depend on your rate limiting implementation
        # Example: Test that after 5 failed attempts, further attempts are blocked

        mock_db.users.find_one.return_value = None  # User doesn't exist

        with patch.object(auth_service, '_get_db', return_value=mock_db):
            with patch.object(auth_service, 'supabase_client') as mock_supabase:
                mock_supabase.auth.sign_in_with_password.return_value = Mock(
                    user=None,
                    session=None,
                    error=Mock(message="Invalid credentials")
                )

                # Simulate multiple failed attempts
                for i in range(6):  # Exceed rate limit
                    with pytest.raises(AuthenticationError):
                        await auth_service.authenticate_user("test@example.com", "wrongpass")

                # After rate limit exceeded, should get different error
                # This would depend on your specific rate limiting implementation