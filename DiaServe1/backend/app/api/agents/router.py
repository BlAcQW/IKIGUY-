"""
Agent API Routes

Endpoints for managing real estate agents and their profiles.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional, List, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.agent import (
    Agent,
    AgentCreate,
    AgentUpdate,
    AgentListResponse,
    AgentStats,
    AgentStatus,
    AgentSpecialization
)
from app.services.agent_service import AgentService
from app.core.database import get_database
from app.core.auth import get_current_user, get_organization_context

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("", response_model=Agent, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent_data: AgentCreate,
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_context: Dict[str, str] = Depends(get_organization_context)
):
    """
    Create a new agent profile.

    Args:
        agent_data: Agent creation data
        database: Database connection
        current_user: Current user from auth
        org_context: Organization context

    Returns:
        Created agent

    Raises:
        HTTPException: If email already exists
    """
    service = AgentService(database)
    organization_id = org_context["organization_id"]

    try:
        agent = await service.create_agent(organization_id, agent_data)
        return agent
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=AgentListResponse)
async def list_agents(
    status_filter: Optional[AgentStatus] = Query(None, alias="status", description="Filter by status"),
    specialization: Optional[AgentSpecialization] = Query(None, description="Filter by specialization"),
    search: Optional[str] = Query(None, description="Search in name or email"),
    limit: int = Query(50, ge=1, le=100, description="Page size"),
    offset: int = Query(0, ge=0, description="Page offset"),
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_context: Dict[str, str] = Depends(get_organization_context)
):
    """
    List agents with optional filters.

    Args:
        status_filter: Filter by status
        specialization: Filter by specialization
        search: Search query
        limit: Page size
        offset: Page offset
        database: Database connection
        current_user: Current user from auth
        org_context: Organization context

    Returns:
        Paginated list of agents
    """
    service = AgentService(database)
    organization_id = org_context["organization_id"]

    return await service.list_agents(
        organization_id=organization_id,
        status=status_filter,
        specialization=specialization,
        search=search,
        limit=limit,
        offset=offset
    )


@router.get("/{agent_id}", response_model=Agent)
async def get_agent(
    agent_id: str,
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_context: Dict[str, str] = Depends(get_organization_context)
):
    """
    Get agent by ID.

    Args:
        agent_id: Agent ID
        database: Database connection
        current_user: Current user from auth
        org_context: Organization context

    Returns:
        Agent details

    Raises:
        HTTPException: If agent not found
    """
    service = AgentService(database)
    organization_id = org_context["organization_id"]
    agent = await service.get_agent(agent_id, organization_id)

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found"
        )

    return agent


@router.put("/{agent_id}", response_model=Agent)
async def update_agent(
    agent_id: str,
    updates: AgentUpdate,
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_context: Dict[str, str] = Depends(get_organization_context)
):
    """
    Update agent profile.

    Args:
        agent_id: Agent ID
        updates: Fields to update
        database: Database connection
        current_user: Current user from auth
        org_context: Organization context

    Returns:
        Updated agent

    Raises:
        HTTPException: If agent not found
    """
    service = AgentService(database)
    organization_id = org_context["organization_id"]
    agent = await service.update_agent(agent_id, organization_id, updates)

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found"
        )

    return agent


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: str,
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_context: Dict[str, str] = Depends(get_organization_context)
):
    """
    Delete an agent (soft delete).

    Args:
        agent_id: Agent ID
        database: Database connection
        current_user: Current user from auth
        org_context: Organization context

    Raises:
        HTTPException: If agent not found
    """
    service = AgentService(database)
    organization_id = org_context["organization_id"]
    success = await service.delete_agent(agent_id, organization_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found"
        )


@router.get("/{agent_id}/stats", response_model=AgentStats)
async def get_agent_stats(
    agent_id: str,
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_context: Dict[str, str] = Depends(get_organization_context)
):
    """
    Get agent performance statistics.

    Args:
        agent_id: Agent ID
        database: Database connection
        current_user: Current user from auth
        org_context: Organization context

    Returns:
        Agent statistics

    Raises:
        HTTPException: If agent not found
    """
    service = AgentService(database)
    organization_id = org_context["organization_id"]
    stats = await service.get_agent_stats(agent_id, organization_id)

    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found"
        )

    return stats


@router.post("/{agent_id}/availability", response_model=dict)
async def check_agent_availability(
    agent_id: str,
    start_time: datetime = Query(..., description="Proposed booking start time"),
    duration_minutes: int = Query(30, ge=15, le=180, description="Duration in minutes"),
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_context: Dict[str, str] = Depends(get_organization_context)
):
    """
    Check if agent is available for a booking.

    Args:
        agent_id: Agent ID
        start_time: Proposed booking start time
        duration_minutes: Duration in minutes
        database: Database connection
        current_user: Current user from auth
        org_context: Organization context

    Returns:
        Availability status and reason

    Raises:
        HTTPException: If agent not found
    """
    service = AgentService(database)
    organization_id = org_context["organization_id"]
    is_available, reason = await service.is_agent_available(
        agent_id,
        organization_id,
        start_time,
        duration_minutes
    )

    return {
        "available": is_available,
        "reason": reason,
        "agent_id": agent_id,
        "start_time": start_time.isoformat(),
        "duration_minutes": duration_minutes
    }


@router.get("/available/search", response_model=List[Agent])
async def search_available_agents(
    start_time: datetime = Query(..., description="Proposed booking start time"),
    duration_minutes: int = Query(30, ge=15, le=180, description="Duration in minutes"),
    specialization: Optional[AgentSpecialization] = Query(None, description="Filter by specialization"),
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_context: Dict[str, str] = Depends(get_organization_context)
):
    """
    Find all agents available for a booking at the given time.

    Args:
        start_time: Proposed booking start time
        duration_minutes: Duration in minutes
        specialization: Filter by specialization
        database: Database connection
        current_user: Current user from auth
        org_context: Organization context

    Returns:
        List of available agents
    """
    service = AgentService(database)
    organization_id = org_context["organization_id"]
    agents = await service.get_available_agents(
        organization_id,
        start_time,
        duration_minutes,
        specialization
    )

    return agents


@router.post("/{agent_id}/update-metrics", response_model=Agent)
async def update_agent_metrics(
    agent_id: str,
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_context: Dict[str, str] = Depends(get_organization_context)
):
    """
    Refresh agent metrics from bookings data.

    Args:
        agent_id: Agent ID
        database: Database connection
        current_user: Current user from auth
        org_context: Organization context

    Returns:
        Updated agent

    Raises:
        HTTPException: If agent not found
    """
    service = AgentService(database)
    organization_id = org_context["organization_id"]
    agent = await service.update_agent_metrics(agent_id, organization_id)

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found"
        )

    return agent
