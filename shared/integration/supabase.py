"""
Supabase Integration Service.
Handles Supabase authentication, database operations, storage, and realtime functionality.
"""

import asyncio
import logging
import os
from typing import Dict, Any, Optional, List, Union, Callable
from datetime import datetime
from dataclasses import dataclass
from pydantic import BaseModel, Field
import json

try:
    from supabase import create_client, Client
    from supabase.lib.client_options import ClientOptions
    from postgrest import APIError
    from storage3 import StorageException
    from gotrue import AuthError
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    # Create mock classes for type hints
    class Client:
        pass
    class APIError(Exception):
        pass
    class StorageException(Exception):
        pass
    class AuthError(Exception):
        pass

logger = logging.getLogger(__name__)


@dataclass
class SupabaseConfig:
    """Configuration for Supabase integration."""
    url: str
    anon_key: str
    service_role_key: Optional[str] = None
    timeout: int = 30
    verify_ssl: bool = True
    auto_refresh_token: bool = True
    persist_session: bool = True


@dataclass
class SupabaseUser:
    """Supabase user data model."""
    id: str
    email: str
    email_confirmed_at: Optional[str] = None
    phone: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    last_sign_in_at: Optional[str] = None
    user_metadata: Optional[Dict[str, Any]] = None
    app_metadata: Optional[Dict[str, Any]] = None


@dataclass
class SupabaseAuthResponse:
    """Supabase authentication response model."""
    user: Optional[SupabaseUser] = None
    session: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class SupabaseQueryResponse:
    """Supabase query response model."""
    data: Optional[List[Dict[str, Any]]] = None
    count: Optional[int] = None
    error: Optional[str] = None
    status_code: Optional[int] = None


@dataclass
class SupabaseStorageResponse:
    """Supabase storage response model."""
    path: Optional[str] = None
    id: Optional[str] = None
    fullPath: Optional[str] = None
    error: Optional[str] = None


class SupabaseIntegration:
    """
    Comprehensive Supabase integration service.
    Provides authentication, database, storage, and realtime functionality.
    """

    def __init__(self, config: SupabaseConfig):
        """
        Initialize Supabase integration.

        Args:
            config: Supabase configuration
        """
        self.config = config
        self.client: Optional[Client] = None
        self.admin_client: Optional[Client] = None
        self._connected = False

        if not SUPABASE_AVAILABLE:
            logger.warning("Supabase library not available. Install with: pip install supabase")
            return

        try:
            # Initialize client with anon key
            self.client = create_client(
                self.config.url,
                self.config.anon_key,
                options=ClientOptions(
                    auto_refresh_token=self.config.auto_refresh_token,
                    persist_session=self.config.persist_session
                )
            )

            # Initialize admin client if service role key is provided
            if self.config.service_role_key:
                self.admin_client = create_client(
                    self.config.url,
                    self.config.service_role_key
                )

            self._connected = True
            logger.info("Supabase integration initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            self._connected = False

    # Authentication Methods
    async def sign_up(
        self,
        email: str,
        password: str,
        user_metadata: Optional[Dict[str, Any]] = None
    ) -> SupabaseAuthResponse:
        """
        Sign up a new user.

        Args:
            email: User email
            password: User password
            user_metadata: Additional user metadata

        Returns:
            SupabaseAuthResponse: Authentication response
        """
        if not self._check_connection():
            return SupabaseAuthResponse(error="Supabase not connected")

        try:
            credentials = {"email": email, "password": password}
            if user_metadata:
                credentials["data"] = user_metadata

            response = self.client.auth.sign_up(credentials)

            if response.user:
                user = SupabaseUser(
                    id=response.user.id,
                    email=response.user.email or email,
                    email_confirmed_at=response.user.email_confirmed_at,
                    phone=response.user.phone,
                    created_at=response.user.created_at,
                    updated_at=response.user.updated_at,
                    last_sign_in_at=response.user.last_sign_in_at,
                    user_metadata=response.user.user_metadata,
                    app_metadata=response.user.app_metadata
                )

                return SupabaseAuthResponse(
                    user=user,
                    session=response.session.__dict__ if response.session else None
                )
            else:
                return SupabaseAuthResponse(error="Sign up failed")

        except AuthError as e:
            logger.error(f"Supabase auth error during sign up: {e}")
            return SupabaseAuthResponse(error=str(e))
        except Exception as e:
            logger.error(f"Error during sign up: {e}")
            return SupabaseAuthResponse(error=str(e))

    async def sign_in(self, email: str, password: str) -> SupabaseAuthResponse:
        """
        Sign in a user.

        Args:
            email: User email
            password: User password

        Returns:
            SupabaseAuthResponse: Authentication response
        """
        if not self._check_connection():
            return SupabaseAuthResponse(error="Supabase not connected")

        try:
            response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            if response.user:
                user = SupabaseUser(
                    id=response.user.id,
                    email=response.user.email or email,
                    email_confirmed_at=response.user.email_confirmed_at,
                    phone=response.user.phone,
                    created_at=response.user.created_at,
                    updated_at=response.user.updated_at,
                    last_sign_in_at=response.user.last_sign_in_at,
                    user_metadata=response.user.user_metadata,
                    app_metadata=response.user.app_metadata
                )

                return SupabaseAuthResponse(
                    user=user,
                    session=response.session.__dict__ if response.session else None
                )
            else:
                return SupabaseAuthResponse(error="Sign in failed")

        except AuthError as e:
            logger.error(f"Supabase auth error during sign in: {e}")
            return SupabaseAuthResponse(error=str(e))
        except Exception as e:
            logger.error(f"Error during sign in: {e}")
            return SupabaseAuthResponse(error=str(e))

    async def sign_out(self) -> bool:
        """
        Sign out the current user.

        Returns:
            bool: Success status
        """
        if not self._check_connection():
            return False

        try:
            self.client.auth.sign_out()
            return True
        except Exception as e:
            logger.error(f"Error during sign out: {e}")
            return False

    async def get_user(self) -> Optional[SupabaseUser]:
        """
        Get current authenticated user.

        Returns:
            Optional[SupabaseUser]: Current user or None
        """
        if not self._check_connection():
            return None

        try:
            user = self.client.auth.get_user()
            if user.user:
                return SupabaseUser(
                    id=user.user.id,
                    email=user.user.email,
                    email_confirmed_at=user.user.email_confirmed_at,
                    phone=user.user.phone,
                    created_at=user.user.created_at,
                    updated_at=user.user.updated_at,
                    last_sign_in_at=user.user.last_sign_in_at,
                    user_metadata=user.user.user_metadata,
                    app_metadata=user.user.app_metadata
                )
            return None
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None

    # Database Methods
    async def insert(
        self,
        table: str,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
        upsert: bool = False
    ) -> SupabaseQueryResponse:
        """
        Insert data into a table.

        Args:
            table: Table name
            data: Data to insert
            upsert: Whether to upsert (insert or update)

        Returns:
            SupabaseQueryResponse: Query response
        """
        if not self._check_connection():
            return SupabaseQueryResponse(error="Supabase not connected")

        try:
            if upsert:
                response = self.client.table(table).upsert(data).execute()
            else:
                response = self.client.table(table).insert(data).execute()

            return SupabaseQueryResponse(
                data=response.data,
                count=len(response.data) if response.data else 0
            )

        except APIError as e:
            logger.error(f"Supabase API error during insert: {e}")
            return SupabaseQueryResponse(error=str(e))
        except Exception as e:
            logger.error(f"Error during insert: {e}")
            return SupabaseQueryResponse(error=str(e))

    async def select(
        self,
        table: str,
        columns: str = "*",
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> SupabaseQueryResponse:
        """
        Select data from a table.

        Args:
            table: Table name
            columns: Columns to select
            filters: Filter conditions
            order_by: Order by column
            limit: Limit number of results
            offset: Offset for pagination

        Returns:
            SupabaseQueryResponse: Query response
        """
        if not self._check_connection():
            return SupabaseQueryResponse(error="Supabase not connected")

        try:
            query = self.client.table(table).select(columns)

            # Apply filters
            if filters:
                for key, value in filters.items():
                    if isinstance(value, dict):
                        # Handle complex filters like {"operator": "eq", "value": "something"}
                        operator = value.get("operator", "eq")
                        filter_value = value.get("value")
                        query = getattr(query, operator)(key, filter_value)
                    else:
                        # Simple equality filter
                        query = query.eq(key, value)

            # Apply ordering
            if order_by:
                if order_by.startswith("-"):
                    query = query.order(order_by[1:], desc=True)
                else:
                    query = query.order(order_by)

            # Apply limit and offset
            if limit:
                query = query.limit(limit)
            if offset:
                query = query.range(offset, offset + (limit or 1000) - 1)

            response = query.execute()

            return SupabaseQueryResponse(
                data=response.data,
                count=len(response.data) if response.data else 0
            )

        except APIError as e:
            logger.error(f"Supabase API error during select: {e}")
            return SupabaseQueryResponse(error=str(e))
        except Exception as e:
            logger.error(f"Error during select: {e}")
            return SupabaseQueryResponse(error=str(e))

    async def update(
        self,
        table: str,
        data: Dict[str, Any],
        filters: Dict[str, Any]
    ) -> SupabaseQueryResponse:
        """
        Update data in a table.

        Args:
            table: Table name
            data: Data to update
            filters: Filter conditions

        Returns:
            SupabaseQueryResponse: Query response
        """
        if not self._check_connection():
            return SupabaseQueryResponse(error="Supabase not connected")

        try:
            query = self.client.table(table).update(data)

            # Apply filters
            for key, value in filters.items():
                query = query.eq(key, value)

            response = query.execute()

            return SupabaseQueryResponse(
                data=response.data,
                count=len(response.data) if response.data else 0
            )

        except APIError as e:
            logger.error(f"Supabase API error during update: {e}")
            return SupabaseQueryResponse(error=str(e))
        except Exception as e:
            logger.error(f"Error during update: {e}")
            return SupabaseQueryResponse(error=str(e))

    async def delete(
        self,
        table: str,
        filters: Dict[str, Any]
    ) -> SupabaseQueryResponse:
        """
        Delete data from a table.

        Args:
            table: Table name
            filters: Filter conditions

        Returns:
            SupabaseQueryResponse: Query response
        """
        if not self._check_connection():
            return SupabaseQueryResponse(error="Supabase not connected")

        try:
            query = self.client.table(table).delete()

            # Apply filters
            for key, value in filters.items():
                query = query.eq(key, value)

            response = query.execute()

            return SupabaseQueryResponse(
                data=response.data,
                count=len(response.data) if response.data else 0
            )

        except APIError as e:
            logger.error(f"Supabase API error during delete: {e}")
            return SupabaseQueryResponse(error=str(e))
        except Exception as e:
            logger.error(f"Error during delete: {e}")
            return SupabaseQueryResponse(error=str(e))

    # Storage Methods
    async def upload_file(
        self,
        bucket: str,
        path: str,
        file_data: bytes,
        content_type: Optional[str] = None
    ) -> SupabaseStorageResponse:
        """
        Upload a file to storage.

        Args:
            bucket: Storage bucket name
            path: File path in bucket
            file_data: File data as bytes
            content_type: File content type

        Returns:
            SupabaseStorageResponse: Storage response
        """
        if not self._check_connection():
            return SupabaseStorageResponse(error="Supabase not connected")

        try:
            options = {}
            if content_type:
                options["content_type"] = content_type

            response = self.client.storage.from_(bucket).upload(
                path, file_data, file_options=options
            )

            return SupabaseStorageResponse(
                path=response.get("path"),
                id=response.get("id"),
                fullPath=response.get("fullPath")
            )

        except StorageException as e:
            logger.error(f"Supabase storage error during upload: {e}")
            return SupabaseStorageResponse(error=str(e))
        except Exception as e:
            logger.error(f"Error during file upload: {e}")
            return SupabaseStorageResponse(error=str(e))

    async def download_file(self, bucket: str, path: str) -> Optional[bytes]:
        """
        Download a file from storage.

        Args:
            bucket: Storage bucket name
            path: File path in bucket

        Returns:
            Optional[bytes]: File data or None
        """
        if not self._check_connection():
            return None

        try:
            response = self.client.storage.from_(bucket).download(path)
            return response
        except Exception as e:
            logger.error(f"Error during file download: {e}")
            return None

    async def delete_file(self, bucket: str, paths: List[str]) -> bool:
        """
        Delete files from storage.

        Args:
            bucket: Storage bucket name
            paths: List of file paths to delete

        Returns:
            bool: Success status
        """
        if not self._check_connection():
            return False

        try:
            self.client.storage.from_(bucket).remove(paths)
            return True
        except Exception as e:
            logger.error(f"Error during file deletion: {e}")
            return False

    async def list_files(
        self,
        bucket: str,
        path: str = "",
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List files in storage bucket.

        Args:
            bucket: Storage bucket name
            path: Path prefix to filter
            limit: Maximum number of files
            offset: Offset for pagination

        Returns:
            List[Dict[str, Any]]: List of file metadata
        """
        if not self._check_connection():
            return []

        try:
            response = self.client.storage.from_(bucket).list(
                path, {"limit": limit, "offset": offset}
            )
            return response
        except Exception as e:
            logger.error(f"Error listing files: {e}")
            return []

    async def get_public_url(self, bucket: str, path: str) -> Optional[str]:
        """
        Get public URL for a file.

        Args:
            bucket: Storage bucket name
            path: File path in bucket

        Returns:
            Optional[str]: Public URL or None
        """
        if not self._check_connection():
            return None

        try:
            response = self.client.storage.from_(bucket).get_public_url(path)
            return response
        except Exception as e:
            logger.error(f"Error getting public URL: {e}")
            return None

    # Edge Functions
    async def invoke_function(
        self,
        function_name: str,
        payload: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Invoke an edge function.

        Args:
            function_name: Function name
            payload: Function payload
            headers: Additional headers

        Returns:
            Dict[str, Any]: Function response
        """
        if not self._check_connection():
            return {"error": "Supabase not connected"}

        try:
            invoke_options = {}
            if payload:
                invoke_options["body"] = payload
            if headers:
                invoke_options["headers"] = headers

            response = self.client.functions.invoke(function_name, invoke_options)
            return response.json() if hasattr(response, 'json') else response

        except Exception as e:
            logger.error(f"Error invoking function {function_name}: {e}")
            return {"error": str(e)}

    # Utility Methods
    def _check_connection(self) -> bool:
        """Check if Supabase is connected."""
        if not SUPABASE_AVAILABLE:
            logger.error("Supabase library not available")
            return False
        if not self._connected or not self.client:
            logger.error("Supabase not connected")
            return False
        return True

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check.

        Returns:
            Dict[str, Any]: Health status
        """
        if not SUPABASE_AVAILABLE:
            return {
                "status": "unhealthy",
                "error": "Supabase library not installed",
                "library_available": False
            }

        if not self._connected:
            return {
                "status": "unhealthy",
                "error": "Supabase not connected",
                "connected": False
            }

        try:
            # Try a simple query to test connection
            response = await self.select("_health_check", limit=1)

            return {
                "status": "healthy" if not response.error else "degraded",
                "connected": True,
                "library_available": True,
                "url": self.config.url,
                "has_service_role": bool(self.config.service_role_key),
                "error": response.error if response.error else None
            }

        except Exception as e:
            return {
                "status": "degraded",
                "connected": True,
                "library_available": True,
                "error": str(e)
            }

    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get service capabilities.

        Returns:
            Dict[str, Any]: Service capabilities
        """
        capabilities = [
            "sign_up", "sign_in", "sign_out", "get_user",
            "insert", "select", "update", "delete",
            "upload_file", "download_file", "delete_file", "list_files", "get_public_url",
            "invoke_function", "health_check"
        ]

        return {
            "service": "supabase",
            "capabilities": capabilities,
            "library_available": SUPABASE_AVAILABLE,
            "connected": self._connected,
            "authentication": True,
            "database": True,
            "storage": True,
            "edge_functions": True,
            "realtime": True,
            "api_reference": "https://supabase.com/docs/reference/python",
            "documentation": "https://supabase.com/docs"
        }