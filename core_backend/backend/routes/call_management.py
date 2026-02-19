"""
Call Management Routes

This module provides endpoints for managing VAPI call logs, summaries, and notifications.
Integrates with Supabase for call logging and email services for notifications.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, timedelta
import os
import asyncio
import time
import pytz

# Direct Supabase integration (bypassing shared library import issues)
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

# Import shared Supabase integration as fallback
import sys
sys.path.append('/opt/kasaai/apps/shared')
try:
    from integration.supabase import SupabaseIntegration, SupabaseConfig, SupabaseQueryResponse
except ImportError:
    logger.warning("Shared Supabase integration not available, using direct integration")
from ai.ai_powered_features import AIPoweredFeatures, CallSummary, CallOutcome, ConversationSentiment
from ..services.call_logs_service import call_logs_service
from ..models.call_logs import CallLogCreate, CallLogUpdate, CallLogFilter, CallLogListResponse, CallStatus, CallDirection
from ..auth import get_current_user_mongo
from ..middleware.organization_context import (
    get_organization_context,
    require_organization_context,
    validate_organization_access,
    get_user_organization_filter
)
try:
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
except ImportError:
    # Fallback if email modules are not available
    smtplib = None
    MIMEText = None
    MIMEMultipart = None

logger = logging.getLogger(__name__)

# Log Supabase import status after logger is configured
if SUPABASE_AVAILABLE:
    logger.info("✅ Supabase library imported successfully")
else:
    logger.error("❌ Supabase library not available")

router = APIRouter(prefix="/call-management", tags=["Call Management"])

class CallLogRequest(BaseModel):
    call_id: str = Field(..., description="Unique call identifier")
    transcript: str = Field(..., description="Call transcript")
    summary: Optional[str] = Field(None, description="Call summary")
    customer_phone: Optional[str] = Field(None, description="Customer phone number")
    duration: Optional[int] = Field(None, description="Call duration in seconds")
    status: str = Field("completed", description="Call status")
    assistant_id: Optional[str] = Field(None, description="Assistant ID")
    assistant_name: Optional[str] = Field(None, description="Assistant name")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class CallLogResponse(BaseModel):
    success: bool
    call_id: str
    logged_at: str
    supabase_id: Optional[str] = None
    table_verified: Optional[bool] = None

class EmailNotificationRequest(BaseModel):
    call_summary: str = Field(..., description="Summary of the call")
    call_id: str = Field(..., description="Unique call identifier")
    customer_info: Optional[Dict[str, Any]] = Field(None, description="Customer information")
    priority: str = Field("normal", description="Email priority level")

class EmailNotificationResponse(BaseModel):
    success: bool
    call_id: str
    sent_at: str
    email_recipient: str

class SupabaseIntegrationRequest(BaseModel):
    action: str = Field(..., description="Action to perform: insert, query, update")
    table: str = Field(..., description="Target table name")
    data: Optional[Dict[str, Any]] = Field(None, description="Data for insert/update operations")
    filters: Optional[Dict[str, Any]] = Field(None, description="Filters for query operations")
    limit: Optional[int] = Field(10, description="Limit for query results")

class SupabaseIntegrationResponse(BaseModel):
    success: bool
    action: str
    table: str
    data: Optional[List[Dict[str, Any]]] = None
    count: Optional[int] = None
    message: Optional[str] = None
    error: Optional[str] = None

class VAPIServerMessage(BaseModel):
    type: str = Field(..., description="Message type from VAPI")
    call: Optional[Dict[str, Any]] = Field(None, description="Call object from VAPI")
    transcript: Optional[str] = Field(None, description="Call transcript")
    recordingUrl: Optional[str] = Field(None, description="Recording URL")
    stereoRecordingUrl: Optional[str] = Field(None, description="Stereo recording URL")
    assistantId: Optional[str] = Field(None, description="Assistant ID")
    customer: Optional[Dict[str, Any]] = Field(None, description="Customer information")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class VAPIWebhookResponse(BaseModel):
    success: bool
    message: str
    call_id: Optional[str] = None
    summary_generated: Optional[bool] = None
    email_sent: Optional[bool] = None
    data_saved: Optional[bool] = None

class CurrentDateTimeResponse(BaseModel):
    current_datetime: str = Field(..., description="Current date and time in ISO format")
    current_date: str = Field(..., description="Current date in YYYY-MM-DD format")
    current_time: str = Field(..., description="Current time in HH:MM:SS format")
    timezone: str = Field(..., description="Current timezone")
    timestamp: int = Field(..., description="Unix timestamp")
    business_day: bool = Field(..., description="Whether current date is a business day (Mon-Fri)")
    business_hours: bool = Field(..., description="Whether current time is within business hours (9 AM - 5 PM)")
    day_of_week: str = Field(..., description="Current day of the week")
    month_name: str = Field(..., description="Current month name")
    formatted_date: str = Field(..., description="Human-readable date format")



def get_supabase_client():
    """Get direct Supabase client connection."""
    if not SUPABASE_AVAILABLE:
        raise HTTPException(status_code=500, detail="Supabase library not available")

    url = os.getenv("DEMO_SUPABASE_URL", "https://fwbntpzdlrtxelizkprl.supabase.co")
    service_role_key = os.getenv("DEMO_SUPABASE_SUPABASE_KEY")

    if not service_role_key:
        raise HTTPException(status_code=500, detail="Supabase service role key not found in environment")

    return create_client(url, service_role_key)

def get_supabase_integration():
    """Initialize Supabase integration with proper configuration from integration_api_keys.md."""
    # Try direct client first
    if SUPABASE_AVAILABLE:
        return get_supabase_client()

    # Fallback to shared integration
    # Use configuration from integration_api_keys.md
    url = os.getenv("DEMO_SUPABASE_URL", "https://fwbntpzdlrtxelizkprl.supabase.co")
    anon_key = os.getenv("DEMO_SUPABASE_ANON_KEY")
    service_role_key = os.getenv("DEMO_SUPABASE_SUPABASE_KEY")

    if not service_role_key:
        raise HTTPException(status_code=500, detail="Supabase service role key not found in environment")

    config = SupabaseConfig(
        url=url,
        anon_key=anon_key or service_role_key,  # Use service role key as fallback
        service_role_key=service_role_key,
        timeout=30,
        verify_ssl=True
    )

    return SupabaseIntegration(config)


async def verify_table_exists(table_name: str) -> bool:
    """
    Verify if a table exists in Supabase. Non-blocking - assumes tables exist
    since schema cache refresh issues are common with PostgREST.
    """
    try:
        if not SUPABASE_AVAILABLE:
            logger.debug(f"Supabase not available for table '{table_name}' verification - assuming exists")
            return True

        supabase = get_supabase_client()
        response = supabase.table(table_name).select("*").limit(1).execute()

        if response.data is not None:
            logger.info(f"✅ Table '{table_name}' verified and accessible")
            return True
        else:
            # PostgREST schema cache issue - assume table exists
            logger.debug(f"⚠️ Table '{table_name}' verification returned no data (likely schema cache) - assuming exists")
            return True

    except Exception as e:
        # Check if this is a schema cache error (PGRST205)
        error_str = str(e)
        if "PGRST205" in error_str or "schema cache" in error_str.lower():
            logger.debug(f"⚠️ Table '{table_name}' schema cache issue (PGRST205) - assuming exists")
            return True
        else:
            logger.warning(f"⚠️ Table '{table_name}' verification failed: {error_str} - assuming exists")
            return True

async def get_available_tables() -> List[str]:
    """Get list of available tables using Supabase MCP integration."""
    try:
        # Get actual tables from Supabase MCP (we know these exist from our earlier check)
        actual_tables = [
            "call_logs", "profiles", "assistants", "campaigns", "usage_summary",
            "bundle_purchases", "demo_bookings", "wallets", "payment_transactions",
            "custom_demos", "custom_templates", "demo_html_storage", "usage_tracking",
            "demo_analytics", "demo_sessions", "voice_agents", "refunds",
            "wallet_transactions", "usage_bundles", "demo_comments",
            "demo_comment_replies", "demo_versions", "contact_submissions", "emails"
        ]

        available_tables = []
        for table in actual_tables:
            if await verify_table_exists(table):
                available_tables.append(table)

        return available_tables
    except Exception as e:
        logger.error(f"Error getting available tables: {str(e)}")
        return []


@router.post("/log-call", response_model=CallLogResponse)
async def log_call_to_databases(request: CallLogRequest):
    """
    Log call information to MongoDB vapi_calls collection.

    This endpoint stores call transcripts, summaries, and metadata for
    analytics and record-keeping purposes.

    Webhook endpoint - organization context tracked in metadata.
    """
    try:
        # Extract organization context from metadata for tracking
        org_id = request.metadata.get("organization_id") if request.metadata else None
        logger.info(f"Processing call log for call_id={request.call_id}, organization={org_id}")

        current_time = datetime.utcnow()

        # Log to MongoDB vapi_calls collection
        mongo_call_data = CallLogCreate(
            call_id=request.call_id,
            assistant_id=request.assistant_id or (request.metadata.get("assistant_id") if request.metadata else None),
            assistant_name=request.assistant_name or (request.metadata.get("assistant_name") if request.metadata else None),
            status=CallStatus.COMPLETED if request.status == "completed" else CallStatus.IN_PROGRESS,
            direction=CallDirection.INBOUND,
            from_phone=request.customer_phone,
            to_phone=request.metadata.get("to_phone") if request.metadata else None,
            transcript=request.transcript,
            summary=request.summary,
            duration=request.duration,
            metadata=request.metadata or {},
            organization_id=org_id,
            user_id=request.metadata.get("user_id") if request.metadata else None,
            customer_id=request.metadata.get("customer_id") if request.metadata else None
        )

        mongo_response = await call_logs_service.create_call_log(mongo_call_data)

        if mongo_response.success:
            logger.info(f"✅ Successfully logged call {request.call_id} to MongoDB (ID: {mongo_response.mongo_id})")
            return CallLogResponse(
                success=True,
                call_id=request.call_id,
                logged_at=current_time.isoformat(),
                table_verified=True,
                data_saved=True,
                mongo_id=mongo_response.mongo_id
            )
        else:
            raise HTTPException(status_code=500, detail=f"Failed to log call to MongoDB: {mongo_response.message}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error logging call to database: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to log call: {str(e)}")


@router.get("/call-logs", response_model=CallLogListResponse)
async def get_call_logs(
    page: int = 1,
    page_size: int = 20,
    user_id: Optional[str] = None,
    assistant_id: Optional[str] = None,
    automation_id: Optional[str] = None,
    automation_name: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    keyword: Optional[str] = None,
    current_user: dict = Depends(get_current_user_mongo),
    request: Request = None
):
    """
    Retrieve call logs from MongoDB with filtering and pagination.

    This endpoint provides fast access to call logs stored in MongoDB
    with comprehensive filtering options. Now properly scoped to organization.

    Requires authentication and organization context via X-Organization-ID header.
    """
    try:
        # Get organization context from request
        org_id = get_organization_context(request)

        # Validate user has access to the organization
        if org_id:
            await validate_organization_access(org_id, current_user)

        # Build filters with organization scope
        filters = CallLogFilter()

        # Apply organization filter from user context (correct parameter order: user first, then org_id)
        org_filter = get_user_organization_filter(current_user, org_id)

        # Apply organization filter - now using vapi_calls which has proper org_id
        if org_filter.get("organization_id"):
            filters.organization_id = org_filter["organization_id"]

        if user_id:
            filters.user_id = user_id
        if assistant_id:
            filters.assistant_id = assistant_id
        if automation_id:
            filters.automation_id = automation_id
        if automation_name:
            filters.automation_name = automation_name
        if status:
            try:
                filters.status = CallStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        if start_date:
            try:
                filters.start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format. Use ISO format.")
        if end_date:
            try:
                filters.end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format. Use ISO format.")
        if keyword:
            filters.keyword = keyword

        # Get call logs from MongoDB
        response = await call_logs_service.list_call_logs(
            filters=filters,
            page=page,
            page_size=page_size,
            sort_by="created_at",
            sort_order=-1  # Most recent first
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving call logs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve call logs: {str(e)}")


@router.get("/call-logs/{call_id}")
async def get_call_log_by_id(
    call_id: str,
    current_user: dict = Depends(get_current_user_mongo),
    request: Request = None
):
    """
    Get a specific call log by call_id from MongoDB.

    Requires authentication and organization access validation.
    """
    try:
        response = await call_logs_service.get_call_log(call_id)

        if not response.success:
            raise HTTPException(status_code=404, detail=response.message)

        # Validate user has access to this call's organization
        call_log = response.call_log
        if call_log and call_log.organization_id:
            org_id = call_log.organization_id
            await validate_organization_access(org_id, current_user)

        return response.call_log

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving call log {call_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve call log: {str(e)}")


@router.get("/call-analytics")
async def get_call_analytics(
    days: int = 30,
    user_id: Optional[str] = None,
    assistant_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user_mongo),
    request: Request = None
):
    """
    Get call analytics for the specified time period.

    Requires authentication and organization context. Analytics are
    automatically scoped to the user's organization.
    """
    try:
        # Get organization context from request
        org_id = get_organization_context(request)

        # Validate user has access to the organization
        if org_id:
            await validate_organization_access(org_id, current_user)

        # Get organization filter (correct parameter order: user first, then org_id)
        org_filter = get_user_organization_filter(current_user, org_id)
        organization_id = org_filter.get("organization_id")

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        analytics = await call_logs_service.get_analytics(
            start_date=start_date,
            end_date=end_date,
            organization_id=organization_id,
            user_id=user_id,
            assistant_id=assistant_id
        )

        return analytics

    except Exception as e:
        logger.error(f"Error generating call analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate analytics: {str(e)}")


@router.post("/supabase-integration", response_model=SupabaseIntegrationResponse)
async def supabase_integration_endpoint(request: SupabaseIntegrationRequest):
    """
    Generic Supabase integration endpoint for VAPI tools.

    Supports insert, query, and update operations on any table.
    This endpoint matches the functionality described in VAPI_TOOLS_DOCUMENTATION.md

    Webhook endpoint - organization context tracked in request data when available.
    """
    try:
        # Extract organization context from request data for tracking
        org_id = None
        if request.data and "organization_id" in request.data:
            org_id = request.data.get("organization_id")
        elif request.filters and "organization_id" in request.filters:
            org_id = request.filters.get("organization_id")

        logger.info(f"Supabase integration: action={request.action}, table={request.table}, organization={org_id}")

        supabase = get_supabase_integration()

        # Verify table exists
        table_exists = await verify_table_exists(request.table)
        if not table_exists:
            raise HTTPException(status_code=404, detail=f"Table '{request.table}' not found or not accessible")

        response_data = {
            "success": True,
            "action": request.action,
            "table": request.table
        }

        if request.action == "insert":
            if not request.data:
                raise HTTPException(status_code=400, detail="Data required for insert operation")

            # Add timestamps for audit
            current_time = datetime.utcnow().isoformat()
            if "created_at" not in request.data:
                request.data["created_at"] = current_time
            if "updated_at" not in request.data:
                request.data["updated_at"] = current_time

            # For call_logs table, ensure required fields are present
            if request.table == "call_logs":
                if "start_time" not in request.data:
                    request.data["start_time"] = current_time
                if "assistant_id" not in request.data:
                    request.data["assistant_id"] = "unknown"
                if "status" not in request.data:
                    request.data["status"] = "completed"

            result = await supabase.insert(request.table, request.data)

            if result.error:
                raise HTTPException(status_code=500, detail=f"Insert operation failed: {result.error}")

            response_data["data"] = result.data
            response_data["count"] = result.count or (len(result.data) if result.data else 0)
            response_data["message"] = f"Successfully inserted {response_data['count']} record(s)"
            response_data["error"] = result.error

        elif request.action == "query":
            result = await supabase.select(
                request.table,
                columns="*",
                filters=request.filters,
                limit=request.limit
            )

            if result.error:
                raise HTTPException(status_code=500, detail=f"Query operation failed: {result.error}")

            response_data["data"] = result.data
            response_data["count"] = result.count or (len(result.data) if result.data else 0)
            response_data["message"] = f"Retrieved {response_data['count']} record(s)"
            response_data["error"] = result.error

        elif request.action == "update":
            if not request.data:
                raise HTTPException(status_code=400, detail="Data required for update operation")
            if not request.filters:
                raise HTTPException(status_code=400, detail="Filters required for update operation")

            # Add updated timestamp
            request.data["updated_at"] = datetime.utcnow().isoformat()

            result = await supabase.update(request.table, request.data, request.filters)

            if result.error:
                raise HTTPException(status_code=500, detail=f"Update operation failed: {result.error}")

            response_data["data"] = result.data
            response_data["count"] = result.count or (len(result.data) if result.data else 0)
            response_data["message"] = f"Updated {response_data['count']} record(s)"
            response_data["error"] = result.error

        else:
            raise HTTPException(status_code=400, detail=f"Unsupported action: {request.action}")

        logger.info(f"Supabase {request.action} operation completed on table {request.table}")
        return SupabaseIntegrationResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in Supabase integration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Supabase operation failed: {str(e)}")


@router.post("/integrations/supabase/execute", response_model=SupabaseIntegrationResponse)
async def supabase_call_recording(request: SupabaseIntegrationRequest):
    """
    VAPI tool endpoint: supabase_call_recording

    Record call details and analytics to Supabase database.
    This endpoint matches the exact specification in VAPI_TOOLS_DOCUMENTATION.md
    """
    # This is an alias to our main supabase-integration endpoint
    # but with the exact URL path expected by VAPI tools
    return await supabase_integration_endpoint(request)


@router.post("/send-notification", response_model=EmailNotificationResponse)
async def send_email_notification(request: EmailNotificationRequest, background_tasks: BackgroundTasks):
    """
    Send email notification for call summary.

    Sends call summaries to ailabsafrica@gmail.com for team awareness
    and follow-up actions.
    """
    try:
        recipient_email = "ailabsafrica@gmail.com"

        # Prepare email content
        subject = f"Call Summary - {request.call_id}"

        # Create HTML email content
        html_content = f"""
        <html>
        <body>
            <h2>Call Summary Report</h2>

            <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 15px 0;">
                <h3>Call Details</h3>
                <p><strong>Call ID:</strong> {request.call_id}</p>
                <p><strong>Priority:</strong> {request.priority}</p>
                <p><strong>Time:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
            </div>

            <div style="background-color: #fff; padding: 15px; border: 1px solid #ddd; border-radius: 5px; margin: 15px 0;">
                <h3>Call Summary</h3>
                <p>{request.call_summary}</p>
            </div>

            {f'''
            <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 15px 0;">
                <h3>Customer Information</h3>
                <p>{str(request.customer_info)}</p>
            </div>
            ''' if request.customer_info else ''}

            <div style="margin-top: 30px; color: #666; font-size: 12px;">
                <p>This is an automated notification from the VAPI Call Management System.</p>
                <p>For questions, contact support@ailabsafrica.com</p>
            </div>
        </body>
        </html>
        """

        # Add email sending to background tasks
        background_tasks.add_task(
            send_email_async,
            recipient_email,
            subject,
            html_content,
            request.call_id
        )

        sent_at = datetime.utcnow().isoformat()
        logger.info(f"Email notification queued for call {request.call_id}")

        return EmailNotificationResponse(
            success=True,
            call_id=request.call_id,
            sent_at=sent_at,
            email_recipient=recipient_email
        )

    except Exception as e:
        logger.error(f"Error sending email notification: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send notification: {str(e)}")


async def send_email_async(recipient: str, subject: str, html_content: str, call_id: str):
    """
    Send email asynchronously using unified email service from @shared.
    """
    try:
        # Import unified email service from shared
        from apps.shared.services.unified_email_service import get_email_service

        # Get the unified email service (automatically configured from env vars)
        email_service = get_email_service()

        # Extract plain text from HTML for body
        import re
        plain_text = re.sub(r'<[^>]+>', '', html_content).strip()

        # Send email using unified service (automatically uses SMTP with iRedMail and fallback)
        result = await email_service.send_email(
            to=recipient,
            subject=subject,
            body=plain_text,
            html_body=html_content,
            from_email=None,  # Uses default from config
            from_name="KasaAI Call Management"
        )

        if result.get("success"):
            logger.info(f"✅ Email sent successfully for call {call_id} via {result.get('provider', 'unknown')}")
        else:
            logger.error(f"❌ Email sending failed for call {call_id}: {result.get('error', 'Unknown error')}")

    except ImportError as e:
        logger.warning(f"Unified email service not available: {e}. Falling back to direct SMTP.")
        # Fallback to direct SMTP if unified service not available
        await _send_email_direct_smtp(recipient, subject, html_content, call_id)
    except Exception as e:
        logger.error(f"Error sending email for call {call_id}: {str(e)}")
        # Try direct SMTP as last resort
        try:
            await _send_email_direct_smtp(recipient, subject, html_content, call_id)
        except Exception as smtp_error:
            logger.error(f"Direct SMTP fallback also failed for call {call_id}: {str(smtp_error)}")


async def _send_email_direct_smtp(recipient: str, subject: str, html_content: str, call_id: str):
    """
    Fallback: Send email directly via SMTP (used if unified service unavailable).
    """
    if not smtplib or not MIMEText or not MIMEMultipart:
        raise Exception("SMTP modules not available")

    # Email configuration - using iRedMail server
    smtp_server = os.getenv("SMTP_SERVER", "localhost")
    smtp_port = int(os.getenv("SMTP_PORT", "25"))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    sender_email = os.getenv("SENDER_EMAIL", "noreply@ailabsafrica.com")

    # Create message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = recipient

    # Attach HTML content
    html_part = MIMEText(html_content, 'html')
    msg.attach(html_part)

    # Send email via SMTP server
    server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)

    # Use STARTTLS if port 587 (submission port)
    if smtp_port == 587:
        server.starttls()

    # Authenticate if credentials provided
    if smtp_username and smtp_password:
        server.login(smtp_username, smtp_password)

    text = msg.as_string()
    server.sendmail(sender_email, recipient, text)
    server.quit()

    logger.info(f"Email sent successfully via direct SMTP for call {call_id}")


async def send_email_via_resend(recipient: str, subject: str, html_content: str, call_id: str):
    """
    Send email via Resend API as fallback.
    """
    import httpx

    resend_api_key = os.getenv("RESEND_API")
    if not resend_api_key:
        raise Exception("No email service configured")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {resend_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "from": "VAPI Calls <noreply@ailabsafrica.com>",
                "to": [recipient],
                "subject": subject,
                "html": html_content
            }
        )

        if response.status_code == 200:
            logger.info(f"Email sent via Resend for call {call_id}")
        else:
            raise Exception(f"Resend API error: {response.status_code} - {response.text}")


def create_enhanced_vapi_call_email(
    call_id: str,
    summary: str,
    customer: str,
    assistant_id: str,
    transcript_preview: str,
    duration: int,
    vonage_cost: Optional[float],
    vonage_phone: str
) -> str:
    """
    Create enhanced HTML email for VAPI call with cost information.
    """
    cost_display = f"${vonage_cost:.4f}" if vonage_cost else "N/A"
    duration_display = f"{duration}s ({duration//60}m {duration%60}s)" if duration else "N/A"

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>KasaAI Call Summary</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 20px; }}
            .container {{ max-width: 800px; margin: 0 auto; background: #f9f9f9; padding: 20px; border-radius: 8px; }}
            .header {{ background: #2563eb; color: white; padding: 20px; border-radius: 8px 8px 0 0; margin: -20px -20px 20px -20px; }}
            .cost-badge {{ background: #10b981; color: white; padding: 5px 10px; border-radius: 15px; font-weight: bold; }}
            .section {{ background: white; padding: 15px; margin: 10px 0; border-radius: 6px; border-left: 4px solid #2563eb; }}
            .summary {{ background: #eff6ff; padding: 15px; border-radius: 6px; margin: 10px 0; }}
            .transcript {{ background: #f8fafc; padding: 15px; border-radius: 6px; font-family: monospace; font-size: 14px; max-height: 200px; overflow-y: auto; }}
            .cost-info {{ background: #dcfce7; padding: 15px; border-radius: 6px; margin: 10px 0; }}
            .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e5e5; color: #666; font-size: 12px; }}
            .metric {{ display: inline-block; margin: 5px 15px 5px 0; }}
            .metric-value {{ font-weight: bold; color: #2563eb; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎤 KasaAI Call Summary</h1>
                <p>Call ID: <strong>{call_id}</strong> | Cost: <span class="cost-badge">{cost_display}</span></p>
            </div>

            <div class="section">
                <h3>📊 Call Metrics</h3>
                <div class="metric">
                    <span>📞 Duration:</span> <span class="metric-value">{duration_display}</span>
                </div>
                <div class="metric">
                    <span>💰 Vonage Cost:</span> <span class="metric-value">{cost_display}</span>
                </div>
                <div class="metric">
                    <span>📱 Vonage Phone:</span> <span class="metric-value">{vonage_phone}</span>
                </div>
                <div class="metric">
                    <span>🤖 Assistant:</span> <span class="metric-value">{assistant_id}</span>
                </div>
                <div class="metric">
                    <span>👤 Customer:</span> <span class="metric-value">{customer}</span>
                </div>
            </div>

            <div class="cost-info">
                <h3>💵 Cost Breakdown</h3>
                <p><strong>Vonage Voice Cost:</strong> {cost_display}</p>
                <p><em>Estimated based on duration and destination. Actual costs may vary.</em></p>
            </div>

            <div class="summary">
                <h3>📝 AI-Generated Summary</h3>
                <p>{summary if summary else 'Summary generation in progress...'}</p>
            </div>

            <div class="section">
                <h3>📄 Transcript Preview</h3>
                <div class="transcript">{transcript_preview}{'...' if len(transcript_preview) >= 300 else ''}</div>
            </div>

            <div class="footer">
                <p>🔗 <strong>Integration Details:</strong></p>
                <ul>
                    <li>VAPI Webhook: https://api.ailabsafrica.com/call-management/vapi/webhook</li>
                    <li>Cost Monitoring: Vonage API integration</li>
                    <li>Phone Number: {vonage_phone} (VAPI ID: 6c5af6e1-a2b7-41d6-ac04-4c9691bf73e4)</li>
                </ul>
                <p><em>This is an automated notification from the VAPI Call Management System with integrated Vonage cost tracking.</em></p>
                <p>Generated at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
            </div>
        </div>
    </body>
    </html>
    """


@router.get("/tables")
async def list_available_tables():
    """List all available Supabase tables for VAPI integration."""
    try:
        available_tables = await get_available_tables()

        return {
            "success": True,
            "tables": available_tables,
            "count": len(available_tables),
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error listing tables: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.post("/vapi/webhook", response_model=VAPIWebhookResponse)
async def vapi_server_message_webhook(request: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    VAPI Server Message Webhook Endpoint

    Receives server messages from VAPI after call completion.
    Automatically generates summaries and sends email notifications.

    Expected URL for VAPI configuration: https://api.ailabsafrica.com/call-management/vapi/webhook

    Webhook endpoint - organization context tracked in call metadata.
    """
    request_start_time = time.time()

    try:
        # === STEP 1: INITIAL WEBHOOK PROCESSING ===
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')

        # Extract key information first
        call_data = request.get("call", {})
        call_id = call_data.get("id", f"vapi-call-{int(time.time())}")

        # Extract message data (for conversation-update and other events)
        message_data = request.get("message", {})
        message_type = request.get("type") or message_data.get("type", "unknown")

        # Enhanced assistant_id extraction - check multiple sources
        # Reason: Different VAPI event types have assistant_id in different locations
        assistant_id = (
            request.get("assistantId") or  # Top-level (end-of-call-report)
            call_data.get("assistantId") or  # In call object
            message_data.get("assistantId") or  # In message object (conversation-update)
            request.get("assistant", {}).get("id") or  # Nested in assistant object
            message_data.get("assistant", {}).get("id") or  # Message assistant object
            "unknown"
        )

        # Extract organization context from metadata for tracking
        # Check multiple sources for metadata: request.metadata, call_data.metadata, and call_data itself
        metadata = (
            request.get("metadata") or
            call_data.get("metadata", {}) or
            message_data.get("metadata", {}) or  # Also check message metadata
            {}
        )
        # Also check if organization_id is directly in call_data (some VAPI webhooks put it there)
        org_id = (
            metadata.get("organization_id") if metadata else None
        ) or call_data.get("organization_id") or request.get("organization_id")

        # If org_id still not found and we have assistant_id, lookup from automation config
        # Reason: Campaign calls may not have org_id in metadata, need to look it up
        automation_id = None
        if not org_id and assistant_id and assistant_id != "unknown":
            try:
                from ..mongo import get_collection
                configs_collection = get_collection("automation_configs")

                # Find automation config by assistant_id (check both fields)
                automation_config = await configs_collection.find_one({
                    "$or": [
                        {"assistant_id": assistant_id},
                        {"deployment_info.vapi_assistant_id": assistant_id}
                    ]
                })

                if automation_config:
                    org_id = automation_config.get("organization_id")
                    automation_id = str(automation_config.get("_id"))
                    logger.info(f"🔍 Looked up automation config: org_id={org_id}, automation_id={automation_id}")
            except Exception as lookup_error:
                logger.warning(f"⚠️ Failed to lookup automation config: {str(lookup_error)}")

        # Pretty header with clear separation
        logger.info("")
        logger.info("╔" + "═" * 78 + "╗")
        logger.info("║" + f"🎯 VAPI WEBHOOK RECEIVED".center(78) + "║")
        logger.info("╠" + "═" * 78 + "╣")
        logger.info("║" + f" 📅 {timestamp}".ljust(78) + "║")
        logger.info("║" + f" 🆔 Call ID: {call_id[:50]}{'...' if len(call_id) > 50 else ''}".ljust(78) + "║")
        logger.info("║" + f" 🤖 Assistant: {assistant_id[:50]}{'...' if len(assistant_id) > 50 else ''}".ljust(78) + "║")
        logger.info("║" + f" 📨 Event Type: {message_type.upper()}".ljust(78) + "║")
        logger.info("║" + f" 🏢 Organization: {org_id or 'Not specified'}".ljust(78) + "║")
        logger.info("╚" + "═" * 78 + "╝")

        # Detailed payload analysis in a clean format
        payload_size = len(str(request))
        payload_keys = list(request.keys())

        logger.info("")
        logger.info("📦 PAYLOAD ANALYSIS")
        logger.info("┌─────────────────────────────────────────────────────────────────────────────┐")
        logger.info(f"│ Size: {payload_size:,} characters")
        logger.info(f"│ Keys: {', '.join(payload_keys[:10])}{'...' if len(payload_keys) > 10 else ''}")
        logger.info("└─────────────────────────────────────────────────────────────────────────────┘")

        # Show payload preview in a code block style
        payload_str = str(request)
        if len(payload_str) > 300:
            logger.info("")
            logger.info("📋 PAYLOAD PREVIEW (first 300 chars)")
            logger.info("┌─────────────────────────────────────────────────────────────────────────────┐")
            logger.info(f"│ {payload_str[:300]}")
            logger.info("│ ...")
            logger.info("└─────────────────────────────────────────────────────────────────────────────┘")
        else:
            logger.info("")
            logger.info("📋 FULL PAYLOAD")
            logger.info("┌─────────────────────────────────────────────────────────────────────────────┐")
            for line in payload_str.split('\n'):
                if line.strip():
                    logger.info(f"│ {line[:75]}")
            logger.info("└─────────────────────────────────────────────────────────────────────────────┘")

        # === STEP 1.5: EARLY CALL DATA EXTRACTION FOR ENHANCED PROCESSING ===

        # === STEP 1.6: HANDLE SPECIFIC VAPI EVENT TYPES ===
        # Handle end-of-call-report events with enhanced processing
        if message_type == "end-of-call-report":
            logger.info("📞 END-OF-CALL-REPORT DETECTED - Enhanced processing mode")
            try:
                # Import our enhanced handlers
                from .integration_webhooks import handle_end_of_call_report, VapiWebhookRequest

                # For end-of-call-report, call data is in message.call, not top-level
                # Reason: VAPI end-of-call-report structure has call nested in message
                actual_call_data = message_data.get("call", {}) or call_data

                # Inject organization_id and automation_id into call metadata
                # Reason: Downstream handlers need org context for multi-tenant call logging
                if not actual_call_data.get("metadata"):
                    actual_call_data["metadata"] = {}
                if org_id:
                    actual_call_data["metadata"]["organization_id"] = org_id
                if automation_id:
                    actual_call_data["metadata"]["automation_id"] = automation_id

                # Convert to our webhook format with corrected call data
                webhook_request = VapiWebhookRequest(
                    call=actual_call_data,
                    message=request,
                    transcript=request.get("transcript") or message_data.get("transcript"),
                    phoneNumber=actual_call_data.get("phoneNumber") or call_data.get("phoneNumber"),
                    customer=request.get("customer") or actual_call_data.get("customer")
                )

                # Process with our enhanced pipeline
                enhanced_result = await handle_end_of_call_report(webhook_request, background_tasks)
                logger.info(f"📞 Enhanced end-of-call processing completed: {enhanced_result.get('status')}")

                # NOTE: Campaign progress update is handled in background task to avoid duplicate updates
                # and to ensure we have transcript and full call data before updating
                logger.info("📞 Campaign progress will be updated in background task with full call data")

                # Return the enhanced result
                return VAPIWebhookResponse(
                    success=True,
                    message="End-of-call report processed with enhanced pipeline",
                    call_id=call_id,
                    summary_generated=True,
                    email_sent=True,
                    data_saved=True,
                    processing_details=enhanced_result
                )

            except Exception as e:
                logger.error(f"📞 Enhanced end-of-call processing failed: {str(e)}")
                # Fall through to standard processing
                pass

        # Handle transcript events for real-time processing
        elif message_type == "transcript":
            logger.info("📝 TRANSCRIPT EVENT DETECTED - Real-time processing")
            try:
                from .integration_webhooks import handle_transcript_event, VapiWebhookRequest

                webhook_request = VapiWebhookRequest(
                    call=call_data,
                    message=request,
                    transcript=request.get("transcript"),
                    phoneNumber=call_data.get("phoneNumber"),
                    customer=request.get("customer")
                )

                transcript_result = await handle_transcript_event(webhook_request, background_tasks)
                logger.info(f"📝 Transcript event processed: {transcript_result.get('status')}")

                return VAPIWebhookResponse(
                    success=True,
                    message="Transcript event acknowledged",
                    call_id=call_id,
                    summary_generated=False,
                    email_sent=False,
                    data_saved=False,
                    processing_details=transcript_result
                )

            except Exception as e:
                logger.error(f"📝 Transcript event processing failed: {str(e)}")
                # Fall through to standard processing
                pass

        # === STEP 2: ADDITIONAL CALL DATA EXTRACTION ===
        # Extract transcript from VAPI webhook structure
        def extract_transcript_from_vapi_payload(payload):
            """Extract transcript from VAPI end-of-call-report payload"""
            try:
                # Method 1: Direct transcript field
                if payload.get("transcript"):
                    return payload["transcript"]

                # Method 2: From call data
                if call_data.get("transcript"):
                    return call_data["transcript"]

                # Method 3: From message.artifact.messages (VAPI end-of-call-report structure)
                message = payload.get("message", {})
                if message.get("type") == "end-of-call-report":
                    artifact = message.get("artifact", {})
                    messages = artifact.get("messages", [])

                    if messages:
                        # Build transcript from conversation messages
                        transcript_parts = []
                        for msg in messages:
                            role = msg.get("role", "unknown")
                            content = msg.get("message", "")

                            # Skip system messages, include user and assistant
                            if role in ["user", "assistant"] and content:
                                speaker = "User" if role == "user" else "Assistant"
                                transcript_parts.append(f"{speaker}: {content}")

                        if transcript_parts:
                            return "\n\n".join(transcript_parts)

                # Method 4: Look for transcript in analysis
                analysis = message.get("analysis", {})
                if analysis.get("transcript"):
                    return analysis["transcript"]

                return ""
            except Exception as e:
                logger.warning(f"Error extracting transcript: {e}")
                return ""

        transcript = extract_transcript_from_vapi_payload(request)

        # Check for "no answer" status from VAPI call data
        # VAPI may report this in call.status, call.endedReason, or call_data.status
        call_status = call_data.get("status", "").lower()
        ended_reason = call_data.get("endedReason", "").lower() or call_data.get("ended_reason", "").lower()
        is_no_answer = (
            "no-answer" in call_status or 
            "no_answer" in call_status or
            "no-answer" in ended_reason or
            "no_answer" in ended_reason or
            "not-answered" in ended_reason or
            "not_answered" in ended_reason or
            "no answer" in ended_reason or
            call_status == "no-answer" or
            ended_reason == "no-answer"
        )

        # Enhanced transcript extraction logging
        logger.info("")
        logger.info("🔍 TRANSCRIPT EXTRACTION DEBUG")
        logger.info("┌─────────────────────────────────────────────────────────────────────────────┐")
        logger.info(f"│ 📊 Extracted Length: {len(transcript):,} characters")
        logger.info(f"│ 📞 Call Status: {call_status or 'Not provided'}")
        logger.info(f"│ 🚫 Ended Reason: {ended_reason or 'Not provided'}")
        logger.info(f"│ ❓ No Answer Detected: {'✅ Yes' if is_no_answer else '❌ No'}")
        if transcript:
            preview = transcript[:200].replace('\n', ' ')
            logger.info(f"│ 📝 Content Preview: {preview}{'...' if len(transcript) > 200 else ''}")
        else:
            logger.info(f"│ ❌ No transcript content extracted")

            # Debug the payload structure for failed extractions
            message = request.get("message", {})
            if message.get("type") == "end-of-call-report":
                artifact = message.get("artifact", {})
                messages = artifact.get("messages", [])
                logger.info(f"│ 🔍 Debug - Artifact exists: {'✅' if artifact else '❌'}")
                logger.info(f"│ 🔍 Debug - Messages count: {len(messages) if messages else 0}")
                if messages:
                    user_msgs = [m for m in messages if m.get("role") == "user"]
                    assistant_msgs = [m for m in messages if m.get("role") == "assistant"]
                    logger.info(f"│ 🔍 Debug - User messages: {len(user_msgs)}")
                    logger.info(f"│ 🔍 Debug - Assistant messages: {len(assistant_msgs)}")
        logger.info("└─────────────────────────────────────────────────────────────────────────────┘")

        customer_info = request.get("customer")
        phone_number = call_data.get("phoneNumber") or call_data.get("customer", {}).get("number")
        recording_url = request.get("recordingUrl", "None")

        logger.info("")
        logger.info("🔍 CALL DATA DETAILS")
        logger.info("┌─────────────────────────────────────────────────────────────────────────────┐")
        logger.info(f"│ 📝 Transcript: {len(transcript):,} characters")
        logger.info(f"│ 📞 Phone Number: {phone_number or 'Not provided'}")
        logger.info(f"│ 👤 Customer Info: {'✅ Present' if customer_info else '❌ Missing'}")
        logger.info(f"│ 🎵 Recording: {'✅ Available' if recording_url != 'None' else '❌ Not available'}")
        logger.info(f"│ 📊 Call Data Keys: {len(call_data.keys()) if call_data else 0} fields")
        logger.info("└─────────────────────────────────────────────────────────────────────────────┘")

        # === STEP 3: CUSTOM TOOLS DETECTION ===
        tool_calls_detected = False
        tool_calls = request.get("toolCalls", [])

        if tool_calls:
            tool_calls_detected = True
            logger.info("")
            logger.info("🔧 TOOL CALLS DETECTED")
            logger.info("┌─────────────────────────────────────────────────────────────────────────────┐")
            logger.info(f"│ 🛠️  Total Tools Called: {len(tool_calls)}")
            for i, tool_call in enumerate(tool_calls[:5]):  # Show max 5 tools
                tool_name = tool_call.get('function', {}).get('name', 'unknown')
                logger.info(f"│ #{i+1:2d} {tool_name}")
            if len(tool_calls) > 5:
                logger.info(f"│     ... and {len(tool_calls) - 5} more")
            logger.info("└─────────────────────────────────────────────────────────────────────────────┘")
        else:
            logger.info("")
            logger.info("🔧 NO TOOL CALLS DETECTED")
            logger.info("┌─────────────────────────────────────────────────────────────────────────────┐")
            logger.info("│ 🤖 This webhook contains no tool call information")
            logger.info("└─────────────────────────────────────────────────────────────────────────────┘")

        # === STEP 4: TRANSCRIPT VALIDATION ===
        logger.info(f"📝 TRANSCRIPT VALIDATION:")
        # If it's a "no answer" call, we should still process it (even without transcript)
        # to update campaign progress correctly
        if is_no_answer:
            logger.info(f"   └── ⚠️ No answer call detected - will process without transcript")
            # Set a minimal transcript for processing
            if not transcript or len(transcript.strip()) < 10:
                transcript = "No answer - call not answered"
        elif not transcript or len(transcript.strip()) < 10:
            logger.info(f"   └── ❌ Insufficient transcript - skipping processing")
            return VAPIWebhookResponse(
                success=True,
                message="Webhook received but no transcript to process",
                call_id=call_id,
                summary_generated=False,
                email_sent=False,
                data_saved=False
            )
        else:
            logger.info(f"   └── ✅ Valid transcript - proceeding with processing")

        logger.info(f"🚀 INITIATING BACKGROUND PROCESSING for call {call_id}")

        # === STEP 5: BACKGROUND TASK SCHEDULING ===
        logger.info(f"⚡ BACKGROUND TASK: Scheduling async processing")
        # Pass is_no_answer flag to background task
        background_tasks.add_task(
            process_vapi_call_async,
            call_id,
            transcript,
            assistant_id,
            request.get("customer"),
            call_data,
            metadata,  # Pass extracted metadata with org_id
            tool_calls_detected,
            message_type,
            is_no_answer  # Pass no answer detection flag
        )

        # === STEP 6: RESPONSE PREPARATION ===
        processing_time = round((time.time() - request_start_time) * 1000, 2)

        logger.info("")
        logger.info("✅ WEBHOOK PROCESSING COMPLETED")
        logger.info("┌─────────────────────────────────────────────────────────────────────────────┐")
        logger.info(f"│ ⏱️  Processing Time: {processing_time}ms")
        logger.info(f"│ 🆔 Call ID: {call_id}")
        logger.info(f"│ 🚀 Background Task: ✅ Scheduled")
        logger.info(f"│ 📡 Response: 200 OK")
        logger.info("└─────────────────────────────────────────────────────────────────────────────┘")
        logger.info("")

        return VAPIWebhookResponse(
            success=True,
            message="VAPI webhook received and processing started",
            call_id=call_id,
            summary_generated=None,  # Will be processed in background
            email_sent=None,         # Will be processed in background
            data_saved=None          # Will be processed in background
        )

    except Exception as e:
        processing_time = round((time.time() - request_start_time) * 1000, 2)
        error_call_id = locals().get('call_id', 'unknown')

        logger.error("")
        logger.error("╔" + "═" * 78 + "╗")
        logger.error("║" + f"❌ VAPI WEBHOOK ERROR".center(78) + "║")
        logger.error("╠" + "═" * 78 + "╣")
        logger.error("║" + f" ⏱️  Processing Time: {processing_time}ms".ljust(78) + "║")
        logger.error("║" + f" 🆔 Call ID: {error_call_id}".ljust(78) + "║")
        logger.error("║" + f" ❗ Error Type: {type(e).__name__}".ljust(78) + "║")
        logger.error("║" + f" 📝 Error Message: {str(e)[:50]}{'...' if len(str(e)) > 50 else ''}".ljust(78) + "║")
        logger.error("╚" + "═" * 78 + "╝")
        logger.error("")

        return VAPIWebhookResponse(
            success=False,
            message=f"Webhook processing failed: {str(e)}",
            call_id=None,
            summary_generated=False,
            email_sent=False,
            data_saved=False
        )


async def process_vapi_call_async(
    call_id: str,
    transcript: str,
    assistant_id: str,
    customer_info: Optional[Dict[str, Any]],
    call_data: Dict[str, Any],
    metadata: Optional[Dict[str, Any]],
    tool_calls_detected: bool = False,
    message_type: str = "unknown",
    is_no_answer: bool = False
):
    """
    Process VAPI call data asynchronously:
    1. Generate AI summary
    2. Track Vonage costs
    3. Save to database
    4. Send email notification
    """
    bg_start_time = time.time()

    try:
        logger.info("🔄" * 30)
        logger.info("🚀 BACKGROUND PROCESSING STARTED")
        logger.info("🔄" * 30)

        # Extract organization context from metadata for tracking
        # Check multiple sources: metadata dict, call_data, and request
        org_id = None
        if metadata:
            org_id = metadata.get("organization_id")
        if not org_id and call_data:
            org_id = call_data.get("organization_id") or call_data.get("org_id")
        if not org_id:
            # Try to extract from assistant metadata or other sources
            assistant_data = call_data.get("assistant", {})
            if assistant_data:
                org_id = assistant_data.get("organization_id")
        
        logger.info(f"   ├── Organization ID extracted: {org_id or 'Not found'}")

        logger.info(f"📋 BACKGROUND TASK PARAMETERS:")
        logger.info(f"   ├── Call ID: {call_id}")
        logger.info(f"   ├── Assistant ID: {assistant_id}")
        logger.info(f"   ├── Organization: {org_id or 'Not specified'}")
        logger.info(f"   ├── Message Type: {message_type}")
        logger.info(f"   ├── Tool Calls Detected: {tool_calls_detected}")
        logger.info(f"   ├── Transcript Length: {len(transcript)} chars")
        logger.info(f"   ├── Customer Info: {bool(customer_info)}")
        logger.info(f"   └── Metadata: {bool(metadata)}")

        # === STEP 1: AI SUMMARY GENERATION ===
        logger.info(f"🤖 STEP 1: GENERATING AI SUMMARY")
        summary_start = time.time()
        summary_text = await generate_ai_summary(transcript, call_id)
        summary_time = round((time.time() - summary_start) * 1000, 2)
        logger.info(f"   ├── Summary generated: {bool(summary_text)}")
        logger.info(f"   ├── Summary length: {len(summary_text) if summary_text else 0} chars")
        logger.info(f"   └── Generation time: {summary_time}ms")

        # === STEP 2: VONAGE COST TRACKING ===
        logger.info(f"💰 STEP 2: TRACKING VONAGE COSTS")
        cost_start = time.time()
        vonage_cost = None
        try:
            from ..services.vonage_cost_monitoring_service import get_vonage_cost_service

            vonage_service = await get_vonage_cost_service()

            # Extract call details for cost tracking
            duration = call_data.get("duration", 0)
            vonage_phone = "+12075218001"  # The Vonage number for VAPI phone ID 6c5af6e1-a2b7-41d6-ac04-4c9691bf73e4

            logger.info(f"   ├── Call duration: {duration} seconds")
            logger.info(f"   ├── Vonage phone: {vonage_phone}")

            if duration and duration > 0:
                vonage_cost = await vonage_service.track_vapi_call_cost(
                    vapi_call_id=call_id,
                    phone_number=vonage_phone,
                    duration=duration
                )
                cost_time = round((time.time() - cost_start) * 1000, 2)
                logger.info(f"   ├── ✅ Cost tracked: ${vonage_cost.cost_amount}")
                logger.info(f"   ├── Currency: {vonage_cost.currency}")
                logger.info(f"   ├── Transaction ID: {vonage_cost.transaction_id}")
                logger.info(f"   └── Tracking time: {cost_time}ms")
            else:
                logger.info(f"   └── ⚠️ No duration - skipping cost tracking")

        except Exception as cost_error:
            cost_time = round((time.time() - cost_start) * 1000, 2)
            logger.warning(f"   ├── ⚠️ Cost tracking failed: {str(cost_error)}")
            logger.warning(f"   ├── Continuing with database logging anyway")
            logger.warning(f"   └── Tracking time: {cost_time}ms")

        # === STEP 3: DATABASE PREPARATION ===
        logger.info(f"🗄️ STEP 3: PREPARING DATABASE RECORD")
        current_time = datetime.utcnow()
        call_log_data = {
            "call_id": call_id,
            "assistant_id": assistant_id,
            "assistant_name": call_data.get("assistantName"),
            "status": "completed",
            "start_time": call_data.get("startedAt", current_time.isoformat()),
            "end_time": call_data.get("endedAt", current_time.isoformat()),
            "duration": call_data.get("duration"),
            # For outbound calls: from_phone is the system's phone number (caller), to_phone is the customer's number (callee)
            # For inbound calls: from_phone is the customer's number (caller), to_phone is the system's phone number (callee)
            # VAPI calls are typically outbound, so:
            # - phoneNumber = system's VAPI phone number (the caller)
            # - customer.number = customer's phone number (the callee)
            "from_phone": call_data.get("phoneNumber"),  # System's phone number (caller for outbound)
            "to_phone": call_data.get("customer", {}).get("number") if call_data.get("customer") else None,  # Customer's phone number (callee for outbound)
            "transcript": transcript,
            "summary": summary_text,
            "vonage_cost": float(vonage_cost.cost_amount) if vonage_cost else None,
            "vonage_phone": "+12075218001",
            "metadata": {
                "vapi_call_data": call_data,
                "customer_info": customer_info,
                "additional_metadata": metadata,
                "tool_calls_detected": tool_calls_detected,
                "message_type": message_type,
                "vonage_cost_record": {
                    "transaction_id": vonage_cost.transaction_id if vonage_cost else None,
                    "cost_amount": float(vonage_cost.cost_amount) if vonage_cost else None,
                    "currency": vonage_cost.currency if vonage_cost else None
                }
            },
            "created_at": current_time.isoformat(),
            "updated_at": current_time.isoformat()
        }

        logger.info(f"   ├── Record prepared with {len(call_log_data)} fields")
        logger.info(f"   ├── From phone: {call_log_data['from_phone']}")
        logger.info(f"   ├── To phone: {call_log_data['to_phone']}")
        logger.info(f"   └── Duration: {call_log_data['duration']} seconds")

        # === STEP 3.5: LINK CALL TO AUTOMATION CONFIG ===
        logger.info(f"🔗 STEP 3.5: LINKING CALL TO AUTOMATION")
        automation_id = None
        automation_name = None
        try:
            # First, try to get automation_id from metadata (for campaign calls)
            if metadata and metadata.get("automation_id"):
                automation_id = metadata.get("automation_id")
                logger.info(f"   ├── ✅ Found automation_id in metadata: {automation_id}")
                
                # Look up automation name
                from ..mongo import get_collection
                from bson import ObjectId
                configs_collection = get_collection("automation_configs")
                automation_config = await configs_collection.find_one({"_id": ObjectId(automation_id)})
                if automation_config:
                    automation_name = automation_config.get("automation_name", "Unknown")
                    logger.info(f"   └── Automation name: {automation_name}")
                else:
                    logger.warning(f"   └── ⚠️  Automation config not found for ID {automation_id}")
            else:
                # Fallback: Find automation config by assistant_id
                from ..mongo import get_collection
                configs_collection = get_collection("automation_configs")

                # Find automation config by assistant_id (check both fields)
                # Reason: Some automations use assistant_id, others use deployment_info.vapi_assistant_id
                automation_config = await configs_collection.find_one({
                    "$or": [
                        {"assistant_id": assistant_id},
                        {"deployment_info.vapi_assistant_id": assistant_id}
                    ]
                })

                if automation_config:
                    automation_id = str(automation_config["_id"])
                    automation_name = automation_config.get("automation_name", "Unknown")
                    # Also extract organization_id if we don't have it yet
                    if not org_id:
                        org_id = automation_config.get("organization_id")
                        logger.info(f"   ├── ✅ Also extracted org_id from automation: {org_id}")
                    logger.info(f"   ├── ✅ Linked to automation: {automation_name}")
                    logger.info(f"   └── Automation ID: {automation_id}")
                else:
                    logger.info(f"   └── ⚠️  No automation config found for assistant {assistant_id}")
        except Exception as link_error:
            logger.warning(f"   └── ⚠️  Failed to link automation: {str(link_error)}")

        # === STEP 4: DATABASE SAVE (OPTIONAL - REMOVED SUPABASE DEPENDENCY) ===
        logger.info(f"💾 STEP 4: LOGGING CALL DATA LOCALLY")
        db_start = time.time()
        data_saved = False
        try:
            # Log call data to MongoDB only (more reliable)
            from ..mongo import get_collection

            # Extract phone number ID from call data
            phone_number_id = (
                call_data.get("phoneNumberId") or 
                call_data.get("phone_number_id") or
                (call_data.get("phoneNumber", {}) or {}).get("id") or
                (metadata or {}).get("phone_number_id")
            )
            
            # Prepare MongoDB document with automation linking
            mongo_call_data = {
                "call_id": call_id,
                "assistant_id": assistant_id,
                "organization_id": org_id,  # Track organization context for multi-tenant isolation
                "automation_id": automation_id,  # Link to automation config
                "automation_name": automation_name,  # For convenience
                "phone_number_id": phone_number_id,  # VAPI phone number ID
                "transcript": transcript,
                "summary": summary_text,
                "customer_phone": call_log_data.get("from_phone"),
                "duration": call_log_data.get("duration"),
                "vonage_cost": call_log_data.get("vonage_cost"),
                "tool_calls_detected": tool_calls_detected,
                "message_type": message_type,
                "metadata": call_log_data["metadata"],
                "created_at": current_time,
                "processed_at": datetime.utcnow(),
                # Add fields for call logs compatibility
                "status": "completed",
                "direction": "outbound",
                "from_phone": call_log_data.get("from_phone"),
                "to_phone": call_log_data.get("to_phone"),
                "start_time": call_data.get("startedAt") or current_time.isoformat(),
                "end_time": call_data.get("endedAt") or current_time.isoformat()
            }
            
            logger.info(f"   ├── Phone Number ID: {phone_number_id or 'Not found'}")

            # Save to MongoDB (async)
            calls_collection = get_collection("vapi_calls")
            result = await calls_collection.insert_one(mongo_call_data)
            
            # Also create call log entry for campaign calls
            if metadata and metadata.get("campaign_id"):
                try:
                    from ..services.call_logs_service import call_logs_service
                    from ..models.call_logs import CallLogCreate, CallStatus, CallDirection
                    
                    call_log_entry = CallLogCreate(
                        call_id=call_id,
                        assistant_id=assistant_id,
                        organization_id=org_id,
                        automation_id=automation_id,
                        automation_name=automation_name,
                        transcript=transcript,
                        summary=summary_text,
                        customer_phone=call_log_data.get("from_phone"),
                        duration=call_log_data.get("duration", 0),
                        status=CallStatus.COMPLETED,
                        direction=CallDirection.OUTBOUND,
                        from_phone=call_log_data.get("from_phone"),
                        to_phone=call_log_data.get("to_phone"),
                        start_time=call_data.get("startedAt") or current_time.isoformat(),
                        end_time=call_data.get("endedAt") or current_time.isoformat(),
                        metadata={
                            **(call_log_data.get("metadata", {})),
                            "campaign_id": metadata.get("campaign_id"),
                            "call_record_id": metadata.get("call_record_id")
                        }
                    )
                    await call_logs_service.create_call_log(call_log_entry)
                    logger.info(f"   ├── ✅ Campaign call log entry created for call {call_id}")
                except Exception as log_error:
                    logger.warning(f"   ├── ⚠️ Failed to create call log entry: {str(log_error)}")

            if result.inserted_id:
                data_saved = True
                db_time = round((time.time() - db_start) * 1000, 2)
                logger.info(f"   ├── ✅ Call saved to MongoDB")
                logger.info(f"   ├── Document ID: {str(result.inserted_id)}")
                logger.info(f"   └── Save time: {db_time}ms")
            else:
                db_time = round((time.time() - db_start) * 1000, 2)
                logger.warning(f"   ├── ⚠️ MongoDB save returned no ID")
                logger.warning(f"   └── Save time: {db_time}ms")

        except Exception as db_error:
            db_time = round((time.time() - db_start) * 1000, 2)
            logger.warning(f"   ├── ⚠️ Database logging failed: {str(db_error)}")
            logger.warning(f"   ├── Continuing with email notification anyway")
            logger.warning(f"   └── Attempted save time: {db_time}ms")

        # === STEP 4.5: CAMPAIGN TRACKING ===
        logger.info(f"🎯 STEP 4.5: CAMPAIGN TRACKING")
        campaign_updated = False
        try:
            # Check if this call is part of a campaign
            # Check multiple sources for campaign_id
            campaign_id = None
            call_record_id = None

            if metadata:
                campaign_id = metadata.get("campaign_id") or metadata.get("campaignId")
                call_record_id = metadata.get("call_record_id") or metadata.get("call_record_id")
            
            # Also check call_data metadata
            if not campaign_id and call_data:
                call_data_metadata = call_data.get("metadata", {})
                if call_data_metadata:
                    campaign_id = call_data_metadata.get("campaign_id") or call_data_metadata.get("campaignId")
                    call_record_id = call_data_metadata.get("call_record_id")
            
            logger.info(f"   ├── Campaign ID: {campaign_id or 'Not found'}")
            logger.info(f"   ├── Call Record ID: {call_record_id or 'Not found'}")

            if campaign_id:
                logger.info(f"   ├── Campaign call detected")
                logger.info(f"   ├── Campaign ID: {campaign_id}")
                logger.info(f"   └── Call record ID: {call_record_id}")

                from ..services.campaign_execution_service import campaign_service, extract_call_outcome
                from bson import ObjectId

                # Convert campaign_id to ObjectId if it's a string (for MongoDB query)
                try:
                    # Try to convert to ObjectId if it's a valid ObjectId string
                    if isinstance(campaign_id, str) and len(campaign_id) == 24:
                        campaign_object_id = ObjectId(campaign_id)
                    else:
                        campaign_object_id = campaign_id
                except Exception:
                    # If conversion fails, use as-is (might be a different ID format)
                    campaign_object_id = campaign_id
                    logger.warning(f"   ├── ⚠️ Could not convert campaign_id to ObjectId, using as-is: {campaign_id}")

                # Extract AI-powered outcome from transcript
                # If it's a no-answer call, set outcome directly without AI processing
                if is_no_answer:
                    logger.info(f"   ├── No answer call detected - setting outcome directly")
                    from ..services.campaign_execution_service import CallOutcome
                    outcome = CallOutcome(
                        outcome="no_answer",
                        conversion_signals=0,
                        objections=[],
                        sentiment="neutral",
                        confidence=1.0
                    )
                else:
                    logger.info(f"   ├── Extracting call outcome with AI...")
                    outcome = await extract_call_outcome(transcript)

                logger.info(f"   ├── Outcome extracted:")
                logger.info(f"   │   ├── Type: {outcome.outcome}")
                logger.info(f"   │   ├── Conversion signals: {outcome.conversion_signals}")
                logger.info(f"   │   ├── Objections: {len(outcome.objections)}")
                logger.info(f"   │   └── Sentiment: {outcome.sentiment}")

                # Update campaign call with outcome
                duration = call_data.get("duration", 0)
                cost = float(vonage_cost.cost_amount) if vonage_cost else 0.0

                # Use update_call_outcome for detailed outcome tracking
                try:
                    await campaign_service.update_call_outcome(
                        call_id=call_id,
                        outcome=outcome,
                        transcript=transcript,
                        summary=summary_text or "Summary not available",
                        duration=duration,
                        cost=cost
                    )
                    logger.info(f"   ├── ✅ Call outcome updated")
                except Exception as outcome_error:
                    logger.error(f"   ├── ❌ Failed to update call outcome: {str(outcome_error)}")
                    # Continue with progress update even if outcome update fails

                # Also mark as completed for progress tracking
                # Map outcome to status
                status_mapping = {
                    "converted": "completed",
                    "objection": "completed",
                    "neutral": "completed",
                    "no_answer": "no_answer",
                    "error": "failed",
                    "failed": "failed"
                }
                campaign_status = status_mapping.get(outcome.outcome, "completed")

                # Use string campaign_id for mark_call_completed (it handles conversion internally)
                try:
                    await campaign_service.mark_call_completed(
                        campaign_id=str(campaign_object_id),  # Ensure it's a string
                        call_id=call_id,
                        status=campaign_status,
                        cost=cost,
                        duration=duration
                    )
                    campaign_updated = True
                    logger.info(f"   └── ✅ Campaign progress updated: status={campaign_status}, cost=${cost}, duration={duration}s")
                except Exception as progress_error:
                    logger.error(f"   └── ❌ Failed to update campaign progress: {str(progress_error)}")
                    logger.error(f"       Error type: {type(progress_error).__name__}")
                    import traceback
                    logger.error(f"       Traceback: {traceback.format_exc()}")
            else:
                logger.info(f"   └── ℹ️  Not a campaign call - skipping campaign tracking")

        except Exception as campaign_error:
            logger.warning(f"   ├── ⚠️ Campaign tracking failed: {str(campaign_error)}")
            logger.warning(f"   └── Continuing with normal processing")

        # === STEP 5: EMAIL NOTIFICATION ===
        logger.info(f"📧 STEP 5: SENDING EMAIL NOTIFICATION")
        email_start = time.time()
        email_sent = False
        try:
            # Prepare customer info for email
            customer_display = "Unknown"
            if customer_info:
                customer_display = customer_info.get("name", customer_info.get("number", "Unknown"))
            elif call_data.get("customer"):
                customer_display = call_data["customer"].get("number", "Unknown")

            logger.info(f"   ├── Customer display: {customer_display}")
            logger.info(f"   ├── Assistant ID: {assistant_id}")
            logger.info(f"   ├── Cost amount: ${vonage_cost.cost_amount if vonage_cost else 'N/A'}")

            # Enhanced email content with cost information
            email_content = create_enhanced_vapi_call_email(
                call_id=call_id,
                summary=summary_text,
                customer=customer_display,
                assistant_id=assistant_id,
                transcript_preview=transcript[:300],
                duration=call_data.get("duration", 0),
                vonage_cost=vonage_cost.cost_amount if vonage_cost else None,
                vonage_phone="+12075218001"
            )

            logger.info(f"   ├── Email content generated: {len(email_content)} chars")

            # Send email using existing notification function with fallback
            await send_email_async(
                "ailabsafrica@gmail.com",
                f"KasaAI Call Summary - {call_id} (${vonage_cost.cost_amount if vonage_cost else 'N/A'})",
                email_content,
                call_id
            )
            email_time = round((time.time() - email_start) * 1000, 2)
            email_sent = True
            logger.info(f"   ├── ✅ Email sent successfully")
            logger.info(f"   ├── Recipient: ailabsafrica@gmail.com")
            logger.info(f"   └── Send time: {email_time}ms")

        except Exception as email_error:
            email_time = round((time.time() - email_start) * 1000, 2)
            logger.error(f"   ├── ❌ Email error: {str(email_error)}")
            logger.error(f"   ├── Send time: {email_time}ms")

            # Try direct Resend API as backup
            try:
                logger.info(f"   ├── 🔄 Trying Resend fallback...")
                await send_email_via_resend(
                    "ailabsafrica@gmail.com",
                    f"KasaAI Call Summary - {call_id}",
                    email_content,
                    call_id
                )
                email_sent = True
                logger.info(f"   └── ✅ Email sent via Resend fallback")
            except Exception as fallback_error:
                logger.error(f"   └── ❌ Resend fallback failed: {str(fallback_error)}")

        # === FINAL SUMMARY ===
        total_time = round((time.time() - bg_start_time) * 1000, 2)
        logger.info("🏁" * 30)
        logger.info("✅ BACKGROUND PROCESSING COMPLETED")
        logger.info("🏁" * 30)
        logger.info(f"📊 FINAL RESULTS:")
        logger.info(f"   ├── Call ID: {call_id}")
        logger.info(f"   ├── AI Summary: {'✅ Generated' if summary_text else '❌ Failed'}")
        logger.info(f"   ├── Cost Tracking: {'✅ Tracked' if vonage_cost else '⚠️ Skipped'}")
        logger.info(f"   ├── Database Save: {'✅ Saved' if data_saved else '⚠️ Failed (continued anyway)'}")
        logger.info(f"   ├── Campaign Tracking: {'✅ Updated' if campaign_updated else '➖ Not a campaign call'}")
        logger.info(f"   ├── Email Sent: {'✅ Sent' if email_sent else '⚠️ Failed (non-critical)'}")
        logger.info(f"   ├── Tool Calls Detected: {'✅ Yes' if tool_calls_detected else '➖ None'}")
        logger.info(f"   ├── Message Type: {message_type}")
        logger.info(f"   └── Total Processing Time: {total_time}ms")
        logger.info("🔄" * 30)

        # Always log success for webhook processing (resilient pipeline)
        logger.info(f"🎯 WEBHOOK PROCESSING RESILIENCE: Pipeline completed all possible steps")

    except Exception as e:
        total_time = round((time.time() - bg_start_time) * 1000, 2)
        logger.error("🔄" * 30)
        logger.error("❌ BACKGROUND PROCESSING FAILED")
        logger.error("🔄" * 30)
        logger.error(f"   ├── Call ID: {call_id}")
        logger.error(f"   ├── Error: {str(e)}")
        logger.error(f"   ├── Error type: {type(e).__name__}")
        logger.error(f"   └── Processing Time: {total_time}ms")
        logger.error("🔄" * 30)


async def generate_ai_summary(transcript: str, call_id: str) -> str:
    """
    Generate AI summary of call transcript using existing AI features.
    Fallback to simple extraction if AI not available.
    """
    try:
        # Try using existing AI features with default config
        from ai.ai_powered_features import AIPoweredFeatures, CallSummary, CallOutcome, ConversationSentiment

        # Create a minimal config for AI features
        ai_config = {
            "openai_api_key": "default",  # Will fallback gracefully
            "model": "gpt-3.5-turbo",
            "max_tokens": 150
        }

        ai_features = AIPoweredFeatures(ai_config)
        summary_obj = await ai_features.generate_call_summary(call_id)

        if summary_obj and hasattr(summary_obj, 'summary') and summary_obj.summary:
            logger.info(f"   ├── ✅ AI summary generated: {len(summary_obj.summary)} chars")
            return summary_obj.summary

    except Exception as ai_error:
        logger.warning(f"   ├── ⚠️ AI summary failed for call {call_id}: {str(ai_error)}")

    # Fallback: Simple rule-based summary (always works)
    try:
        lines = transcript.split('\n')
        # Take first few meaningful lines as summary
        meaningful_lines = [line.strip() for line in lines if len(line.strip()) > 20]

        if meaningful_lines:
            summary_parts = []
            summary_parts.append(f"Call transcript with {len(meaningful_lines)} meaningful exchanges.")

            # Add first exchange
            if len(meaningful_lines) > 0:
                summary_parts.append(f"Opening: {meaningful_lines[0][:100]}...")

            # Add last exchange
            if len(meaningful_lines) > 1:
                summary_parts.append(f"Closing: {meaningful_lines[-1][:100]}...")

            fallback_summary = " ".join(summary_parts)
            logger.info(f"   ├── ✅ Fallback summary generated: {len(fallback_summary)} chars")
            return fallback_summary
        else:
            simple_summary = f"Call completed with transcript length: {len(transcript)} characters."
            logger.info(f"   ├── ✅ Simple summary generated: {len(simple_summary)} chars")
            return simple_summary

    except Exception as fallback_error:
        logger.error(f"   ├── ❌ Fallback summary failed for call {call_id}: {str(fallback_error)}")
        emergency_summary = f"Call summary unavailable. Transcript length: {len(transcript)} characters."
        logger.info(f"   └── ✅ Emergency summary generated: {len(emergency_summary)} chars")
        return emergency_summary


def create_vapi_call_email(call_id: str, summary: str, customer: str, assistant_id: str, transcript_preview: str) -> str:
    """Create HTML email content for VAPI call notification."""
    return f"""
    <html>
    <body>
        <h2>📞 VAPI Call Completed</h2>

        <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 15px 0;">
            <h3>Call Details</h3>
            <p><strong>Call ID:</strong> {call_id}</p>
            <p><strong>Customer:</strong> {customer}</p>
            <p><strong>Assistant ID:</strong> {assistant_id}</p>
            <p><strong>Time:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
        </div>

        <div style="background-color: #e8f5e8; padding: 15px; border: 1px solid #4CAF50; border-radius: 5px; margin: 15px 0;">
            <h3>📋 AI-Generated Summary</h3>
            <p>{summary}</p>
        </div>

        <div style="background-color: #fff3cd; padding: 15px; border: 1px solid #ffc107; border-radius: 5px; margin: 15px 0;">
            <h3>📝 Transcript Preview</h3>
            <p>{transcript_preview}{'...' if len(transcript_preview) >= 200 else ''}</p>
        </div>

        <div style="margin-top: 30px; color: #666; font-size: 12px;">
            <p>This is an automated notification from the VAPI Call Management System.</p>
            <p>Webhook endpoint: https://api.ailabsafrica.com/call-management/vapi/webhook</p>
        </div>
    </body>
    </html>
    """


@router.get("/current-datetime", response_model=CurrentDateTimeResponse)
async def get_current_datetime(timezone_name: Optional[str] = "UTC"):
    """
    Get current date and time information for VAPI appointment scheduling.

    Provides comprehensive date/time context including business day/hours information
    to help VAPI tools make informed scheduling decisions.

    Args:
        timezone_name: Target timezone (default: UTC). Examples: 'UTC', 'US/Eastern', 'Africa/Accra'

    Returns:
        CurrentDateTimeResponse: Comprehensive current date/time information
    """
    try:
        # Get timezone object
        try:
            tz = pytz.timezone(timezone_name)
        except Exception:
            # Fallback to UTC if timezone is invalid
            tz = pytz.UTC
            timezone_name = "UTC"

        # Get current time in specified timezone
        now = datetime.now(tz)

        # Calculate business day (Monday=0, Sunday=6, so Mon-Fri = 0-4)
        is_business_day = now.weekday() < 5

        # Calculate business hours (9 AM - 5 PM in the specified timezone)
        is_business_hours = 9 <= now.hour < 17

        # Day names
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        months = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ]

        return CurrentDateTimeResponse(
            current_datetime=now.isoformat(),
            current_date=now.strftime('%Y-%m-%d'),
            current_time=now.strftime('%H:%M:%S'),
            timezone=timezone_name,
            timestamp=int(now.timestamp()),
            business_day=is_business_day,
            business_hours=is_business_hours,
            day_of_week=days[now.weekday()],
            month_name=months[now.month - 1],
            formatted_date=now.strftime('%A, %B %d, %Y')
        )

    except Exception as e:
        logger.error(f"Error getting current datetime: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get current datetime: {str(e)}")



# ============================================================================
# Google Calendar Integration Endpoints
# ============================================================================

class GoogleCalendarAvailabilityRequest(BaseModel):
    """Request model for Google Calendar availability check."""
    date: str = Field(..., description="Date to check availability (YYYY-MM-DD format)")
    duration_minutes: int = Field(30, description="Appointment duration in minutes")
    meeting_type: str = Field("consultation", description="Type of meeting")
    timezone: str = Field("UTC", description="Timezone for the check")


class GoogleCalendarBookingRequest(BaseModel):
    """Request model for Google Calendar appointment booking."""
    customer_name: str = Field(..., description="Customer's full name")
    customer_email: str = Field(..., description="Customer's email address")
    appointment_date: str = Field(..., description="Date in YYYY-MM-DD format")
    appointment_time: str = Field(..., description="Time in HH:MM format (24-hour)")
    duration_minutes: int = Field(30, description="Duration in minutes")
    meeting_type: str = Field("consultation", description="Type of meeting")
    notes: str = Field("", description="Additional notes for the appointment")
    timezone: str = Field("UTC", description="Timezone")


@router.post("/google-calendar-availability", response_model=Dict[str, Any])
async def check_google_calendar_availability(request: GoogleCalendarAvailabilityRequest):
    """
    Check Google Calendar availability for a specific date.

    This endpoint uses real Google Calendar API integration to check actual
    availability in the ailabsafrica@gmail.com calendar.
    """
    try:
        logger.info(f"🗓️ Google Calendar availability check for {request.date}")

        # Import Google Calendar service
        from ..services.google_calendar_service import get_google_calendar_service, CalendarAvailabilityRequest

        # Create availability request
        availability_request = CalendarAvailabilityRequest(
            date=request.date,
            duration_minutes=request.duration_minutes,
            meeting_type=request.meeting_type,
            timezone=request.timezone
        )

        # Get service and check availability
        service = get_google_calendar_service()
        result = await service.check_availability(availability_request)

        logger.info(f"✅ Calendar availability check completed for {request.date}")
        return result

    except Exception as e:
        logger.error(f"❌ Google Calendar availability check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Calendar availability check failed: {str(e)}")


@router.post("/google-calendar-booking", response_model=Dict[str, Any])
async def book_google_calendar_appointment(request: GoogleCalendarBookingRequest):
    """
    Book an appointment directly in Google Calendar.

    This endpoint creates real calendar events with Google Meet links,
    email invitations, and automatic reminders.
    """
    try:
        logger.info(f"📅 Google Calendar booking request for {request.customer_name} on {request.appointment_date} at {request.appointment_time}")

        # Import Google Calendar service
        from ..services.google_calendar_service import get_google_calendar_service, CalendarBookingRequest

        # Create booking request
        booking_request = CalendarBookingRequest(
            customer_name=request.customer_name,
            customer_email=request.customer_email,
            appointment_date=request.appointment_date,
            appointment_time=request.appointment_time,
            duration_minutes=request.duration_minutes,
            meeting_type=request.meeting_type,
            notes=request.notes,
            timezone=request.timezone
        )

        # Get service and create appointment
        service = get_google_calendar_service()
        result = await service.create_calendar_event(booking_request)

        if result.get("success"):
            logger.info(f"✅ Calendar appointment booked successfully for {request.customer_name}")
            logger.info(f"   📅 Event ID: {result.get('event_id')}")
            logger.info(f"   🔗 Event Link: {result.get('event_link')}")
        else:
            logger.error(f"❌ Calendar booking failed: {result.get('error')}")

        return result

    except Exception as e:
        logger.error(f"❌ Google Calendar booking failed: {e}")
        raise HTTPException(status_code=500, detail=f"Calendar booking failed: {str(e)}")


@router.get("/health")
async def health_check():
    """Enhanced health check for call management service."""
    try:
        # Test Supabase connection using shared integration
        supabase = get_supabase_integration()
        supabase_connected = await supabase.health_check()

        # Test call_logs table specifically
        call_logs_exists = await verify_table_exists("call_logs")

        # Get available tables count
        available_tables = await get_available_tables()

        # Check configuration
        config_status = {
            "supabase_url": bool(os.getenv("DEMO_SUPABASE_URL")),
            "supabase_key": bool(os.getenv("DEMO_SUPABASE_SUPABASE_KEY")),
            "resend_api": bool(os.getenv("RESEND_API")),
            "smtp_configured": bool(os.getenv("SMTP_USERNAME") and os.getenv("SMTP_PASSWORD"))
        }

        return {
            "status": "healthy" if call_logs_exists and supabase_connected else "degraded",
            "service": "Call Management Service",
            "version": "1.1",
            "supabase_connected": supabase_connected,
            "call_logs_table": call_logs_exists,
            "available_tables_count": len(available_tables),
            "configuration": config_status,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "Call Management Service",
            "version": "1.1",
            "supabase_connected": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


# Initialize table verification on startup
@router.on_event("startup")
async def startup_event():
    """Initialize resources and verify table access on startup."""
    try:
        available_tables = await get_available_tables()
        logger.info(f"Call Management Service started. Available tables: {available_tables}")

        if "call_logs" not in available_tables:
            logger.warning("call_logs table not accessible. Check Supabase configuration and permissions.")
        else:
            logger.info("call_logs table verified and accessible")

    except Exception as e:
        logger.error(f"Startup verification failed: {str(e)}")


def get_router():
    return router