"""
ANT Cellular Gateway Management API

CRUD endpoints for managing cellular gateway devices.
"""

import logging
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from ...mongo import get_database
from ...models.ant_gateway import (
    ANTGateway,
    GatewayCreateRequest,
    GatewayUpdateRequest,
    GatewayStatusResponse,
    GatewayListResponse
)
from ...services.ant_gateway_service import ANTGatewayService


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ant-gateways", tags=["ant-gateways"])


def get_gateway_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> ANTGatewayService:
    """Get gateway service instance"""
    return ANTGatewayService(db)


@router.post("", response_model=ANTGateway)
async def create_gateway(
    request: GatewayCreateRequest,
    service: ANTGatewayService = Depends(get_gateway_service)
):
    """
    Create new ANT cellular gateway configuration.

    Args:
        request: Gateway creation request

    Returns:
        Created gateway configuration
    """
    try:
        gateway = await service.create_gateway(request)
        logger.info(f"Gateway created: {gateway.gateway_id}")
        return gateway

    except Exception as e:
        logger.error(f"Failed to create gateway: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[ANTGateway])
async def list_gateways(
    service: ANTGatewayService = Depends(get_gateway_service)
):
    """
    List all configured ANT gateways.

    Returns:
        List of gateway configurations
    """
    try:
        gateways = await service.list_gateways()
        return gateways

    except Exception as e:
        logger.error(f"Failed to list gateways: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=GatewayListResponse)
async def get_all_gateways_status(
    service: ANTGatewayService = Depends(get_gateway_service)
):
    """
    Get status of all ANT cellular gateways.

    This endpoint checks connectivity and SIM card status for all
    configured gateways.

    Returns:
        Combined status for all gateways
    """
    try:
        status = await service.get_all_status()
        return status

    except Exception as e:
        logger.error(f"Failed to get gateways status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{gateway_id}", response_model=ANTGateway)
async def get_gateway(
    gateway_id: str,
    service: ANTGatewayService = Depends(get_gateway_service)
):
    """
    Get gateway configuration by ID.

    Args:
        gateway_id: Gateway identifier

    Returns:
        Gateway configuration

    Raises:
        404 if gateway not found
    """
    gateway = await service.get_gateway(gateway_id)

    if not gateway:
        raise HTTPException(status_code=404, detail="Gateway not found")

    return gateway


@router.put("/{gateway_id}", response_model=ANTGateway)
async def update_gateway(
    gateway_id: str,
    request: GatewayUpdateRequest,
    service: ANTGatewayService = Depends(get_gateway_service)
):
    """
    Update gateway configuration.

    Args:
        gateway_id: Gateway identifier
        request: Update request

    Returns:
        Updated gateway configuration

    Raises:
        404 if gateway not found
    """
    gateway = await service.update_gateway(gateway_id, request)

    if not gateway:
        raise HTTPException(status_code=404, detail="Gateway not found")

    logger.info(f"Gateway updated: {gateway_id}")
    return gateway


@router.delete("/{gateway_id}")
async def delete_gateway(
    gateway_id: str,
    service: ANTGatewayService = Depends(get_gateway_service)
):
    """
    Delete gateway configuration.

    Args:
        gateway_id: Gateway identifier

    Returns:
        Success message

    Raises:
        404 if gateway not found
    """
    deleted = await service.delete_gateway(gateway_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Gateway not found")

    logger.info(f"Gateway deleted: {gateway_id}")
    return {"success": True, "message": "Gateway deleted"}


@router.get("/{gateway_id}/status", response_model=GatewayStatusResponse)
async def check_gateway_status(
    gateway_id: str,
    service: ANTGatewayService = Depends(get_gateway_service)
):
    """
    Check specific gateway status.

    This endpoint connects to the gateway device and retrieves
    current status including SIM card registrations.

    Args:
        gateway_id: Gateway identifier

    Returns:
        Gateway status including SIM cards
    """
    try:
        status = await service.check_gateway_status(gateway_id)
        return status

    except Exception as e:
        logger.error(f"Failed to check gateway status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
