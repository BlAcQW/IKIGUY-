"""
Client library for Asterisk REST API
Use this in other Kasa AI apps to interact with Asterisk API
"""
import os
import logging
from typing import Optional, Dict, Any
import httpx

logger = logging.getLogger(__name__)


class AsteriskAPIClient:
    """
    Client for Asterisk REST API
    Used by Kasa AI apps to provision phone numbers and manage SIP peers
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: int = 30
    ):
        """
        Initialize Asterisk API client

        Args:
            base_url: Base URL for Asterisk API (default from env)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url or os.getenv(
            'ASTERISK_API_URL',
            'https://asterisk-api.ailabsafrica.com'
        )
        self.timeout = timeout
        logger.info(f"Asterisk API client initialized: {self.base_url}")

    async def health_check(self) -> Dict[str, Any]:
        """
        Check Asterisk API health

        Returns:
            Health status dict

        Raises:
            httpx.HTTPError: If request fails
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()

    async def create_sip_peer(
        self,
        number: str,
        sip_username: str,
        sip_password: str,
        webhook_url: str,
        context: str = "kasaai-virtual"
    ) -> Dict[str, Any]:
        """
        Create SIP peer in Asterisk

        Args:
            number: Phone number (E.164 format)
            sip_username: SIP username
            sip_password: SIP password
            webhook_url: Webhook URL for incoming calls
            context: Asterisk context

        Returns:
            Response dict with SIP credentials

        Raises:
            httpx.HTTPError: If request fails
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/sip/peer",
                json={
                    "number": number,
                    "sip_username": sip_username,
                    "sip_password": sip_password,
                    "webhook_url": webhook_url,
                    "context": context
                }
            )
            response.raise_for_status()
            result = response.json()
            logger.info(f"Created SIP peer for {number}")
            return result

    async def delete_sip_peer(
        self,
        number: str,
        sip_username: str
    ) -> Dict[str, Any]:
        """
        Delete SIP peer from Asterisk

        Args:
            number: Phone number
            sip_username: SIP username

        Returns:
            Response dict

        Raises:
            httpx.HTTPError: If request fails
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.request(
                "DELETE",
                f"{self.base_url}/sip/peer",
                json={
                    "number": number,
                    "sip_username": sip_username
                }
            )
            response.raise_for_status()
            result = response.json()
            logger.info(f"Deleted SIP peer for {number}")
            return result

    async def get_sip_peer(self, sip_username: str) -> Dict[str, Any]:
        """
        Get SIP peer information

        Args:
            sip_username: SIP username

        Returns:
            Peer information dict

        Raises:
            httpx.HTTPError: If request fails or peer not found
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/sip/peer/{sip_username}"
            )
            response.raise_for_status()
            return response.json()

    async def list_sip_peers(self) -> Dict[str, Any]:
        """
        List all SIP peers

        Returns:
            Dict with list of peer usernames

        Raises:
            httpx.HTTPError: If request fails
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/sip/peers")
            response.raise_for_status()
            return response.json()

    async def create_call_route(
        self,
        number: str,
        webhook_url: str
    ) -> Dict[str, Any]:
        """
        Create call routing rule

        Args:
            number: Phone number
            webhook_url: Webhook URL to invoke

        Returns:
            Response dict

        Raises:
            httpx.HTTPError: If request fails
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/call/route",
                json={
                    "number": number,
                    "webhook_url": webhook_url
                }
            )
            response.raise_for_status()
            result = response.json()
            logger.info(f"Created call route for {number}")
            return result

    async def get_asterisk_status(self) -> Dict[str, Any]:
        """
        Get Asterisk server status

        Returns:
            Status dict with uptime, channels, calls, etc.

        Raises:
            httpx.HTTPError: If request fails
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/asterisk/status")
            response.raise_for_status()
            return response.json()

    async def reload_pjsip(self) -> Dict[str, Any]:
        """
        Reload PJSIP configuration

        Returns:
            Response dict

        Raises:
            httpx.HTTPError: If request fails
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.base_url}/asterisk/reload")
            response.raise_for_status()
            result = response.json()
            logger.info("Reloaded PJSIP configuration")
            return result


# Example usage
async def example_usage():
    """Example of using the Asterisk API client"""
    client = AsteriskAPIClient()

    # Health check
    health = await client.health_check()
    print(f"Asterisk API health: {health}")

    # Create SIP peer
    result = await client.create_sip_peer(
        number="+12345678901",
        sip_username="kasaai_test_001",
        sip_password="secure_password_123",
        webhook_url="https://api.kasaai.ailabsafrica.com/voice/webhook/kasaai_test_001"
    )
    print(f"Created SIP peer: {result}")

    # Get peer info
    peer = await client.get_sip_peer("kasaai_test_001")
    print(f"Peer info: {peer}")

    # Delete peer
    result = await client.delete_sip_peer(
        number="+12345678901",
        sip_username="kasaai_test_001"
    )
    print(f"Deleted SIP peer: {result}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
