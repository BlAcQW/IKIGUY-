"""
Email Account Service.

Manages email account creation, deactivation, and management via iRedMail API.
"""

import logging
import httpx
import os
from typing import Dict, Optional, Tuple
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


class EmailAccountError(Exception):
    """Base exception for email account operations."""
    pass


class EmailAccountCreationError(EmailAccountError):
    """Email account creation failed."""
    pass


class EmailAccountDisableError(EmailAccountError):
    """Email account disable operation failed."""
    pass


class EmailAlreadyExistsError(EmailAccountError):
    """Email account already exists."""
    pass


class EmailAccountService:
    """
    Service for managing email accounts on iRedMail server.

    Communicates with custom iRedMail REST API to create, disable, and manage
    email accounts for employees.
    """

    def __init__(
        self,
        api_url: str = None,
        api_key: str = None,
        default_quota_mb: int = 512,
        max_retries: int = 3,
        timeout_seconds: int = 30
    ):
        """
        Initialize Email Account Service.

        Args:
            api_url: iRedMail API base URL
            api_key: API key for authentication
            default_quota_mb: Default mailbox quota in MB
            max_retries: Maximum retry attempts
            timeout_seconds: HTTP request timeout
        """
        self.api_url = api_url or os.getenv(
            "IREDMAIL_API_URL",
            "http://85.214.12.174:8100"  # Direct connection for now
        )
        self.api_key = api_key or os.getenv("IREDMAIL_API_KEY", "")
        self.default_quota_mb = default_quota_mb
        self.max_retries = max_retries
        self.timeout = timeout_seconds

        if not self.api_key:
            logger.warning("IREDMAIL_API_KEY not set - email account operations will fail")

    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers with API key."""
        return {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict] = None,
        retry_count: int = 0
    ) -> Tuple[int, Dict]:
        """
        Make HTTP request to iRedMail API with retry logic.

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE)
            endpoint: API endpoint (e.g., "/api/accounts")
            json_data: JSON payload for POST/PATCH requests
            retry_count: Current retry attempt

        Returns:
            Tuple of (status_code, response_data)

        Raises:
            EmailAccountError: If request fails after retries
        """
        url = f"{self.api_url}{endpoint}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    json=json_data,
                    headers=self._get_headers()
                )

                # Try to parse JSON response
                try:
                    response_data = response.json()
                except Exception:
                    response_data = {"detail": response.text}

                return response.status_code, response_data

        except (httpx.TimeoutException, httpx.ConnectError) as e:
            logger.warning(f"Request to {url} failed: {e}")

            # Retry with exponential backoff
            if retry_count < self.max_retries:
                wait_time = 2 ** retry_count  # 1s, 2s, 4s
                logger.info(f"Retrying in {wait_time}s... (attempt {retry_count + 1}/{self.max_retries})")
                await asyncio.sleep(wait_time)
                return await self._make_request(method, endpoint, json_data, retry_count + 1)
            else:
                raise EmailAccountError(f"Request failed after {self.max_retries} retries: {str(e)}")

        except Exception as e:
            logger.error(f"Unexpected error making request to {url}: {e}")
            raise EmailAccountError(f"Request failed: {str(e)}")

    async def generate_email(self, first_name: str, last_name: str) -> str:
        """
        Generate email address from names.

        Calls the API to generate email with duplicate handling.

        Args:
            first_name: First name
            last_name: Last name

        Returns:
            Generated email address

        Raises:
            EmailAccountError: If generation fails
        """
        try:
            status_code, response_data = await self._make_request(
                method="POST",
                endpoint="/api/accounts/generate-email",
                json_data={
                    "first_name": first_name,
                    "last_name": last_name
                }
            )

            if status_code == 200 and response_data.get("success"):
                email = response_data.get("email")
                logger.info(f"Generated email: {email}")
                return email
            else:
                error_detail = response_data.get("detail", "Unknown error")
                raise EmailAccountError(f"Email generation failed: {error_detail}")

        except EmailAccountError:
            raise
        except Exception as e:
            logger.error(f"Failed to generate email: {e}")
            raise EmailAccountError(f"Email generation failed: {str(e)}")

    async def create_account(
        self,
        first_name: str,
        last_name: str,
        email: Optional[str] = None,
        password: Optional[str] = None,
        quota_mb: Optional[int] = None,
        display_name: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Create a new email account.

        Args:
            first_name: Employee first name
            last_name: Employee last name
            email: Email address (or auto-generate if None)
            password: Password (or auto-generate if None)
            quota_mb: Mailbox quota in MB (default from config)
            display_name: Display name for the account

        Returns:
            Dict with:
                - email: Created email address
                - password: Temporary password (if auto-generated)
                - status: Creation status
                - message: Status message

        Raises:
            EmailAlreadyExistsError: If account already exists
            EmailAccountCreationError: If creation fails
        """
        quota_mb = quota_mb or self.default_quota_mb
        display_name = display_name or f"{first_name} {last_name}"

        try:
            # Prepare request data
            request_data = {
                "first_name": first_name,
                "last_name": last_name,
                "quota_mb": quota_mb,
                "display_name": display_name
            }

            if email:
                request_data["email"] = email
            if password:
                request_data["password"] = password

            # Make creation request
            status_code, response_data = await self._make_request(
                method="POST",
                endpoint="/api/accounts",
                json_data=request_data
            )

            # Handle response
            if status_code == 200:
                logger.info(f"Successfully created email account: {response_data.get('email')}")
                return {
                    "email": response_data.get("email"),
                    "password": response_data.get("password"),  # Only returned on creation
                    "status": "created",
                    "message": "Email account created successfully",
                    "created_at": datetime.utcnow().isoformat()
                }
            elif status_code == 409:
                # Account already exists
                raise EmailAlreadyExistsError(
                    f"Email account already exists: {response_data.get('detail', 'unknown email')}"
                )
            else:
                error_detail = response_data.get("detail", "Unknown error")
                raise EmailAccountCreationError(f"Account creation failed: {error_detail}")

        except EmailAlreadyExistsError:
            raise
        except EmailAccountCreationError:
            raise
        except Exception as e:
            logger.error(f"Failed to create email account: {e}")
            raise EmailAccountCreationError(f"Account creation failed: {str(e)}")

    async def disable_account(self, email: str) -> Dict[str, any]:
        """
        Disable an email account (suspend without deleting data).

        Args:
            email: Email address to disable

        Returns:
            Dict with operation result

        Raises:
            EmailAccountDisableError: If operation fails
        """
        try:
            status_code, response_data = await self._make_request(
                method="PATCH",
                endpoint=f"/api/accounts/{email}/disable"
            )

            if status_code == 200:
                logger.info(f"Successfully disabled email account: {email}")
                return {
                    "email": email,
                    "status": "disabled",
                    "message": "Email account disabled successfully",
                    "disabled_at": datetime.utcnow().isoformat()
                }
            elif status_code == 404:
                raise EmailAccountDisableError(f"Email account not found: {email}")
            else:
                error_detail = response_data.get("detail", "Unknown error")
                raise EmailAccountDisableError(f"Account disable failed: {error_detail}")

        except EmailAccountDisableError:
            raise
        except Exception as e:
            logger.error(f"Failed to disable email account: {e}")
            raise EmailAccountDisableError(f"Account disable failed: {str(e)}")

    async def enable_account(self, email: str) -> Dict[str, any]:
        """
        Enable a disabled email account.

        Args:
            email: Email address to enable

        Returns:
            Dict with operation result

        Raises:
            EmailAccountError: If operation fails
        """
        try:
            status_code, response_data = await self._make_request(
                method="PATCH",
                endpoint=f"/api/accounts/{email}/enable"
            )

            if status_code == 200:
                logger.info(f"Successfully enabled email account: {email}")
                return {
                    "email": email,
                    "status": "enabled",
                    "message": response_data.get("message", "Email account enabled successfully"),
                    "enabled_at": datetime.utcnow().isoformat()
                }
            elif status_code == 404:
                raise EmailAccountError(f"Email account not found: {email}")
            else:
                error_detail = response_data.get("detail", "Unknown error")
                raise EmailAccountError(f"Account enable failed: {error_detail}")

        except EmailAccountError:
            raise
        except Exception as e:
            logger.error(f"Failed to enable email account: {e}")
            raise EmailAccountError(f"Account enable failed: {str(e)}")

    async def check_exists(self, email: str) -> bool:
        """
        Check if an email account exists.

        Args:
            email: Email address to check

        Returns:
            True if account exists, False otherwise
        """
        try:
            status_code, response_data = await self._make_request(
                method="GET",
                endpoint=f"/api/accounts/{email}"
            )

            if status_code == 200:
                return response_data.get("status") == "exists"
            return False

        except Exception as e:
            logger.error(f"Failed to check account existence: {e}")
            return False


# Singleton instance
_email_account_service: Optional[EmailAccountService] = None


def get_email_account_service() -> EmailAccountService:
    """
    Get singleton instance of EmailAccountService.

    Returns:
        EmailAccountService instance
    """
    global _email_account_service
    if _email_account_service is None:
        _email_account_service = EmailAccountService()
    return _email_account_service
