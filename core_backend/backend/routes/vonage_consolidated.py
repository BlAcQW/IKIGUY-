"""
Consolidated Vonage Routes
Uses the unified Vonage service for all SMS, Voice, and Number management operations.
"""

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks, Depends, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
import uuid
import json
from datetime import datetime
import logging

from ..auth import get_current_user_mongo
from ..services.vonage_consolidated_service import vonage_consolidated_service
from apps.shared.integration.vonage import VonageSMSMessage, VonageVoiceCall

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vonage-consolidated", tags=["Vonage Consolidated"])

# Request models
class VonageSMSRequest(BaseModel):
    """Request model for sending SMS via Vonage."""
    to: str = Field(..., description="Recipient phone number")
    from_: str = Field(..., alias="from", description="Sender phone number")
    text: str = Field(..., description="Message text")
    type: str = Field("text", description="Message type")
    client_ref: Optional[str] = Field(None, description="Client reference")
    webhook_url: Optional[str] = Field(None, description="Webhook callback URL")
    ttl: Optional[int] = Field(None, description="Time to live in milliseconds")
    message_class: Optional[int] = Field(None, description="Message class")
    tenant_id: str = Field("default", description="Tenant identifier")


class VonageVoiceCallRequest(BaseModel):
    """Request model for making voice calls via Vonage."""
    to: str = Field(..., description="Recipient phone number")
    from_: str = Field(..., alias="from", description="Caller phone number")
    answer_url: str = Field(..., description="Answer URL for NCCO")
    event_url: Optional[str] = Field(None, description="Event webhook URL")
    answer_method: str = Field("GET", description="Answer URL HTTP method")
    event_method: str = Field("POST", description="Event URL HTTP method")
    machine_detection: Optional[str] = Field(None, description="Machine detection setting")
    length_timer: Optional[int] = Field(None, description="Call length timer")
    ringing_timer: Optional[int] = Field(None, description="Ringing timer")
    tenant_id: str = Field("default", description="Tenant identifier")


class VonageNumberSearchRequest(BaseModel):
    """Request model for searching available numbers."""
    country: str = Field(..., description="Country code (e.g., 'US', 'GB')")
    type_: str = Field("mobile-lvn", alias="type", description="Number type")
    pattern: Optional[str] = Field(None, description="Number pattern to search")
    search_pattern: int = Field(0, description="Search pattern type")
    features: Optional[List[str]] = Field(None, description="Required features")
    size: int = Field(10, description="Number of results")
    index: int = Field(1, description="Start index")
    tenant_id: str = Field("default", description="Tenant identifier")


class VonageNumberManagementRequest(BaseModel):
    """Request model for number management operations."""
    operation: str = Field(..., description="Operation (search, buy, cancel, list)")
    country: str = Field(..., description="Country code")
    msisdn: Optional[str] = Field(None, description="Phone number (for buy/cancel)")
    search_params: Optional[Dict[str, Any]] = Field({}, description="Search parameters")
    tenant_id: str = Field("default", description="Tenant identifier")


class VonageTTSRequest(BaseModel):
    """Request model for text-to-speech in calls."""
    call_uuid: str = Field(..., description="Call UUID")
    text: str = Field(..., description="Text to speak")
    voice_name: str = Field("Amy", description="Voice name")
    language: str = Field("en-US", description="Language code")
    tenant_id: str = Field("default", description="Tenant identifier")


# SMS Routes
@router.post("/sms/send", response_model=Dict[str, Any])
async def send_sms_message(
    sms_request: VonageSMSRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Send SMS message using the consolidated Vonage service.
    """
    try:
        # Convert request to VonageSMSMessage
        message = VonageSMSMessage(
            to=sms_request.to,
            from_=sms_request.from_,
            text=sms_request.text,
            type=sms_request.type,
            client_ref=sms_request.client_ref,
            webhook_url=sms_request.webhook_url,
            ttl=sms_request.ttl,
            message_class=sms_request.message_class
        )

        result = await vonage_consolidated_service.send_tenant_sms(
            tenant_id=sms_request.tenant_id,
            message=message,
            context={
                "sent_by": current_user.get("user_id"),
                "sent_at": datetime.now().isoformat()
            }
        )

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))

        return {
            "success": True,
            "sms": result,
            "message": "SMS sent successfully via consolidated Vonage service"
        }

    except Exception as e:
        logger.error(f"Error sending SMS: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sms/pricing/{country}", response_model=Dict[str, Any])
async def get_sms_pricing(
    country: str,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Get SMS pricing for a country.
    """
    try:
        result = await vonage_consolidated_service.get_sms_pricing(country)

        if not result.success:
            raise HTTPException(status_code=400, detail=result.error)

        return {
            "success": True,
            "pricing": result.data,
            "country": country
        }

    except Exception as e:
        logger.error(f"Error getting SMS pricing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Voice Routes
@router.post("/voice/call", response_model=Dict[str, Any])
async def make_voice_call(
    call_request: VonageVoiceCallRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Make a voice call using the consolidated Vonage service.
    """
    try:
        # Convert request to VonageVoiceCall
        call = VonageVoiceCall(
            to=call_request.to,
            from_=call_request.from_,
            answer_url=call_request.answer_url,
            event_url=call_request.event_url,
            answer_method=call_request.answer_method,
            event_method=call_request.event_method,
            machine_detection=call_request.machine_detection,
            length_timer=call_request.length_timer,
            ringing_timer=call_request.ringing_timer
        )

        result = await vonage_consolidated_service.make_tenant_voice_call(
            tenant_id=call_request.tenant_id,
            call=call,
            context={
                "initiated_by": current_user.get("user_id"),
                "initiated_at": datetime.now().isoformat()
            }
        )

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))

        return {
            "success": True,
            "call": result,
            "message": "Voice call initiated successfully via consolidated Vonage service"
        }

    except Exception as e:
        logger.error(f"Error making voice call: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voice/call/{call_uuid}", response_model=Dict[str, Any])
async def get_call_details(
    call_uuid: str,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Get call details by UUID.
    """
    try:
        result = await vonage_consolidated_service.get_call_details(call_uuid)

        if not result.success:
            raise HTTPException(status_code=400, detail=result.error)

        return {
            "success": True,
            "call": result.data,
            "call_uuid": call_uuid
        }

    except Exception as e:
        logger.error(f"Error getting call details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/voice/call/{call_uuid}/hangup", response_model=Dict[str, Any])
async def hangup_call(
    call_uuid: str,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Hangup an active call.
    """
    try:
        result = await vonage_consolidated_service.hangup_call(call_uuid)

        if not result.success:
            raise HTTPException(status_code=400, detail=result.error)

        return {
            "success": True,
            "result": result.data,
            "call_uuid": call_uuid,
            "message": "Call hung up successfully"
        }

    except Exception as e:
        logger.error(f"Error hanging up call: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/voice/call/tts", response_model=Dict[str, Any])
async def play_tts_to_call(
    tts_request: VonageTTSRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Play text-to-speech to an active call.
    """
    try:
        result = await vonage_consolidated_service.play_tts_to_call(
            call_uuid=tts_request.call_uuid,
            text=tts_request.text,
            voice_name=tts_request.voice_name,
            language=tts_request.language
        )

        if not result.success:
            raise HTTPException(status_code=400, detail=result.error)

        return {
            "success": True,
            "result": result.data,
            "call_uuid": tts_request.call_uuid,
            "message": "TTS played successfully"
        }

    except Exception as e:
        logger.error(f"Error playing TTS: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/voice/call/{call_uuid}/tts", response_model=Dict[str, Any])
async def stop_tts_in_call(
    call_uuid: str,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Stop text-to-speech in an active call.
    """
    try:
        result = await vonage_consolidated_service.stop_tts_in_call(call_uuid)

        if not result.success:
            raise HTTPException(status_code=400, detail=result.error)

        return {
            "success": True,
            "result": result.data,
            "call_uuid": call_uuid,
            "message": "TTS stopped successfully"
        }

    except Exception as e:
        logger.error(f"Error stopping TTS: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Number Management Routes
@router.post("/numbers/search", response_model=Dict[str, Any])
async def search_available_numbers(
    search_request: VonageNumberSearchRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Search for available phone numbers.
    """
    try:
        search_params = {
            "type": search_request.type_,
            "pattern": search_request.pattern,
            "search_pattern": search_request.search_pattern,
            "features": search_request.features,
            "size": search_request.size,
            "index": search_request.index
        }

        result = await vonage_consolidated_service.manage_tenant_numbers(
            tenant_id=search_request.tenant_id,
            operation="search",
            country=search_request.country,
            search_params=search_params,
            context={
                "searched_by": current_user.get("user_id"),
                "searched_at": datetime.now().isoformat()
            }
        )

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))

        return result

    except Exception as e:
        logger.error(f"Error searching numbers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/numbers/manage", response_model=Dict[str, Any])
async def manage_phone_numbers(
    management_request: VonageNumberManagementRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Manage phone numbers (buy, cancel, list).
    """
    try:
        result = await vonage_consolidated_service.manage_tenant_numbers(
            tenant_id=management_request.tenant_id,
            operation=management_request.operation,
            country=management_request.country,
            msisdn=management_request.msisdn,
            search_params=management_request.search_params,
            context={
                "managed_by": current_user.get("user_id"),
                "managed_at": datetime.now().isoformat()
            }
        )

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))

        return result

    except Exception as e:
        logger.error(f"Error managing numbers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Account Routes
@router.get("/account/balance", response_model=Dict[str, Any])
async def get_account_balance(
    tenant_id: str = "default",
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Get Vonage account balance.
    """
    try:
        result = await vonage_consolidated_service.get_tenant_account_info(
            tenant_id=tenant_id,
            context={
                "requested_by": current_user.get("user_id"),
                "requested_at": datetime.now().isoformat()
            }
        )

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))

        return result

    except Exception as e:
        logger.error(f"Error getting account balance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/account/settings", response_model=Dict[str, Any])
async def update_account_settings(
    mo_callback_url: Optional[str] = None,
    dr_callback_url: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Update account webhook settings.
    """
    try:
        result = await vonage_consolidated_service.update_account_settings(
            mo_callback_url=mo_callback_url,
            dr_callback_url=dr_callback_url
        )

        if not result.success:
            raise HTTPException(status_code=400, detail=result.error)

        return {
            "success": True,
            "result": result.data,
            "message": "Account settings updated successfully"
        }

    except Exception as e:
        logger.error(f"Error updating account settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Webhook Routes
@router.post("/webhooks/{tenant_id}", response_model=Dict[str, Any])
async def handle_vonage_webhook(
    tenant_id: str,
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Handle Vonage webhooks using the consolidated service.
    """
    try:
        # Get raw body and headers
        body = await request.body()
        headers = dict(request.headers)

        # Parse webhook data
        try:
            if request.headers.get("content-type") == "application/json":
                webhook_data = json.loads(body.decode())
            else:
                # Handle form-encoded webhooks
                form_data = await request.form()
                webhook_data = dict(form_data)
        except Exception:
            webhook_data = {"raw_body": body.decode()}

        # Get signature for validation
        signature = headers.get("x-nexmo-signature")

        # Process webhook through consolidated service
        result = await vonage_consolidated_service.handle_tenant_webhook(
            tenant_id=tenant_id,
            webhook_data=webhook_data,
            signature=signature,
            context={
                "headers": headers,
                "received_at": datetime.now().isoformat()
            }
        )

        if not result.get("success"):
            logger.error(f"Webhook processing failed: {result.get('error')}")
            return JSONResponse(status_code=400, content=result)

        return JSONResponse(status_code=200, content=result)

    except Exception as e:
        logger.error(f"Error handling Vonage webhook: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


# Analytics Routes
@router.get("/analytics/{tenant_id}", response_model=Dict[str, Any])
async def get_vonage_analytics(
    tenant_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Get Vonage analytics for a tenant using the consolidated service.
    """
    try:
        # Parse dates if provided
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None

        result = await vonage_consolidated_service.get_tenant_voice_analytics(
            tenant_id=tenant_id,
            start_date=start_dt,
            end_date=end_dt
        )

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))

        return result

    except Exception as e:
        logger.error(f"Error getting Vonage analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Utility Routes
@router.get("/capabilities", response_model=Dict[str, Any])
async def get_vonage_capabilities():
    """
    Get Vonage service capabilities.
    """
    try:
        capabilities = vonage_consolidated_service.get_extended_capabilities()
        return {
            "success": True,
            "capabilities": capabilities,
            "service_version": "consolidated",
            "consolidation_status": "active"
        }

    except Exception as e:
        logger.error(f"Error getting Vonage capabilities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=Dict[str, Any])
async def vonage_health_check():
    """
    Health check for the consolidated Vonage service.
    """
    try:
        result = await vonage_consolidated_service.health_check()

        return {
            "success": True,
            "service": "vonage_consolidated",
            "status": result.get("status", "unknown"),
            "connection_test": result,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Vonage health check failed: {e}")
        return {
            "success": False,
            "service": "vonage_consolidated",
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }