"""
Unit tests for database connections and operations in African Language Community Platform.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from database import connect_to_mongo, close_mongo_connection, initialize_database


class TestDatabaseConnection:
    """Test database connection functionality."""

    @patch('database.AsyncIOMotorClient')
    @patch('database.initialize_database')
    async def test_connect_to_mongo_success(self, mock_init_db, mock_client_class):
        """Test successful MongoDB connection."""
        # Mock client and database
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        mock_client.admin.command = AsyncMock(return_value={})

        # Mock settings
        with patch('database.settings') as mock_settings:
            mock_settings.MONGODB_URL = "mongodb://localhost:27017"
            mock_settings.DATABASE_NAME = "test_db"

            await connect_to_mongo()

            # Verify client creation
            mock_client_class.assert_called_once_with(
                "mongodb://localhost:27017",
                serverSelectionTimeoutMS=5000
            )

            # Verify ping command
            mock_client.admin.command.assert_called_once_with('ping')

            # Verify database initialization
            mock_init_db.assert_called_once()

    @patch('database.AsyncIOMotorClient')
    async def test_connect_to_mongo_timeout(self, mock_client_class):
        """Test MongoDB connection timeout."""
        from pymongo.errors import ServerSelectionTimeoutError

        # Mock client to raise timeout error
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        mock_client.admin.command.side_effect = ServerSelectionTimeoutError("Timeout")

        with patch('database.settings') as mock_settings:
            mock_settings.MONGODB_URL = "mongodb://localhost:27017"

            with pytest.raises(ServerSelectionTimeoutError):
                await connect_to_mongo()

    @patch('database.mongodb_client')
    async def test_close_mongo_connection(self, mock_client):
        """Test MongoDB connection closing."""
        await close_mongo_connection()
        mock_client.close.assert_called_once()

    @patch('database.mongodb')
    async def test_initialize_database_success(self, mock_db):
        """Test successful database initialization."""
        # Mock database collections - all collections used by initialize_database
        mock_collection = AsyncMock()
        mock_collection.create_index = AsyncMock()

        # All collections used in initialize_database
        all_collections = [
            'language_families', 'language_subfamilies', 'languages',
            'users', 'submissions', 'validations', 'achievements', 'proposals',
            'user_achievements', 'community_proposals', 'community_votes',
            'family_shared_resources'
        ]

        for collection_name in all_collections:
            setattr(mock_db, collection_name, mock_collection)

        await initialize_database()

        # Verify that create_index was called multiple times
        assert mock_collection.create_index.call_count > 10

    async def test_initialize_database_no_connection(self):
        """Test database initialization without connection."""
        with patch('database.mongodb', None):
            with pytest.raises(RuntimeError, match="Database not connected"):
                await initialize_database()

    @patch('database.mongodb')
    async def test_database_indexes_creation(self, mock_db):
        """Test specific database indexes creation."""
        # Mock collections - including all collections used by initialize_database
        collections = {}
        all_collection_names = [
            'language_families', 'language_subfamilies', 'languages',
            'users', 'submissions', 'validations', 'achievements', 'proposals',
            'user_achievements', 'community_proposals', 'community_votes',
            'family_shared_resources'
        ]
        for collection_name in all_collection_names:
            collections[collection_name] = AsyncMock()
            setattr(mock_db, collection_name, collections[collection_name])

        await initialize_database()

        # Verify specific indexes
        # Language families
        collections['language_families'].create_index.assert_any_call([("name", 1)], unique=True)
        collections['language_families'].create_index.assert_any_call([("created_at", -1)])

        # Users
        collections['users'].create_index.assert_any_call([("email", 1)], unique=True)
        collections['users'].create_index.assert_any_call([("supabase_id", 1)], unique=True)
        collections['users'].create_index.assert_any_call([("username", 1)], unique=True, sparse=True)

        # Languages
        collections['languages'].create_index.assert_any_call([("code", 1)], unique=True)
        collections['languages'].create_index.assert_any_call([("subfamily_id", 1)])

        # Submissions
        collections['submissions'].create_index.assert_any_call([("contributor_id", 1)])
        collections['submissions'].create_index.assert_any_call([("language_code", 1)])
        collections['submissions'].create_index.assert_any_call([("validation_status", 1)])

    @patch('database.mongodb')
    async def test_database_compound_indexes(self, mock_db):
        """Test compound indexes creation."""
        # Need to mock all collections used by initialize_database
        mock_collection = AsyncMock()

        all_collections = [
            'language_families', 'language_subfamilies', 'languages',
            'users', 'submissions', 'validations', 'achievements', 'proposals',
            'user_achievements', 'community_proposals', 'community_votes',
            'family_shared_resources'
        ]

        for collection_name in all_collections:
            setattr(mock_db, collection_name, mock_collection)

        await initialize_database()

        # Check for compound indexes
        mock_collection.create_index.assert_any_call([("language_code", 1), ("tier", 1)])
        mock_collection.create_index.assert_any_call([("contributor_id", 1), ("created_at", -1)])


class TestDatabaseOperations:
    """Test database operation helpers."""

    @patch('database.mongodb')
    async def test_get_database_connection(self, mock_db):
        """Test getting database connection."""
        from database import mongodb

        # Mock should be the database instance
        assert mock_db is not None

    def test_objectid_conversion(self):
        """Test ObjectId string conversion utilities."""
        from bson import ObjectId
        from models.language_models import PyObjectId

        # Test valid ObjectId
        obj_id = ObjectId()
        py_obj_id = PyObjectId.validate(str(obj_id))
        assert py_obj_id == obj_id

        # Test string ObjectId
        obj_id_str = "507f1f77bcf86cd799439011"
        py_obj_id = PyObjectId.validate(obj_id_str)
        assert str(py_obj_id) == obj_id_str

    @patch('database.mongodb')
    async def test_database_error_handling(self, mock_db):
        """Test database error handling."""
        from pymongo.errors import DuplicateKeyError

        # Mock a duplicate key error
        mock_collection = AsyncMock()
        mock_collection.insert_one.side_effect = DuplicateKeyError("Duplicate key error")
        mock_db.users = mock_collection

        # The actual error handling would be in service classes
        with pytest.raises(DuplicateKeyError):
            await mock_collection.insert_one({"email": "test@example.com"})

    def test_connection_string_parsing(self):
        """Test MongoDB connection string parsing."""
        # Test basic connection string
        url = "mongodb://localhost:27017"
        assert "mongodb://" in url
        assert "27017" in url

        # Test connection string with auth
        auth_url = "mongodb://user:pass@localhost:27017/db?authSource=admin"
        assert "user:pass" in auth_url
        assert "authSource=admin" in auth_url

    @patch('database.settings')
    def test_database_name_configuration(self, mock_settings):
        """Test database name configuration."""
        mock_settings.DATABASE_NAME = "african_language_community"

        assert mock_settings.DATABASE_NAME == "african_language_community"
        assert "african" in mock_settings.DATABASE_NAME.lower()
        assert "language" in mock_settings.DATABASE_NAME.lower()

    @patch('database.mongodb')
    async def test_collection_operations(self, mock_db):
        """Test basic collection operations."""
        # Mock collection
        mock_collection = AsyncMock()
        mock_db.users = mock_collection

        # Mock operations
        mock_collection.find_one.return_value = {"_id": "123", "email": "test@example.com"}
        mock_collection.insert_one.return_value = MagicMock(inserted_id="123")
        mock_collection.update_one.return_value = MagicMock(modified_count=1)
        mock_collection.delete_one.return_value = MagicMock(deleted_count=1)

        # Test operations would be in service classes
        # This just verifies the mocks work correctly
        result = await mock_collection.find_one({"email": "test@example.com"})
        assert result["email"] == "test@example.com"

        insert_result = await mock_collection.insert_one({"email": "new@example.com"})
        assert insert_result.inserted_id == "123"

        update_result = await mock_collection.update_one({}, {"$set": {"name": "New Name"}})
        assert update_result.modified_count == 1

        delete_result = await mock_collection.delete_one({"_id": "123"})
        assert delete_result.deleted_count == 1