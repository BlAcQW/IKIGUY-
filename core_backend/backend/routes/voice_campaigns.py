"""
Voice Campaign Routes

This module provides API endpoints for voice campaign management,
including database connections, audience filtering, VAPI integration,
and automated follow-up with emails and calendly booking.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import asyncio
import logging
from datetime import datetime, timezone
import json
import uuid
from ..auth import get_current_user_mongo
from ..middleware.organization_context import (
    get_organization_context,
    validate_organization_access
)
from ..mongo import get_collection
import os
import httpx
import asyncpg
import aiomysql
import sqlite3
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import sys

# Add shared services to path
sys.path.insert(0, "/opt/kasaai/apps")

logger = logging.getLogger(__name__)

# Import Slack notifier for failure notifications
try:
    from shared.services.slack_notifier import get_slack_notifier  # type: ignore[import]
    SLACK_NOTIFICATIONS_ENABLED = True
except ImportError:
    SLACK_NOTIFICATIONS_ENABLED = False
    logger.warning("Slack notifier not available - notifications disabled")

router = APIRouter(prefix="/campaigns", tags=["Voice Campaigns"])

# Pydantic Models
class DatabaseConnection(BaseModel):
    id: Optional[str] = None
    name: str
    type: str = Field(..., pattern="^(mysql|postgresql|sqlite)$")
    host: str
    port: int = 5432
    database: str
    username: str
    password: str
    ssl_enabled: bool = False

class FilterCondition(BaseModel):
    field: str
    operator: str = Field(..., pattern="^(equals|not_equals|greater_than|less_than|contains|is_null|is_not_null)$")
    value: str = ""

class VoiceCampaignRequest(BaseModel):
    name: str
    description: str = ""
    campaign_type: str
    voice_agent_id: str
    
    # Audience Configuration
    audience_type: str = Field(..., pattern="^(predefined|database)$")
    predefined_audience_id: Optional[str] = None
    database_connection_id: Optional[str] = None
    selected_table: Optional[str] = None
    filter_conditions: List[FilterCondition] = []
    
    # Call Configuration
    max_concurrent_calls: int = Field(default=3, ge=1, le=5)
    call_schedule: str = Field(..., pattern="^(immediate|scheduled)$")
    scheduled_date: Optional[str] = None
    scheduled_time: Optional[str] = None
    
    # Follow-up Configuration
    enable_email_summaries: bool = True
    email_template: str = ""
    enable_calendly_booking: bool = False
    calendly_settings: Dict[str, str] = {}

class CallRecord(BaseModel):
    campaign_id: str
    contact_id: str
    phone_number: str
    vapi_call_id: Optional[str] = None
    status: str = "pending"  # pending, calling, completed, failed
    transcript: str = ""
    summary: str = ""
    duration: int = 0
    cost: float = 0.0
    created_at: str
    completed_at: Optional[str] = None


@router.post("/database-connections")
async def create_database_connection(
    request: Request,
    connection: DatabaseConnection,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Create a new database connection for audience selection.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        # Test the connection first
        connection_valid = await test_database_connection(connection)
        if not connection_valid:
            raise HTTPException(status_code=400, detail="Database connection test failed")

        connections_collection = get_collection("database_connections")

        connection_data = connection.dict()
        connection_data["id"] = str(uuid.uuid4())

        # Use organization_id with tenant_id fallback for backward compatibility
        organization_id = org_id or current_user.get("organization_id") or current_user.get("tenant_id", "default")
        connection_data["organization_id"] = organization_id
        connection_data["created_by"] = current_user.get("sub")
        connection_data["created_at"] = datetime.utcnow().isoformat()

        logger.info(f"Creating database connection for organization: {organization_id}")

        # Encrypt password in production
        # connection_data["password"] = encrypt_password(connection.password)

        await connections_collection.insert_one(connection_data)

        return {
            "success": True,
            "connection_id": connection_data["id"],
            "message": "Database connection created successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating database connection: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create database connection")


@router.get("/database-connections")
async def list_database_connections(
    request: Request,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    List all database connections for the current organization.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        connections_collection = get_collection("database_connections")

        # Use organization_id with tenant_id fallback for backward compatibility
        organization_id = org_id or current_user.get("organization_id") or current_user.get("tenant_id", "default")

        # Query with both organization_id and tenant_id for backward compatibility
        query = {
            "$or": [
                {"organization_id": organization_id},
                {"tenant_id": organization_id}
            ]
        }

        logger.info(f"Listing database connections for organization: {organization_id}")

        cursor = connections_collection.find(
            query,
            {"password": 0}  # Don't return passwords
        )
        connections = await cursor.to_list(length=None)

        # Convert MongoDB _id to string
        for conn in connections:
            conn["_id"] = str(conn["_id"])

        return {
            "success": True,
            "connections": connections
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing database connections: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list database connections")


@router.get("/database-tables/{connection_id}")
async def get_database_tables(
    request: Request,
    connection_id: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get list of tables from a database connection.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        # Use organization_id with tenant_id fallback for backward compatibility
        organization_id = org_id or current_user.get("organization_id") or current_user.get("tenant_id", "default")

        logger.info(f"Fetching database tables for organization: {organization_id}, connection: {connection_id}")

        connection = await get_database_connection(connection_id, organization_id)
        if not connection:
            raise HTTPException(status_code=404, detail="Database connection not found")

        tables = await fetch_database_tables(connection)

        return {
            "success": True,
            "tables": tables
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching database tables: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch database tables")


@router.get("/table-columns/{connection_id}/{table_name}")
async def get_table_columns(
    request: Request,
    connection_id: str,
    table_name: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get column information for a specific table.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        # Use organization_id with tenant_id fallback for backward compatibility
        organization_id = org_id or current_user.get("organization_id") or current_user.get("tenant_id", "default")

        logger.info(f"Fetching table columns for organization: {organization_id}, connection: {connection_id}, table: {table_name}")

        connection = await get_database_connection(connection_id, organization_id)
        if not connection:
            raise HTTPException(status_code=404, detail="Database connection not found")

        columns = await fetch_table_columns(connection, table_name)

        return {
            "success": True,
            "columns": columns
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching table columns: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch table columns")


@router.post("/voice-campaigns")
async def create_voice_campaign(
    request: Request,
    campaign_request: VoiceCampaignRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Create a new voice campaign with VAPI integration.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        campaigns_collection = get_collection("voice_campaigns")

        # Generate campaign ID
        campaign_id = str(uuid.uuid4())

        # Use organization_id with tenant_id fallback for backward compatibility
        organization_id = org_id or current_user.get("organization_id") or current_user.get("tenant_id", "default")

        logger.info(f"Creating voice campaign for organization: {organization_id}")

        # Create campaign record
        campaign_data = {
            "id": campaign_id,
            "organization_id": organization_id,
            "created_by": current_user.get("sub"),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "status": "created",
            **campaign_request.dict()
        }

        await campaigns_collection.insert_one(campaign_data)

        # Process audience and create call queue
        background_tasks.add_task(
            process_campaign_audience,
            campaign_id,
            campaign_request,
            organization_id
        )

        # Schedule campaign execution
        if campaign_request.call_schedule == "immediate":
            background_tasks.add_task(start_campaign_execution, campaign_id)
        else:
            # Schedule for later - would use a job scheduler like Celery in production
            background_tasks.add_task(
                schedule_campaign_execution,
                campaign_id,
                campaign_request.scheduled_date,
                campaign_request.scheduled_time
            )

        return {
            "success": True,
            "campaign_id": campaign_id,
            "status": "created",
            "message": "Voice campaign created successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating voice campaign: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create voice campaign")


@router.get("/voice-campaigns")
async def list_voice_campaigns(
    request: Request,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    List all voice campaigns for the current organization.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        campaigns_collection = get_collection("voice_campaigns")

        # Use organization_id with tenant_id fallback for backward compatibility
        organization_id = org_id or current_user.get("organization_id") or current_user.get("tenant_id", "default")

        # Query with both organization_id and tenant_id for backward compatibility
        query = {
            "$or": [
                {"organization_id": organization_id},
                {"tenant_id": organization_id}
            ]
        }

        logger.info(f"Listing voice campaigns for organization: {organization_id}")

        cursor = campaigns_collection.find(
            query,
            {"_id": 0}
        ).sort("created_at", -1)
        campaigns = await cursor.to_list(length=None)

        return {
            "success": True,
            "campaigns": campaigns
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing voice campaigns: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list voice campaigns")


@router.get("/voice-campaigns/{campaign_id}")
async def get_voice_campaign(
    request: Request,
    campaign_id: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get detailed information about a voice campaign.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        campaigns_collection = get_collection("voice_campaigns")
        calls_collection = get_collection("campaign_calls")

        # Use organization_id with tenant_id fallback for backward compatibility
        organization_id = org_id or current_user.get("organization_id") or current_user.get("tenant_id", "default")

        # Get campaign data with organization validation
        query = {
            "id": campaign_id,
            "$or": [
                {"organization_id": organization_id},
                {"tenant_id": organization_id}
            ]
        }

        logger.info(f"Fetching voice campaign {campaign_id} for organization: {organization_id}")

        campaign = campaigns_collection.find_one(query, {"_id": 0})

        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        # Get call statistics with both VAPI and phone costs
        cursor = calls_collection.aggregate([
            {"$match": {"campaign_id": campaign_id}},
            {"$group": {
                "_id": "$status",
                "count": {"$sum": 1},
                "total_duration": {"$sum": "$duration"},
                "total_vapi_cost_usd": {"$sum": "$cost"}
            }}
        ])
        call_stats = await cursor.to_list(length=None)

        # Calculate phone costs for statistics
        phone_cost_per_minute = 0.15  # Default GHC rate
        if campaign.get("phone_id"):
            try:
                from backend.services.phone_management_service import get_phone_manager
                phone_manager = get_phone_manager()
                phone = phone_manager.get_phone(campaign["phone_id"])
                if phone:
                    phone_cost_per_minute = phone.cost_per_minute
            except Exception as e:
                logger.warning(f"Could not get phone rate, using default: {e}")

        # Add phone costs to statistics
        for stat in call_stats:
            duration_minutes = stat.get("total_duration", 0) / 60.0
            stat["total_phone_cost_ghc"] = duration_minutes * phone_cost_per_minute
            stat["total_cost"] = stat.get("total_vapi_cost_usd", 0) + stat["total_phone_cost_ghc"]

        campaign["call_statistics"] = call_stats

        return {
            "success": True,
            "campaign": campaign
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching voice campaign: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch voice campaign")


@router.post("/webhook/vapi/{campaign_id}")
async def handle_vapi_webhook(
    campaign_id: str,
    webhook_data: dict,
    background_tasks: BackgroundTasks
):
    """
    Handle VAPI webhook callbacks for campaign calls.

    Webhook endpoint - organization context tracked via campaign metadata.
    """
    try:
        # Extract organization from webhook metadata
        metadata = webhook_data.get("metadata", {})
        org_id = metadata.get("organization_id")

        logger.info(f"Received VAPI webhook for campaign {campaign_id}, organization: {org_id}")
        logger.debug(f"Webhook data: {webhook_data}")

        # Process webhook data
        call_id = webhook_data.get("call", {}).get("id")
        event_type = webhook_data.get("message", {}).get("type")

        if event_type == "status-update":
            background_tasks.add_task(
                process_call_status_update,
                campaign_id,
                call_id,
                webhook_data
            )
        elif event_type == "transcript":
            background_tasks.add_task(
                process_call_transcript,
                campaign_id,
                call_id,
                webhook_data
            )
        elif event_type == "end-of-call-report":
            background_tasks.add_task(
                process_call_completion,
                campaign_id,
                call_id,
                webhook_data
            )

        return {"success": True, "message": "Webhook processed"}

    except Exception as e:
        logger.error(f"Error processing VAPI webhook: {str(e)}")
        return {"success": False, "error": str(e)}


# Helper Functions

async def test_database_connection(connection: DatabaseConnection) -> bool:
    """Test if database connection is valid."""
    try:
        if connection.type == "postgresql":
            conn = await asyncpg.connect(
                host=connection.host,
                port=connection.port,
                database=connection.database,
                user=connection.username,
                password=connection.password
            )
            await conn.close()
            return True
            
        elif connection.type == "mysql":
            conn = await aiomysql.connect(
                host=connection.host,
                port=connection.port,
                db=connection.database,
                user=connection.username,
                password=connection.password
            )
            conn.close()
            return True
            
        elif connection.type == "sqlite":
            # SQLite doesn't require network connection testing
            return True
            
        return False
        
    except Exception as e:
        logger.error(f"Database connection test failed: {str(e)}")
        return False


async def get_database_connection(connection_id: str, organization_id: str) -> Optional[Dict[str, Any]]:
    """
    Get database connection by ID.

    Args:
        connection_id: The database connection ID
        organization_id: The organization ID (supports both organization_id and tenant_id for backward compatibility)

    Returns:
        Database connection dictionary or None
    """
    connections_collection = get_collection("database_connections")
    # Query with both organization_id and tenant_id for backward compatibility
    return connections_collection.find_one({
        "id": connection_id,
        "$or": [
            {"organization_id": organization_id},
            {"tenant_id": organization_id}
        ]
    })


async def fetch_database_tables(connection: Dict[str, Any]) -> List[str]:
    """Fetch list of tables from database connection."""
    try:
        if connection["type"] == "postgresql":
            conn = await asyncpg.connect(
                host=connection["host"],
                port=connection["port"],
                database=connection["database"],
                user=connection["username"],
                password=connection["password"]
            )
            
            tables = await conn.fetch(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            )
            await conn.close()
            
            return [table["table_name"] for table in tables]
            
        elif connection["type"] == "mysql":
            conn = await aiomysql.connect(
                host=connection["host"],
                port=connection["port"],
                db=connection["database"],
                user=connection["username"],
                password=connection["password"]
            )
            
            cursor = await conn.cursor()
            await cursor.execute("SHOW TABLES")
            tables = await cursor.fetchall()
            await cursor.close()
            conn.close()
            
            return [table[0] for table in tables]
            
        return []
        
    except Exception as e:
        logger.error(f"Error fetching database tables: {str(e)}")
        return []


async def fetch_table_columns(connection: Dict[str, Any], table_name: str) -> List[Dict[str, Any]]:
    """Fetch column information for a specific table."""
    try:
        if connection["type"] == "postgresql":
            conn = await asyncpg.connect(
                host=connection["host"],
                port=connection["port"],
                database=connection["database"],
                user=connection["username"],
                password=connection["password"]
            )
            
            columns = await conn.fetch("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = $1 AND table_schema = 'public'
            """, table_name)
            await conn.close()
            
            return [
                {
                    "name": col["column_name"],
                    "type": col["data_type"],
                    "nullable": col["is_nullable"] == "YES"
                }
                for col in columns
            ]
            
        elif connection["type"] == "mysql":
            conn = await aiomysql.connect(
                host=connection["host"],
                port=connection["port"],
                db=connection["database"],
                user=connection["username"],
                password=connection["password"]
            )
            
            cursor = await conn.cursor()
            await cursor.execute(f"DESCRIBE {table_name}")
            columns = await cursor.fetchall()
            await cursor.close()
            conn.close()
            
            return [
                {
                    "name": col[0],
                    "type": col[1],
                    "nullable": col[2] == "YES"
                }
                for col in columns
            ]
            
        return []
        
    except Exception as e:
        logger.error(f"Error fetching table columns: {str(e)}")
        return []


async def process_campaign_audience(
    campaign_id: str,
    campaign_request: VoiceCampaignRequest,
    organization_id: str
):
    """
    Process campaign audience and create call queue.

    Args:
        campaign_id: The voice campaign ID
        campaign_request: Campaign configuration
        organization_id: The organization ID
    """
    try:
        calls_collection = get_collection("campaign_calls")

        contacts = []

        if campaign_request.audience_type == "predefined":
            # Load predefined audience
            contacts = await load_predefined_audience(campaign_request.predefined_audience_id, organization_id)
        else:
            # Query database with filters
            contacts = await query_database_audience(
                campaign_request.database_connection_id,
                campaign_request.selected_table,
                campaign_request.filter_conditions,
                organization_id
            )
        
        # Create call records
        call_records = []
        for contact in contacts:
            call_record = {
                "id": str(uuid.uuid4()),
                "campaign_id": campaign_id,
                "contact_id": contact.get("id", str(uuid.uuid4())),
                "phone_number": contact.get("phone", contact.get("phone_number", "")),
                "contact_name": contact.get("name", ""),
                "contact_data": contact,
                "status": "pending",
                "created_at": datetime.utcnow().isoformat(),
                "attempts": 0
            }
            call_records.append(call_record)
        
        if call_records:
            await calls_collection.insert_many(call_records)
        
        # Update campaign with audience size
        campaigns_collection = get_collection("voice_campaigns")
        await campaigns_collection.update_one(
            {"id": campaign_id},
            {
                "$set": {
                    "audience_size": len(call_records),
                    "status": "ready",
                    "updated_at": datetime.utcnow().isoformat()
                }
            }
        )
        
        logger.info(f"Processed audience for campaign {campaign_id}: {len(call_records)} contacts")
        
    except Exception as e:
        logger.error(f"Error processing campaign audience: {str(e)}")

        # Get campaign details for notification
        campaigns_collection = get_collection("voice_campaigns")
        campaign = await campaigns_collection.find_one({"id": campaign_id})

        # Update campaign status to error
        await campaigns_collection.update_one(
            {"id": campaign_id},
            {
                "$set": {
                    "status": "error",
                    "error_message": str(e),
                    "updated_at": datetime.utcnow().isoformat()
                }
            }
        )

        # Send Slack notification for campaign processing failure
        if SLACK_NOTIFICATIONS_ENABLED and campaign:
            try:
                slack = get_slack_notifier()
                await slack.notify_voice_failure(
                    campaign_id=campaign_id,
                    campaign_name=campaign.get("name", "Unknown Campaign"),
                    error_message=f"Campaign audience processing failed: {str(e)}",
                    organization_id=campaign.get("organization_id")
                )
            except Exception as slack_error:
                logger.error(f"Failed to send Slack notification: {slack_error}")


async def load_predefined_audience(audience_id: str, organization_id: str) -> List[Dict[str, Any]]:
    """
    Load contacts from predefined audience.

    Args:
        audience_id: The predefined audience ID
        organization_id: The organization ID

    Returns:
        List of contact dictionaries
    """
    # This would load from your existing audience management system
    # For now, return mock data
    logger.info(f"Loading predefined audience {audience_id} for organization: {organization_id}")
    return [
        {"id": "1", "name": "John Doe", "phone": "+1234567890"},
        {"id": "2", "name": "Jane Smith", "phone": "+1234567891"}
    ]


async def query_database_audience(
    connection_id: str,
    table_name: str,
    filter_conditions: List[FilterCondition],
    organization_id: str
) -> List[Dict[str, Any]]:
    """
    Query database to get filtered audience.

    Args:
        connection_id: Database connection ID
        table_name: Table to query
        filter_conditions: List of filter conditions
        organization_id: The organization ID

    Returns:
        List of contact dictionaries from database
    """
    try:
        logger.info(f"Querying database audience for organization: {organization_id}, connection: {connection_id}")

        connection = await get_database_connection(connection_id, organization_id)
        if not connection:
            return []
        
        # Build SQL query with filters
        query = f"SELECT * FROM {table_name}"
        params = []
        
        if filter_conditions:
            where_clauses = []
            for condition in filter_conditions:
                if condition.operator == "equals":
                    where_clauses.append(f"{condition.field} = %s")
                    params.append(condition.value)
                elif condition.operator == "not_equals":
                    where_clauses.append(f"{condition.field} != %s")
                    params.append(condition.value)
                elif condition.operator == "greater_than":
                    where_clauses.append(f"{condition.field} > %s")
                    params.append(condition.value)
                elif condition.operator == "less_than":
                    where_clauses.append(f"{condition.field} < %s")
                    params.append(condition.value)
                elif condition.operator == "contains":
                    where_clauses.append(f"{condition.field} LIKE %s")
                    params.append(f"%{condition.value}%")
                elif condition.operator == "is_null":
                    where_clauses.append(f"{condition.field} IS NULL")
                elif condition.operator == "is_not_null":
                    where_clauses.append(f"{condition.field} IS NOT NULL")
            
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
        
        # Execute query
        if connection["type"] == "postgresql":
            conn = await asyncpg.connect(
                host=connection["host"],
                port=connection["port"],
                database=connection["database"],
                user=connection["username"],
                password=connection["password"]
            )
            
            # Convert %s to $1, $2, etc for PostgreSQL
            pg_query = query
            for i, _ in enumerate(params):
                pg_query = pg_query.replace("%s", f"${i+1}", 1)
            
            rows = await conn.fetch(pg_query, *params)
            await conn.close()
            
            return [dict(row) for row in rows]
            
        elif connection["type"] == "mysql":
            conn = await aiomysql.connect(
                host=connection["host"],
                port=connection["port"],
                db=connection["database"],
                user=connection["username"],
                password=connection["password"]
            )
            
            cursor = await conn.cursor(aiomysql.DictCursor)
            await cursor.execute(query, params)
            rows = await cursor.fetchall()
            await cursor.close()
            conn.close()
            
            return list(rows)
        
        return []
        
    except Exception as e:
        logger.error(f"Error querying database audience: {str(e)}")
        return []


async def start_campaign_execution(campaign_id: str):
    """Start executing a voice campaign."""
    try:
        # Update campaign status
        campaigns_collection = get_collection("voice_campaigns")
        await campaigns_collection.update_one(
            {"id": campaign_id},
            {
                "$set": {
                    "status": "running",
                    "started_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
            }
        )
        
        # Start processing calls
        await process_campaign_calls(campaign_id)
        
    except Exception as e:
        logger.error(f"Error starting campaign execution: {str(e)}")


async def schedule_campaign_execution(campaign_id: str, scheduled_date: str, scheduled_time: str):
    """Schedule campaign execution for later."""
    # In production, this would use a job scheduler like Celery
    # For now, we'll just update the campaign status
    campaigns_collection = get_collection("voice_campaigns")
    campaigns_collection.update_one(
        {"id": campaign_id},
        {
            "$set": {
                "status": "scheduled",
                "updated_at": datetime.utcnow().isoformat()
            }
        }
    )


async def process_campaign_calls(campaign_id: str):
    """Process calls for a campaign with concurrency limits and SSE updates."""
    try:
        from shared.services.sse_publisher import sse_publisher

        campaigns_collection = get_collection("voice_campaigns")
        calls_collection = get_collection("campaign_calls")

        # Get campaign configuration
        campaign = campaigns_collection.find_one({"id": campaign_id})
        if not campaign:
            return

        max_concurrent = campaign.get("max_concurrent_calls", 3)

        # Get pending calls
        cursor = calls_collection.find({
            "campaign_id": campaign_id,
            "status": "pending"
        }).limit(100)  # Process in batches
        pending_calls = await cursor.to_list(length=100)

        # Process calls with concurrency limit
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_single_call(call_record):
            async with semaphore:
                await make_vapi_call(campaign_id, call_record, campaign)

        # Execute calls concurrently
        tasks = [process_single_call(call) for call in pending_calls]
        await asyncio.gather(*tasks, return_exceptions=True)

        # Publish progress update after batch
        total_calls = await calls_collection.count_documents({"campaign_id": campaign_id})
        completed_calls = await calls_collection.count_documents({
            "campaign_id": campaign_id,
            "status": {"$in": ["completed", "failed"]}
        })
        successful_calls = await calls_collection.count_documents({
            "campaign_id": campaign_id,
            "status": "completed"
        })
        failed_calls = await calls_collection.count_documents({
            "campaign_id": campaign_id,
            "status": "failed"
        })

        success_rate = (successful_calls / completed_calls * 100) if completed_calls > 0 else 0

        # Publish SSE progress event
        await sse_publisher.publish(
            campaign_id,
            "voice_progress",
            {
                "id": campaign_id,
                "campaign_id": campaign_id,
                "status": campaign.get("status", "running"),
                "calls_made": completed_calls,
                "calls_total": total_calls,
                "success_count": successful_calls,
                "failed_count": failed_calls,
                "success_rate": round(success_rate, 2),
                "current_cost": campaign.get("total_cost", 0)
            }
        )

        logger.info(f"Processed {len(pending_calls)} calls for campaign {campaign_id}")

    except Exception as e:
        logger.error(f"Error processing campaign calls: {str(e)}")


async def make_vapi_call(campaign_id: str, call_record: Dict[str, Any], campaign: Dict[str, Any]):
    """Make a VAPI call for a specific contact with SSE updates."""
    try:
        from shared.services.sse_publisher import sse_publisher

        calls_collection = get_collection("campaign_calls")

        # Update call status to calling
        await calls_collection.update_one(
            {"id": call_record["id"]},
            {
                "$set": {
                    "status": "calling",
                    "started_at": datetime.utcnow().isoformat(),
                    "attempts": call_record.get("attempts", 0) + 1
                }
            }
        )

        # Publish call started event
        await sse_publisher.publish(
            campaign_id,
            "call_started",
            {
                "id": campaign_id,
                "campaign_id": campaign_id,
                "call_id": call_record["id"],
                "contact_name": call_record.get("contact_name", "Unknown"),
                "phone_number": call_record["phone_number"]
            }
        )
        
        # Get VAPI configuration
        vapi_api_key = os.getenv("VAPI_API_KEY")
        if not vapi_api_key:
            raise Exception("VAPI API key not configured")
        
        # Prepare VAPI call request
        webhook_url = f"https://api.ailabsafrica.com/campaigns/webhook/vapi/{campaign_id}"
        
        call_request = {
            "assistant": {
                "model": {
                    "provider": "openai",
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {
                            "role": "system",
                            "content": campaign.get("system_prompt", "You are a helpful voice assistant.")
                        }
                    ]
                },
                "voice": {
                    "provider": "11labs",
                    "voiceId": "EXAVITQu4vr4xnSDxMaL"
                }
            },
            "customer": {
                "number": call_record["phone_number"]
            },
            "metadata": {
                "campaign_id": campaign_id,
                "call_id": call_record["id"],
                "contact_id": call_record["contact_id"],
                "organization_id": campaign.get("organization_id") or campaign.get("tenant_id")  # Include organization context
            },
            "serverMessages": [
                {
                    "type": "status-update",
                    "url": webhook_url
                },
                {
                    "type": "transcript",
                    "url": webhook_url
                },
                {
                    "type": "end-of-call-report",
                    "url": webhook_url
                }
            ]
        }
        
        # Make VAPI API call
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.vapi.ai/call",
                headers={
                    "Authorization": f"Bearer {vapi_api_key}",
                    "Content-Type": "application/json"
                },
                json=call_request,
                timeout=30.0
            )
        
        if response.is_success:
            vapi_call_data = response.json()
            vapi_call_id = vapi_call_data.get("id")
            
            # Update call record with VAPI call ID
            await calls_collection.update_one(
                {"id": call_record["id"]},
                {
                    "$set": {
                        "vapi_call_id": vapi_call_id,
                        "vapi_call_data": vapi_call_data,
                        "updated_at": datetime.utcnow().isoformat()
                    }
                }
            )
            
            logger.info(f"VAPI call initiated for campaign {campaign_id}, call {call_record['id']}")
            
        else:
            # Handle VAPI call failure
            error_msg = f"VAPI call failed: {response.text}"
            await calls_collection.update_one(
                {"id": call_record["id"]},
                {
                    "$set": {
                        "status": "failed",
                        "error_message": error_msg,
                        "completed_at": datetime.utcnow().isoformat()
                    }
                }
            )

            # Send Slack notification for voice call failure
            if SLACK_NOTIFICATIONS_ENABLED:
                try:
                    slack = get_slack_notifier()
                    await slack.notify_voice_failure(
                        campaign_id=campaign_id,
                        campaign_name=campaign.get("name", "Unknown Campaign"),
                        error_message=error_msg,
                        organization_id=campaign.get("organization_id"),
                        recipient_phone=call_record.get("phone_number"),
                        call_id=call_record.get("id")
                    )
                except Exception as slack_error:
                    logger.error(f"Failed to send Slack notification: {slack_error}")

    except Exception as e:
        logger.error(f"Error making VAPI call: {str(e)}")

        # Update call status to failed
        calls_collection = get_collection("campaign_calls")
        await calls_collection.update_one(
            {"id": call_record["id"]},
            {
                "$set": {
                    "status": "failed",
                    "error_message": str(e),
                    "completed_at": datetime.utcnow().isoformat()
                }
            }
        )

        # Send Slack notification for voice call failure
        if SLACK_NOTIFICATIONS_ENABLED:
            try:
                slack = get_slack_notifier()
                await slack.notify_voice_failure(
                    campaign_id=campaign_id,
                    campaign_name=campaign.get("name", "Unknown Campaign"),
                    error_message=str(e),
                    organization_id=campaign.get("organization_id"),
                    recipient_phone=call_record.get("phone_number"),
                    call_id=call_record.get("id")
                )
            except Exception as slack_error:
                logger.error(f"Failed to send Slack notification: {slack_error}")


async def process_call_completion(campaign_id: str, call_id: str, webhook_data: Dict[str, Any]):
    """Process call completion and trigger follow-up actions with SSE updates."""
    try:
        from shared.services.sse_publisher import sse_publisher

        calls_collection = get_collection("campaign_calls")
        campaigns_collection = get_collection("voice_campaigns")

        # Get call record
        call_record = calls_collection.find_one({"vapi_call_id": call_id})
        if not call_record:
            return

        # Extract call data
        call_data = webhook_data.get("call", {})
        transcript = call_data.get("transcript", "")
        duration = call_data.get("duration", 0)
        cost = call_data.get("cost", 0.0)

        # Update call record
        await calls_collection.update_one(
            {"id": call_record["id"]},
            {
                "$set": {
                    "status": "completed",
                    "transcript": transcript,
                    "duration": duration,
                    "cost": cost,
                    "completed_at": datetime.utcnow().isoformat(),
                    "webhook_data": webhook_data
                }
            }
        )

        # Get campaign configuration
        campaign = campaigns_collection.find_one({"id": campaign_id})
        if not campaign:
            return

        # Generate AI summary
        summary = await generate_call_summary(transcript)
        await calls_collection.update_one(
            {"id": call_record["id"]},
            {"$set": {"summary": summary}}
        )

        # Publish call completed event
        await sse_publisher.publish(
            campaign_id,
            "call_completed",
            {
                "id": campaign_id,
                "campaign_id": campaign_id,
                "call_id": call_record["id"],
                "contact_name": call_record.get("contact_name", "Unknown"),
                "phone_number": call_record["phone_number"],
                "duration": duration,
                "status": "success",
                "transcript_available": bool(transcript),
                "summary": summary,
                "cost": cost
            }
        )

        # Send email summary if enabled
        if campaign.get("enable_email_summaries", False):
            await send_email_summary(campaign, call_record, transcript, summary)

        # Update database based on call outcome if configured
        await update_contact_database(campaign, call_record, transcript, summary)

        logger.info(f"Processed call completion for campaign {campaign_id}, call {call_record['id']}")

    except Exception as e:
        logger.error(f"Error processing call completion: {str(e)}")


async def generate_call_summary(transcript: str) -> str:
    """Generate AI summary of call transcript."""
    try:
        # Use OpenAI or other AI service to generate summary
        # For now, return a simple summary
        if len(transcript) > 100:
            return transcript[:100] + "..."
        return transcript
        
    except Exception as e:
        logger.error(f"Error generating call summary: {str(e)}")
        return "Summary unavailable"


async def send_email_summary(
    campaign: Dict[str, Any],
    call_record: Dict[str, Any],
    transcript: str,
    summary: str
):
    """Send email summary using Resend API."""
    try:
        resend_api_key = os.getenv("RESEND_API_KEY")
        if not resend_api_key:
            logger.warning("Resend API key not configured")
            return
        
        # Prepare email content
        template = campaign.get("email_template", "")
        if not template:
            template = """
            Call Summary Report
            
            Contact: {{caller_name}}
            Phone: {{phone_number}}
            Duration: {{duration}} seconds
            
            Summary: {{summary}}
            
            Full Transcript:
            {{transcript}}
            """
        
        # Replace variables in template
        email_content = template.replace("{{transcript}}", transcript)
        email_content = email_content.replace("{{summary}}", summary)
        email_content = email_content.replace("{{duration}}", str(call_record.get("duration", 0)))
        email_content = email_content.replace("{{caller_name}}", call_record.get("contact_name", "Unknown"))
        email_content = email_content.replace("{{phone_number}}", call_record.get("phone_number", ""))
        
        # Send email via Resend
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {resend_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "from": "campaigns@ailabsafrica.com",
                    "to": [campaign.get("notification_email", "admin@ailabsafrica.com")],
                    "subject": f"Call Summary - {campaign['name']}",
                    "text": email_content
                }
            )
        
        if response.is_success:
            logger.info(f"Email summary sent for campaign {campaign['id']}")
        else:
            logger.error(f"Failed to send email summary: {response.text}")
            
    except Exception as e:
        logger.error(f"Error sending email summary: {str(e)}")


async def update_contact_database(
    campaign: Dict[str, Any],
    call_record: Dict[str, Any],
    transcript: str,
    summary: str
):
    """Update contact database with call results."""
    try:
        # This would update the original database table with call results
        # Implementation depends on campaign configuration
        pass
        
    except Exception as e:
        logger.error(f"Error updating contact database: {str(e)}")


async def process_call_status_update(campaign_id: str, call_id: str, webhook_data: Dict[str, Any]):
    """Process VAPI call status updates."""
    try:
        calls_collection = get_collection("campaign_calls")
        
        # Update call status based on webhook data
        status = webhook_data.get("message", {}).get("status", "unknown")
        
        await calls_collection.update_one(
            {"vapi_call_id": call_id},
            {
                "$set": {
                    "status": status,
                    "updated_at": datetime.utcnow().isoformat()
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error processing call status update: {str(e)}")


async def process_call_transcript(campaign_id: str, call_id: str, webhook_data: Dict[str, Any]):
    """Process real-time call transcript updates."""
    try:
        calls_collection = get_collection("campaign_calls")
        
        # Update transcript
        transcript_data = webhook_data.get("message", {}).get("transcript", "")
        
        await calls_collection.update_one(
            {"vapi_call_id": call_id},
            {
                "$set": {
                    "live_transcript": transcript_data,
                    "updated_at": datetime.utcnow().isoformat()
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error processing call transcript: {str(e)}")

# ==================== SSE Endpoints ====================

@router.get("/{campaign_id}/status-stream")
async def stream_voice_campaign_status(
    request: Request,
    campaign_id: str,
    token: Optional[str] = None
):
    """
    Stream real-time voice campaign status updates using Server-Sent Events (SSE).

    Uses the shared SSE publisher service for efficient event broadcasting.
    Events are published from the campaign execution loop and streamed to all connected clients.

    Usage from frontend:
    ```javascript
    const token = getAuthToken(); // Get JWT token
    const eventSource = new EventSource(`/campaigns/voice-campaigns/${id}/status-stream?token=${token}`);
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Campaign progress:', data);
    };
    ```
    """
    from shared.services.sse_publisher import sse_publisher

    async def event_generator():
        """Generate SSE events with campaign status updates."""
        try:
            # Authenticate using query parameter token
            if not token:
                yield f"data: {json.dumps({'error': 'Authentication token required'})}\n\n"
                return

            # Manually authenticate with the token
            try:
                from ..auth import get_current_user_mongo
                current_user = await get_current_user_mongo(authorization=f"Bearer {token}")
            except Exception as e:
                logger.error(f"Authentication failed for SSE: {e}")
                yield f"data: {json.dumps({'error': 'Authentication failed'})}\n\n"
                return

            org_id = get_organization_context(request)
            if org_id:
                await validate_organization_access(request, current_user, org_id)

            organization_id = org_id or current_user.get("organization_id") or current_user.get("tenant_id")
            user_id = current_user.get("sub") or current_user.get("user_id")

            campaigns_collection = get_collection("voice_campaigns")

            # Verify access
            campaign = await campaigns_collection.find_one({"id": campaign_id})
            if not campaign:
                yield f"data: {json.dumps({'error': 'Campaign not found'})}\n\n"
                return

            if campaign.get("organization_id") != organization_id:
                yield f"data: {json.dumps({'error': 'Access denied'})}\n\n"
                return

            # Get initial campaign data
            calls_collection = get_collection("campaign_calls")
            total_calls = await calls_collection.count_documents({"campaign_id": campaign_id})
            completed_calls = await calls_collection.count_documents({
                "campaign_id": campaign_id,
                "status": {"$in": ["completed", "failed"]}
            })
            successful_calls = await calls_collection.count_documents({
                "campaign_id": campaign_id,
                "status": "completed"
            })
            failed_calls = await calls_collection.count_documents({
                "campaign_id": campaign_id,
                "status": "failed"
            })

            success_rate = (successful_calls / completed_calls * 100) if completed_calls > 0 else 0

            initial_data = {
                "id": campaign_id,
                "campaign_id": campaign_id,
                "status": campaign.get("status", "unknown"),
                "calls_made": completed_calls,
                "calls_total": total_calls,
                "success_count": successful_calls,
                "failed_count": failed_calls,
                "success_rate": round(success_rate, 2),
                "current_cost": campaign.get("total_cost", 0)
            }

            # Subscribe to SSE events for this campaign
            async for event in sse_publisher.subscribe(campaign_id, user_id, initial_data):
                # Check for keep-alive
                if event.get("_keepalive"):
                    yield ": keepalive\n\n"
                    continue

                # Send event data
                yield f"data: {json.dumps(event)}\n\n"

        except asyncio.CancelledError:
            logger.info(f"Client disconnected from voice campaign {campaign_id} status stream")
        except Exception as e:
            logger.error(f"Error in voice campaign status stream: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable buffering in nginx
        }
    )


@router.get("/{campaign_id}/call-stream")
async def stream_voice_campaign_calls(
    request: Request,
    campaign_id: str,
    token: Optional[str] = None
):
    """
    Stream individual call completion events in real-time.

    This endpoint streams call_completed events as individual calls finish,
    allowing the UI to show live call completions with transcripts and summaries.

    Usage from frontend:
    ```javascript
    const eventSource = new EventSource(`/campaigns/voice-campaigns/${id}/call-stream?token=${token}`);
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.event_type === 'call_completed') {
            console.log('Call completed:', data.contact_name, data.duration);
        }
    };
    ```
    """
    from shared.services.sse_publisher import sse_publisher

    async def event_generator():
        """Generate SSE events for individual call completions."""
        try:
            # Authenticate using query parameter token
            if not token:
                yield f"data: {json.dumps({'error': 'Authentication token required'})}\n\n"
                return

            # Manually authenticate with the token
            try:
                from ..auth import get_current_user_mongo
                current_user = await get_current_user_mongo(authorization=f"Bearer {token}")
            except Exception as e:
                logger.error(f"Authentication failed for SSE: {e}")
                yield f"data: {json.dumps({'error': 'Authentication failed'})}\n\n"
                return

            org_id = get_organization_context(request)
            if org_id:
                await validate_organization_access(request, current_user, org_id)

            organization_id = org_id or current_user.get("organization_id") or current_user.get("tenant_id")
            user_id = current_user.get("sub") or current_user.get("user_id")

            campaigns_collection = get_collection("voice_campaigns")

            # Verify access
            campaign = await campaigns_collection.find_one({"id": campaign_id})
            if not campaign:
                yield f"data: {json.dumps({'error': 'Campaign not found'})}\n\n"
                return

            if campaign.get("organization_id") != organization_id:
                yield f"data: {json.dumps({'error': 'Access denied'})}\n\n"
                return

            # Subscribe to SSE events for this campaign (call events only)
            async for event in sse_publisher.subscribe(campaign_id, user_id):
                # Check for keep-alive
                if event.get("_keepalive"):
                    yield ": keepalive\n\n"
                    continue

                # Only stream call-related events
                event_type = event.get("event_type", "")
                if event_type in ["call_completed", "call_started", "call_failed"]:
                    yield f"data: {json.dumps(event)}\n\n"

        except asyncio.CancelledError:
            logger.info(f"Client disconnected from voice campaign {campaign_id} call stream")
        except Exception as e:
            logger.error(f"Error in voice campaign call stream: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable buffering in nginx
        }
    )
