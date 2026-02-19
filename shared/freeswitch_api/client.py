"""
FreeSWITCH API Client for KasaAI
Communicates with FreeSWITCH REST API for dynamic user provisioning.
"""

import logging
from typing import Dict, Any, Optional
import aiohttp

logger = logging.getLogger(__name__)


class FreeSWITCHAPIClient:
    """
    Client for communicating with FreeSWITCH REST API.

    This client provides methods to create, update, delete, and check
    SIP users dynamically without needing to restart FreeSWITCH.
    """

    def __init__(self, base_url: str = "http://localhost:30040"):
        """
        Initialize FreeSWITCH API client.

        Args:
            base_url: Base URL for FreeSWITCH REST API.
        """
        self.base_url = base_url.rstrip("/")
        self.session: Optional[aiohttp.ClientSession] = None
        logger.info(f"FreeSWITCH API client initialized: {self.base_url}")

    async def _get_session(self) -> aiohttp.ClientSession:
        """
        Get or create HTTP session.

        Returns:
            aiohttp.ClientSession: HTTP session.
        """
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        """Close HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None

    async def create_sip_peer(
        self,
        number: str,
        sip_username: str,
        sip_password: str,
        webhook_url: Optional[str] = None,
        context: str = "kasaai-inbound"
    ) -> Dict[str, Any]:
        """
        Create SIP peer in FreeSWITCH.

        Args:
            number: Phone number to associate with user.
            sip_username: SIP username.
            sip_password: SIP password.
            webhook_url: Optional webhook URL for call events.
            context: Dialplan context (default: kasaai-inbound).

        Returns:
            dict: Response with success status and credentials.
        """
        try:
            session = await self._get_session()

            payload = {
                "username": sip_username,
                "password": sip_password,
                "phone_number": number,
                "context": context
            }

            async with session.post(
                f"{self.base_url}/users",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Successfully created SIP peer: {sip_username}")

                    return {
                        "success": True,
                        "message": "SIP peer created successfully",
                        "sip_credentials": {
                            "username": data["username"],
                            "phone_number": data["phone_number"],
                            "domain": "asterisk.ailabsafrica.com",
                            "port": 5060,
                            "transport": "UDP",
                            "context": data["context"]
                        }
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to create SIP peer: {response.status} - {error_text}")
                    return {
                        "success": False,
                        "message": f"Failed to create SIP peer: {error_text}"
                    }

        except aiohttp.ClientError as e:
            logger.error(f"Network error creating SIP peer: {e}")
            return {
                "success": False,
                "message": f"Network error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error creating SIP peer: {e}")
            return {
                "success": False,
                "message": f"Unexpected error: {str(e)}"
            }

    async def delete_sip_peer(
        self,
        number: str,
        sip_username: str
    ) -> Dict[str, Any]:
        """
        Delete SIP peer from FreeSWITCH.

        Args:
            number: Phone number.
            sip_username: SIP username to delete.

        Returns:
            dict: Response with success status.
        """
        try:
            session = await self._get_session()

            async with session.delete(
                f"{self.base_url}/users/{sip_username}",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    logger.info(f"Successfully deleted SIP peer: {sip_username}")
                    return {
                        "success": True,
                        "message": "SIP peer deleted successfully"
                    }
                elif response.status == 404:
                    logger.warning(f"SIP peer not found: {sip_username}")
                    return {
                        "success": True,
                        "message": "SIP peer not found (already deleted)"
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to delete SIP peer: {response.status} - {error_text}")
                    return {
                        "success": False,
                        "message": f"Failed to delete SIP peer: {error_text}"
                    }

        except aiohttp.ClientError as e:
            logger.error(f"Network error deleting SIP peer: {e}")
            return {
                "success": False,
                "message": f"Network error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error deleting SIP peer: {e}")
            return {
                "success": False,
                "message": f"Unexpected error: {str(e)}"
            }

    async def get_sip_peer_status(self, sip_username: str) -> Dict[str, Any]:
        """
        Get SIP peer registration status.

        Args:
            sip_username: SIP username to check.

        Returns:
            dict: Peer status information.
        """
        try:
            session = await self._get_session()

            async with session.get(
                f"{self.base_url}/users/{sip_username}",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Got status for SIP peer: {sip_username}")

                    return {
                        "username": data["username"],
                        "phone_number": data["phone_number"],
                        "registration_status": data["registration_status"],
                        "ip_address": None,  # FreeSWITCH API doesn't return IP yet
                        "user_agent": None,
                        "last_registration": data.get("updated_at")
                    }
                elif response.status == 404:
                    logger.warning(f"SIP peer not found: {sip_username}")
                    raise Exception("Peer not found")
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to get SIP peer status: {response.status} - {error_text}")
                    raise Exception(f"Failed to get status: {error_text}")

        except aiohttp.ClientError as e:
            logger.error(f"Network error getting SIP peer status: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting SIP peer status: {e}")
            raise

    async def update_sip_peer(
        self,
        sip_username: str,
        password: Optional[str] = None,
        enabled: Optional[bool] = None,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update SIP peer configuration.

        Args:
            sip_username: SIP username to update.
            password: New password (optional).
            enabled: Enable/disable user (optional).
            context: New dialplan context (optional).

        Returns:
            dict: Response with success status.
        """
        try:
            session = await self._get_session()

            payload = {}
            if password is not None:
                payload["password"] = password
            if enabled is not None:
                payload["enabled"] = enabled
            if context is not None:
                payload["context"] = context

            if not payload:
                return {
                    "success": True,
                    "message": "No updates provided"
                }

            async with session.patch(
                f"{self.base_url}/users/{sip_username}",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    logger.info(f"Successfully updated SIP peer: {sip_username}")
                    return {
                        "success": True,
                        "message": "SIP peer updated successfully"
                    }
                elif response.status == 404:
                    logger.warning(f"SIP peer not found: {sip_username}")
                    return {
                        "success": False,
                        "message": "SIP peer not found"
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to update SIP peer: {response.status} - {error_text}")
                    return {
                        "success": False,
                        "message": f"Failed to update SIP peer: {error_text}"
                    }

        except aiohttp.ClientError as e:
            logger.error(f"Network error updating SIP peer: {e}")
            return {
                "success": False,
                "message": f"Network error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error updating SIP peer: {e}")
            return {
                "success": False,
                "message": f"Unexpected error: {str(e)}"
            }

    async def health_check(self) -> Dict[str, Any]:
        """
        Check FreeSWITCH API health.

        Returns:
            dict: Health status.
        """
        try:
            session = await self._get_session()

            async with session.get(
                f"{self.base_url}/health",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "success": True,
                        "status": "healthy",
                        "details": data
                    }
                else:
                    return {
                        "success": False,
                        "status": "unhealthy",
                        "message": f"HTTP {response.status}"
                    }

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "success": False,
                "status": "unhealthy",
                "message": str(e)
            }
