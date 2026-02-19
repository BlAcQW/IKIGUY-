"""
Vapi.ai Integration for Kasaai Voice Engine
Handles webhook events and call orchestration with Vapi
"""

import logging
import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel, Field
import aiohttp

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vapi", tags=["vapi"])


class VapiWebhookEvent(BaseModel):
    """Vapi webhook event model"""
    event: str
    call_id: Optional[str] = Field(None, alias="callId")
    assistant_id: Optional[str] = Field(None, alias="assistantId")
    phone_number: Optional[str] = Field(None, alias="phoneNumber")
    customer_number: Optional[str] = Field(None, alias="customerNumber")
    transcript: Optional[str] = None
    recording_url: Optional[str] = Field(None, alias="recordingUrl")
    duration: Optional[int] = None
    ended_reason: Optional[str] = Field(None, alias="endedReason")
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None


class VapiCallRequest(BaseModel):
    """Request to initiate a Vapi call"""
    to_number: str = Field(..., description="Phone number to call")
    assistant_id: str = Field(..., description="Vapi assistant ID")
    from_number: Optional[str] = Field(None, description="Caller ID")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    first_message: Optional[str] = None
    model: Optional[str] = "gpt-4"
    voice_id: Optional[str] = None
    webhook_url: Optional[str] = None


class VapiConfig:
    """Vapi configuration"""
    API_KEY = "YOUR_VAPI_API_KEY"  # Should be in environment variables
    BASE_URL = "https://api.vapi.ai"
    WEBHOOK_URL = "https://api.kasaai.ailabsafrica.com/voice/vapi/webhook"
    SIP_URI = "sip:vapi@asterisk.ailabsafrica.com"


class VapiIntegration:
    """Handles Vapi.ai integration"""
    
    def __init__(self):
        self.config = VapiConfig()
        self.session: Optional[aiohttp.ClientSession] = None
        self.active_calls: Dict[str, Dict[str, Any]] = {}
        
    async def initialize(self):
        """Initialize Vapi integration"""
        if not self.session:
            self.session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.config.API_KEY}",
                    "Content-Type": "application/json"
                }
            )
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
    
    async def create_phone_call(
        self,
        to_number: str,
        assistant_id: str,
        from_number: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create an outbound phone call via Vapi
        
        Args:
            to_number: Phone number to call
            assistant_id: Vapi assistant ID
            from_number: Caller ID (optional)
            metadata: Additional metadata
            
        Returns:
            Call details from Vapi
        """
        await self.initialize()
        
        payload = {
            "assistantId": assistant_id,
            "customer": {
                "number": to_number
            },
            "phoneNumberId": from_number,
            "metadata": metadata or {},
            "webhookUrl": self.config.WEBHOOK_URL
        }
        
        try:
            async with self.session.post(
                f"{self.config.BASE_URL}/call/phone",
                json=payload
            ) as response:
                if response.status == 201:
                    data = await response.json()
                    call_id = data.get("id")
                    
                    # Track active call
                    self.active_calls[call_id] = {
                        "call_id": call_id,
                        "to_number": to_number,
                        "assistant_id": assistant_id,
                        "status": "initiated",
                        "started_at": datetime.utcnow(),
                        "metadata": metadata
                    }
                    
                    return data
                else:
                    error = await response.text()
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"Vapi API error: {error}"
                    )
                    
        except aiohttp.ClientError as e:
            logger.error(f"Failed to create Vapi call: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def end_call(self, call_id: str) -> bool:
        """
        End an active Vapi call
        
        Args:
            call_id: Vapi call ID
            
        Returns:
            Success status
        """
        await self.initialize()
        
        try:
            async with self.session.delete(
                f"{self.config.BASE_URL}/call/{call_id}"
            ) as response:
                success = response.status == 200
                
                if success and call_id in self.active_calls:
                    self.active_calls[call_id]["status"] = "ended"
                    self.active_calls[call_id]["ended_at"] = datetime.utcnow()
                
                return success
                
        except aiohttp.ClientError as e:
            logger.error(f"Failed to end Vapi call {call_id}: {e}")
            return False
    
    async def get_call_status(self, call_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a Vapi call
        
        Args:
            call_id: Vapi call ID
            
        Returns:
            Call status details
        """
        await self.initialize()
        
        try:
            async with self.session.get(
                f"{self.config.BASE_URL}/call/{call_id}"
            ) as response:
                if response.status == 200:
                    return await response.json()
                return None
                
        except aiohttp.ClientError as e:
            logger.error(f"Failed to get Vapi call status for {call_id}: {e}")
            return None
    
    async def handle_webhook_event(self, event: VapiWebhookEvent) -> Dict[str, Any]:
        """
        Handle incoming Vapi webhook event
        
        Args:
            event: Vapi webhook event
            
        Returns:
            Response data
        """
        logger.info(f"Received Vapi event: {event.event} for call {event.call_id}")
        
        call_id = event.call_id
        
        # Update call tracking
        if call_id and call_id in self.active_calls:
            call_data = self.active_calls[call_id]
            
            if event.event == "call.started":
                call_data["status"] = "in_progress"
                call_data["started_at"] = datetime.utcnow()
                
            elif event.event == "call.ended":
                call_data["status"] = "ended"
                call_data["ended_at"] = datetime.utcnow()
                call_data["duration"] = event.duration
                call_data["ended_reason"] = event.ended_reason
                
            elif event.event == "speech.transcribed":
                if "transcripts" not in call_data:
                    call_data["transcripts"] = []
                call_data["transcripts"].append({
                    "text": event.transcript,
                    "timestamp": datetime.utcnow()
                })
                
            elif event.event == "recording.available":
                call_data["recording_url"] = event.recording_url
        
        # Process specific events
        response = await self.process_event(event)
        
        return response
    
    async def process_event(self, event: VapiWebhookEvent) -> Dict[str, Any]:
        """
        Process specific Vapi events
        
        Args:
            event: Vapi webhook event
            
        Returns:
            Response data for Vapi
        """
        response = {"success": True}
        
        if event.event == "assistant.request":
            # Vapi is requesting assistant configuration
            response["assistant"] = {
                "firstMessage": "Hello! I'm your Kasaai AI assistant. How can I help you today?",
                "model": {
                    "provider": "openai",
                    "model": "gpt-4",
                    "temperature": 0.7
                },
                "voice": {
                    "provider": "11labs",
                    "voiceId": "21m00Tcm4TlvDq8ikWAM"
                },
                "recordingEnabled": True,
                "endCallFunctionEnabled": True
            }
            
        elif event.event == "function.call":
            # Handle function calls from Vapi
            function_name = event.metadata.get("function", {}).get("name")
            function_args = event.metadata.get("function", {}).get("arguments", {})
            
            result = await self.execute_function(function_name, function_args)
            response["result"] = result
            
        elif event.event == "transfer.request":
            # Handle call transfer request
            transfer_to = event.metadata.get("transferTo")
            response["transfer"] = {
                "number": transfer_to,
                "sipUri": f"sip:{transfer_to}@asterisk.ailabsafrica.com"
            }
        
        return response
    
    async def execute_function(
        self,
        function_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a function requested by Vapi
        
        Args:
            function_name: Name of function to execute
            arguments: Function arguments
            
        Returns:
            Function result
        """
        logger.info(f"Executing function: {function_name} with args: {arguments}")
        
        # Implement your custom functions here
        if function_name == "transfer_call":
            return {
                "success": True,
                "message": "Call transferred successfully"
            }
        elif function_name == "send_sms":
            return {
                "success": True,
                "message": "SMS sent successfully"
            }
        elif function_name == "schedule_callback":
            return {
                "success": True,
                "message": "Callback scheduled",
                "callback_time": arguments.get("time")
            }
        else:
            return {
                "success": False,
                "error": f"Unknown function: {function_name}"
            }


# Global Vapi integration instance
vapi_integration = VapiIntegration()


# API Routes

@router.post("/webhook")
async def handle_vapi_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Handle incoming webhooks from Vapi
    
    Args:
        request: FastAPI request object
        background_tasks: Background task manager
        
    Returns:
        Webhook response
    """
    try:
        # Parse webhook data
        data = await request.json()
        event = VapiWebhookEvent(**data)
        
        # Process event
        response = await vapi_integration.handle_webhook_event(event)
        
        # Log event in background
        background_tasks.add_task(log_webhook_event, event)
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to process Vapi webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/call/outbound")
async def make_vapi_call(request: VapiCallRequest):
    """
    Initiate an outbound call via Vapi
    
    Args:
        request: Call request details
        
    Returns:
        Call initiation response
    """
    try:
        result = await vapi_integration.create_phone_call(
            to_number=request.to_number,
            assistant_id=request.assistant_id,
            from_number=request.from_number,
            metadata=request.metadata
        )
        
        return {
            "success": True,
            "call_id": result.get("id"),
            "status": "initiated",
            "message": "Call initiated successfully via Vapi"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to initiate Vapi call: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/call/{call_id}")
async def end_vapi_call(call_id: str):
    """
    End an active Vapi call
    
    Args:
        call_id: Vapi call ID
        
    Returns:
        Success status
    """
    try:
        success = await vapi_integration.end_call(call_id)
        
        if success:
            return {
                "success": True,
                "message": "Call ended successfully"
            }
        else:
            raise HTTPException(status_code=404, detail="Call not found or already ended")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to end Vapi call {call_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/call/{call_id}/status")
async def get_vapi_call_status(call_id: str):
    """
    Get status of a Vapi call
    
    Args:
        call_id: Vapi call ID
        
    Returns:
        Call status details
    """
    try:
        # Check local tracking first
        if call_id in vapi_integration.active_calls:
            local_data = vapi_integration.active_calls[call_id]
            
            # Get latest from Vapi
            vapi_data = await vapi_integration.get_call_status(call_id)
            
            if vapi_data:
                # Merge data
                return {
                    **local_data,
                    **vapi_data,
                    "source": "vapi"
                }
            else:
                return {
                    **local_data,
                    "source": "local"
                }
        else:
            # Try to get from Vapi
            vapi_data = await vapi_integration.get_call_status(call_id)
            if vapi_data:
                return vapi_data
            else:
                raise HTTPException(status_code=404, detail="Call not found")
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get Vapi call status for {call_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calls/active")
async def get_active_vapi_calls():
    """
    Get all active Vapi calls
    
    Returns:
        List of active calls
    """
    try:
        active_calls = [
            call for call in vapi_integration.active_calls.values()
            if call.get("status") not in ["ended", "failed"]
        ]
        
        return {
            "count": len(active_calls),
            "calls": active_calls
        }
        
    except Exception as e:
        logger.error(f"Failed to get active Vapi calls: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def log_webhook_event(event: VapiWebhookEvent):
    """
    Log webhook event for analytics
    
    Args:
        event: Vapi webhook event
    """
    try:
        logger.info(f"Vapi Event Log: {event.event} - Call: {event.call_id}")
        # TODO: Save to database for analytics
        
    except Exception as e:
        logger.error(f"Failed to log webhook event: {e}")


# Initialize on module load
async def initialize_vapi():
    """Initialize Vapi integration on startup"""
    await vapi_integration.initialize()
    logger.info("Vapi integration initialized")


async def cleanup_vapi():
    """Cleanup Vapi integration on shutdown"""
    await vapi_integration.cleanup()
    logger.info("Vapi integration cleaned up")