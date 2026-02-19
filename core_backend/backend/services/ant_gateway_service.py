"""
ANT Cellular Gateway Service

Handles gateway management and status checking for various cellular gateway types.
"""

import logging
import asyncio
import aiohttp
from datetime import datetime
from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from ..models.ant_gateway import (
    ANTGateway,
    GatewayType,
    GatewayStatus,
    SIMCard,
    SIMStatus,
    GatewayCreateRequest,
    GatewayUpdateRequest,
    GatewayStatusResponse,
    GatewayListResponse
)


logger = logging.getLogger(__name__)


class GatewayAPIAdapter:
    """Base adapter for gateway API communication"""

    def __init__(self, gateway: ANTGateway):
        self.gateway = gateway
        self.base_url = self._build_base_url()

    def _build_base_url(self) -> str:
        """Build base URL for gateway API"""
        protocol = "https" if self.gateway.https else "http"
        return f"{protocol}://{self.gateway.ip_address}:{self.gateway.port}"

    async def get_status(self) -> Dict[str, Any]:
        """
        Get gateway status.

        Returns:
            Dict with status, sim_cards, etc.

        Raises:
            Exception if connection fails
        """
        raise NotImplementedError("Subclass must implement get_status")

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make HTTP request to gateway.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            **kwargs: Additional request parameters

        Returns:
            Response JSON

        Raises:
            Exception if request fails
        """
        url = f"{self.base_url}{endpoint}"

        auth = aiohttp.BasicAuth(
            self.gateway.credentials.username,
            self.gateway.credentials.password
        )

        timeout = aiohttp.ClientTimeout(total=10)

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.request(
                    method,
                    url,
                    auth=auth,
                    ssl=False,  # Many gateways use self-signed certs
                    **kwargs
                ) as response:
                    response.raise_for_status()
                    return await response.json()

        except aiohttp.ClientError as e:
            logger.error(f"Gateway API request failed: {e}")
            raise Exception(f"Connection failed: {str(e)}")


class GoIPAdapter(GatewayAPIAdapter):
    """Adapter for GoIP gateways"""

    async def get_status(self) -> Dict[str, Any]:
        """Get GoIP gateway status"""
        try:
            # GoIP API endpoint for status
            data = await self._make_request("GET", "/default/en_US/status.xml")

            # Parse GoIP XML response (simplified)
            sim_cards = []
            for i in range(1, self.gateway.total_sim_slots + 1):
                sim_cards.append(SIMCard(
                    slot=i,
                    phone_number=data.get(f"gsm{i}_number"),
                    network_provider=data.get(f"gsm{i}_operator"),
                    status=SIMStatus.REGISTERED if data.get(f"gsm{i}_status") == "registered" else SIMStatus.NOT_REGISTERED,
                    signal_strength=int(data.get(f"gsm{i}_signal", 0)),
                    network_type=data.get(f"gsm{i}_network_type")
                ))

            return {
                "status": GatewayStatus.ONLINE,
                "sim_cards": sim_cards,
                "firmware_version": data.get("firmware_version"),
                "hardware_version": data.get("hardware_version")
            }

        except Exception as e:
            logger.error(f"GoIP status check failed: {e}")
            raise


class DinstarAdapter(GatewayAPIAdapter):
    """Adapter for Dinstar gateways"""

    async def get_status(self) -> Dict[str, Any]:
        """Get Dinstar gateway status"""
        try:
            # Dinstar API endpoint
            data = await self._make_request("GET", "/api/status")

            sim_cards = []
            for i, sim_data in enumerate(data.get("sims", []), 1):
                sim_cards.append(SIMCard(
                    slot=i,
                    phone_number=sim_data.get("number"),
                    imsi=sim_data.get("imsi"),
                    network_provider=sim_data.get("operator"),
                    status=SIMStatus(sim_data.get("status", "unknown")),
                    signal_strength=int(sim_data.get("signal", 0)),
                    network_type=sim_data.get("network_type")
                ))

            return {
                "status": GatewayStatus.ONLINE,
                "sim_cards": sim_cards,
                "firmware_version": data.get("firmware"),
                "hardware_version": data.get("hardware")
            }

        except Exception as e:
            logger.error(f"Dinstar status check failed: {e}")
            raise


class GenericAdapter(GatewayAPIAdapter):
    """Generic adapter for unknown gateway types"""

    async def get_status(self) -> Dict[str, Any]:
        """
        Generic status check - just ping gateway.

        For generic gateways, we only check connectivity.
        User must manually configure SIM details.
        """
        try:
            # Just try to connect to gateway
            await self._make_request("GET", "/")

            # Return basic online status
            return {
                "status": GatewayStatus.ONLINE,
                "sim_cards": [],
                "firmware_version": None,
                "hardware_version": None
            }

        except Exception as e:
            logger.error(f"Generic gateway ping failed: {e}")
            raise


class ANTGatewayService:
    """Service for managing ANT cellular gateways"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.ant_gateways

    def _get_adapter(self, gateway: ANTGateway) -> GatewayAPIAdapter:
        """
        Get appropriate adapter for gateway type.

        Args:
            gateway: Gateway configuration

        Returns:
            API adapter instance
        """
        adapters = {
            GatewayType.GOIP: GoIPAdapter,
            GatewayType.DINSTAR: DinstarAdapter,
            GatewayType.GENERIC: GenericAdapter,
        }

        adapter_class = adapters.get(gateway.gateway_type, GenericAdapter)
        return adapter_class(gateway)

    async def create_gateway(self, request: GatewayCreateRequest) -> ANTGateway:
        """
        Create new gateway configuration.

        Args:
            request: Gateway creation request

        Returns:
            Created gateway

        Raises:
            Exception if creation fails
        """
        # Generate gateway ID
        gateway_id = f"ant_gateway_{ObjectId()}"

        # Create gateway object
        gateway = ANTGateway(
            gateway_id=gateway_id,
            name=request.name,
            gateway_type=request.gateway_type,
            ip_address=request.ip_address,
            port=request.port,
            https=request.https,
            credentials={
                "username": request.username,
                "password": request.password,
                "api_key": request.api_key
            },
            total_sim_slots=request.total_sim_slots,
            status=GatewayStatus.OFFLINE
        )

        # Save to database
        await self.collection.insert_one(gateway.dict())

        logger.info(f"Created gateway: {gateway_id}")
        return gateway

    async def get_gateway(self, gateway_id: str) -> Optional[ANTGateway]:
        """
        Get gateway by ID.

        Args:
            gateway_id: Gateway identifier

        Returns:
            Gateway or None if not found
        """
        data = await self.collection.find_one({"gateway_id": gateway_id})

        if data:
            data.pop("_id", None)
            return ANTGateway(**data)

        return None

    async def list_gateways(self) -> List[ANTGateway]:
        """
        List all configured gateways.

        Returns:
            List of gateways
        """
        cursor = self.collection.find()
        gateways = []

        async for data in cursor:
            data.pop("_id", None)
            gateways.append(ANTGateway(**data))

        return gateways

    async def update_gateway(
        self,
        gateway_id: str,
        request: GatewayUpdateRequest
    ) -> Optional[ANTGateway]:
        """
        Update gateway configuration.

        Args:
            gateway_id: Gateway identifier
            request: Update request

        Returns:
            Updated gateway or None if not found
        """
        # Build update dict
        update_data = {
            "updated_at": datetime.utcnow()
        }

        if request.name:
            update_data["name"] = request.name
        if request.ip_address:
            update_data["ip_address"] = request.ip_address
        if request.port:
            update_data["port"] = request.port
        if request.https is not None:
            update_data["https"] = request.https
        if request.username:
            update_data["credentials.username"] = request.username
        if request.password:
            update_data["credentials.password"] = request.password
        if request.api_key:
            update_data["credentials.api_key"] = request.api_key

        # Update in database
        result = await self.collection.update_one(
            {"gateway_id": gateway_id},
            {"$set": update_data}
        )

        if result.modified_count > 0:
            logger.info(f"Updated gateway: {gateway_id}")
            return await self.get_gateway(gateway_id)

        return None

    async def delete_gateway(self, gateway_id: str) -> bool:
        """
        Delete gateway configuration.

        Args:
            gateway_id: Gateway identifier

        Returns:
            True if deleted, False if not found
        """
        result = await self.collection.delete_one({"gateway_id": gateway_id})

        if result.deleted_count > 0:
            logger.info(f"Deleted gateway: {gateway_id}")
            return True

        return False

    async def check_gateway_status(self, gateway_id: str) -> GatewayStatusResponse:
        """
        Check gateway status and update database.

        Args:
            gateway_id: Gateway identifier

        Returns:
            Gateway status response
        """
        gateway = await self.get_gateway(gateway_id)

        if not gateway:
            return GatewayStatusResponse(
                success=False,
                gateway_id=gateway_id,
                name="Unknown",
                status=GatewayStatus.UNKNOWN,
                sim_cards=[],
                online_sims=0,
                registered_numbers=0,
                last_seen=None,
                error="Gateway not found"
            )

        try:
            # Get appropriate adapter and check status
            adapter = self._get_adapter(gateway)
            status_data = await adapter.get_status()

            # Update gateway in database
            update_data = {
                "status": status_data["status"],
                "sim_cards": [sim.dict() for sim in status_data["sim_cards"]],
                "last_seen": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            if status_data.get("firmware_version"):
                update_data["firmware_version"] = status_data["firmware_version"]
            if status_data.get("hardware_version"):
                update_data["hardware_version"] = status_data["hardware_version"]

            await self.collection.update_one(
                {"gateway_id": gateway_id},
                {"$set": update_data}
            )

            # Count registered SIMs
            online_sims = len(status_data["sim_cards"])
            registered_numbers = sum(
                1 for sim in status_data["sim_cards"]
                if sim.status == SIMStatus.REGISTERED
            )

            return GatewayStatusResponse(
                success=True,
                gateway_id=gateway_id,
                name=gateway.name,
                status=status_data["status"],
                sim_cards=status_data["sim_cards"],
                online_sims=online_sims,
                registered_numbers=registered_numbers,
                last_seen=datetime.utcnow()
            )

        except Exception as e:
            logger.error(f"Gateway status check failed for {gateway_id}: {e}")

            # Update gateway as offline
            await self.collection.update_one(
                {"gateway_id": gateway_id},
                {"$set": {
                    "status": GatewayStatus.OFFLINE,
                    "updated_at": datetime.utcnow()
                }}
            )

            return GatewayStatusResponse(
                success=False,
                gateway_id=gateway_id,
                name=gateway.name,
                status=GatewayStatus.OFFLINE,
                sim_cards=[],
                online_sims=0,
                registered_numbers=0,
                last_seen=gateway.last_seen,
                error=str(e)
            )

    async def get_all_status(self) -> GatewayListResponse:
        """
        Get status of all gateways.

        Returns:
            Combined status response
        """
        gateways = await self.list_gateways()

        # Check status for all gateways concurrently
        status_tasks = [
            self.check_gateway_status(gw.gateway_id)
            for gw in gateways
        ]

        if status_tasks:
            status_results = await asyncio.gather(*status_tasks, return_exceptions=True)
        else:
            status_results = []

        # Update gateways with latest status
        updated_gateways = []
        online_count = 0
        total_sims = 0
        registered_sims = 0

        for gateway in gateways:
            # Refresh from database to get latest status
            updated = await self.get_gateway(gateway.gateway_id)
            if updated:
                updated_gateways.append(updated)

                if updated.status == GatewayStatus.ONLINE:
                    online_count += 1

                total_sims += len(updated.sim_cards)
                registered_sims += sum(
                    1 for sim in updated.sim_cards
                    if sim.status == SIMStatus.REGISTERED
                )

        return GatewayListResponse(
            success=True,
            gateways=updated_gateways,
            total_gateways=len(updated_gateways),
            online_gateways=online_count,
            total_sims=total_sims,
            registered_sims=registered_sims
        )
