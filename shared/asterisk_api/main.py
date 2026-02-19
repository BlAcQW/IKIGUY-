"""
Asterisk REST API Service
Provides HTTP REST access to Asterisk AMI operations
Used by all Kasa AI apps for phone number provisioning
"""
import os
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, status, Depends, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Asterisk REST API",
    description="REST API wrapper for Asterisk AMI operations",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration - explicit origins to avoid duplication issue
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # Production frontends
        "https://kasaai.ailabsafrica.com",
        "https://api.ailabsafrica.com",
        "https://developer.ailabsafrica.com",
        "https://developer-portal-api.ailabsafrica.com",
        "https://churchflow.ailabsafrica.com",
        "https://churchflow-api.ailabsafrica.com",
        "https://studyflow.ailabsafrica.com",
        "https://studyflow-api.ailabsafrica.com",
        "https://eventflow.ailabsafrica.com",
        "https://eventflow-api.ailabsafrica.com",
        "https://inkwave.ailabsafrica.com",
        "https://inkwave-api.ailabsafrica.com",
        "https://erp.ailabsafrica.com",
        "https://erp-api.ailabsafrica.com",
        # Dev frontends
        "https://dev-kasaai.ailabsafrica.com",
        "https://dev-api.ailabsafrica.com",
        "https://dev-developer.ailabsafrica.com",
        "https://dev-developer-portal-api.ailabsafrica.com",
        "https://dev-churchflow.ailabsafrica.com",
        "https://dev-churchflow-api.ailabsafrica.com",
        "https://dev-studyflow.ailabsafrica.com",
        "https://dev-studyflow-api.ailabsafrica.com",
        "https://dev-eventflow.ailabsafrica.com",
        "https://dev-eventflow-api.ailabsafrica.com",
        "https://dev-inkwave.ailabsafrica.com",
        "https://dev-inkwave-api.ailabsafrica.com",
        "https://dev-erp.ailabsafrica.com",
        "https://dev-erp-api.ailabsafrica.com",
        # Localhost for development
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models
class SIPCredentials(BaseModel):
    """SIP credentials for a phone number"""
    username: str = Field(..., description="SIP username")
    password: str = Field(..., description="SIP password")
    server: str = Field(default="asterisk.ailabsafrica.com", description="SIP server hostname")
    port: int = Field(default=5060, description="SIP server port")
    context: str = Field(default="kasaai-virtual", description="Asterisk context")

class PhoneNumberCreate(BaseModel):
    """Request to create a phone number in Asterisk"""
    number: str = Field(..., description="Phone number (E.164 format)")
    sip_username: str = Field(..., description="SIP username for authentication")
    sip_password: str = Field(..., description="SIP password for authentication")
    webhook_url: str = Field(..., description="Webhook URL for incoming calls")
    context: str = Field(default="kasaai-virtual", description="Asterisk context")
    capabilities: List[str] = Field(default=["voice"], description="Number capabilities")

class PhoneNumberResponse(BaseModel):
    """Response from phone number operation"""
    success: bool
    message: str
    number: Optional[str] = None
    sip_credentials: Optional[SIPCredentials] = None
    created_at: Optional[datetime] = None

class PhoneNumberDelete(BaseModel):
    """Request to delete a phone number"""
    number: str = Field(..., description="Phone number to delete")
    sip_username: str = Field(..., description="SIP username to remove")

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    asterisk_connected: bool
    ami_version: Optional[str] = None
    timestamp: datetime

class CallRouteCreate(BaseModel):
    """Create call routing rule"""
    number: str = Field(..., description="Phone number to route")
    webhook_url: str = Field(..., description="Webhook URL to invoke")
    method: str = Field(default="POST", description="HTTP method")

# Dependency for API key validation
def verify_api_key(api_key: str = Depends(lambda: os.getenv("ASTERISK_API_KEY"))):
    """Verify API key for authentication"""
    # For now, we'll use a simple API key from environment
    # In production, this should be more sophisticated
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key not configured on server"
        )
    return api_key

# Import AMI client
try:
    from ami_client import AsteriskAMIClient
    ami_client = AsteriskAMIClient()
    logger.info("AMI client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize AMI client: {e}")
    ami_client = None


# Lifecycle events for proper cleanup
@app.on_event("shutdown")
async def shutdown_event():
    """
    Clean up resources on shutdown.
    Close AMI connection to prevent resource leaks.
    """
    logger.info("Shutting down Asterisk REST API...")
    if ami_client:
        try:
            await ami_client.close()
            logger.info("AMI client connection closed")
        except Exception as e:
            logger.error(f"Error closing AMI client: {e}")

# API Routes

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "service": "Asterisk REST API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    Verifies API is running and Asterisk is accessible
    """
    asterisk_connected = False
    ami_version = None

    if ami_client:
        try:
            asterisk_connected = await ami_client.test_connection()
            if asterisk_connected:
                ami_version = await ami_client.get_version()
        except Exception as e:
            logger.error(f"Health check failed: {e}")

    return HealthResponse(
        status="healthy" if asterisk_connected else "degraded",
        asterisk_connected=asterisk_connected,
        ami_version=ami_version,
        timestamp=datetime.utcnow()
    )

@app.post("/sip/peer", response_model=PhoneNumberResponse, status_code=status.HTTP_201_CREATED)
async def create_sip_peer(request: PhoneNumberCreate):
    """
    Create SIP peer in Asterisk for a phone number

    This creates:
    - PJSIP endpoint with authentication
    - AOR (Address of Record) configuration
    - Webhook URL registration in AstDB
    """
    if not ami_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AMI client not available"
        )

    try:
        logger.info(f"Creating SIP peer for {request.number}")

        # Create SIP peer
        success = await ami_client.create_sip_peer(
            number=request.number,
            sip_username=request.sip_username,
            sip_password=request.sip_password,
            webhook_url=request.webhook_url,
            context=request.context
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create SIP peer in Asterisk"
            )

        # Return success response
        return PhoneNumberResponse(
            success=True,
            message=f"SIP peer created successfully for {request.number}",
            number=request.number,
            sip_credentials=SIPCredentials(
                username=request.sip_username,
                password=request.sip_password,
                server="asterisk.ailabsafrica.com",
                port=5060,
                context=request.context
            ),
            created_at=datetime.utcnow()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating SIP peer: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )

@app.delete("/sip/peer", response_model=PhoneNumberResponse)
async def delete_sip_peer(request: PhoneNumberDelete):
    """
    Delete SIP peer from Asterisk

    This removes:
    - PJSIP endpoint configuration
    - AOR configuration
    - Webhook URL from AstDB
    """
    if not ami_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AMI client not available"
        )

    try:
        logger.info(f"Deleting SIP peer for {request.number}")

        # Delete SIP peer
        success = await ami_client.delete_sip_peer(
            number=request.number,
            sip_username=request.sip_username
        )

        if not success:
            logger.warning(f"Failed to delete SIP peer for {request.number}")
            # Don't raise error - peer might not exist

        return PhoneNumberResponse(
            success=True,
            message=f"SIP peer deleted for {request.number}",
            number=request.number
        )

    except Exception as e:
        logger.error(f"Error deleting SIP peer: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )

@app.get("/sip/peer/{sip_username}", response_model=Dict[str, Any])
async def get_sip_peer(sip_username: str):
    """
    Get SIP peer information from Asterisk
    """
    if not ami_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AMI client not available"
        )

    try:
        peer_info = await ami_client.get_sip_peer(sip_username)

        if not peer_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"SIP peer {sip_username} not found"
            )

        return peer_info

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting SIP peer: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )

@app.get("/sip/peers", response_model=Dict[str, List[str]])
async def list_sip_peers():
    """
    List all SIP peers managed by Kasa AI
    """
    if not ami_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AMI client not available"
        )

    try:
        peers = await ami_client.list_sip_peers()
        return {"peers": peers}

    except Exception as e:
        logger.error(f"Error listing SIP peers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )

@app.post("/call/route", response_model=Dict[str, str])
async def create_call_route(request: CallRouteCreate):
    """
    Create call routing rule for incoming calls
    Stores webhook URL in AstDB for the given number
    """
    if not ami_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AMI client not available"
        )

    try:
        success = await ami_client.set_webhook_url(
            number=request.number,
            webhook_url=request.webhook_url
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to set webhook URL"
            )

        return {
            "success": True,
            "message": f"Call route created for {request.number}",
            "webhook_url": request.webhook_url
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating call route: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )

@app.get("/asterisk/status", response_model=Dict[str, Any])
async def asterisk_status():
    """
    Get Asterisk server status
    Returns channels, calls, uptime, etc.
    """
    if not ami_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AMI client not available"
        )

    try:
        status_info = await ami_client.get_asterisk_status()
        return status_info

    except Exception as e:
        logger.error(f"Error getting Asterisk status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )

@app.post("/asterisk/reload", response_model=Dict[str, str])
async def reload_asterisk():
    """
    Reload Asterisk configuration
    Use with caution - reloads PJSIP module
    """
    if not ami_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AMI client not available"
        )

    try:
        success = await ami_client.reload_pjsip()

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reload PJSIP"
            )

        return {
            "success": True,
            "message": "PJSIP configuration reloaded successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reloading Asterisk: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to WebSocket: {e}")
                disconnected.append(connection)

        # Remove disconnected clients
        for conn in disconnected:
            if conn in self.active_connections:
                self.active_connections.remove(conn)

manager = ConnectionManager()

@app.websocket("/ws/events")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time Asterisk events
    Broadcasts call events, peer registrations, system status

    Note: Status updates use cached data from ami_client to avoid
    creating new AMI connections on each poll.
    """
    await manager.connect(websocket)
    consecutive_errors = 0
    max_consecutive_errors = 5

    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "timestamp": datetime.utcnow().isoformat()
        })

        # Keep connection alive and broadcast events
        while True:
            # Poll every 10 seconds instead of 5 to reduce load
            await asyncio.sleep(10)

            if ami_client:
                try:
                    # get_asterisk_status() uses caching and persistent connection
                    status_info = await ami_client.get_asterisk_status()
                    await websocket.send_json({
                        "type": "status_update",
                        "data": status_info,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    consecutive_errors = 0  # Reset on success
                except Exception as e:
                    consecutive_errors += 1
                    logger.error(f"Error getting status for WebSocket (attempt {consecutive_errors}): {e}")

                    # If too many errors, send error status and back off
                    if consecutive_errors >= max_consecutive_errors:
                        await websocket.send_json({
                            "type": "status_update",
                            "data": {"status": "error", "error": "AMI connection issues"},
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        # Back off for 30 seconds on persistent errors
                        await asyncio.sleep(30)
                        consecutive_errors = 0

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

@app.get("/call-history", response_model=Dict[str, Any])
async def get_call_history(
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0),
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
    direction: Optional[str] = Query(default=None)
):
    """
    Get call detail records (CDR)
    Returns paginated call history with optional filters
    """
    # Mock data for now - replace with actual CDR database query
    mock_calls = []

    # Generate mock call history for demonstration
    for i in range(50):
        hours_ago = i * 2
        start_time = datetime.utcnow() - timedelta(hours=hours_ago)
        duration = 120 + (i * 10)

        call_direction = "inbound" if i % 2 == 0 else "outbound"
        call_status = ["completed", "failed", "no-answer", "busy"][i % 4]

        mock_calls.append({
            "id": f"call-{i+1}",
            "call_id": f"call-2025-11-12-{str(i+1).zfill(3)}",
            "direction": call_direction,
            "from_number": f"+123456{str(i).zfill(4)}",
            "to_number": f"+987654{str(i).zfill(4)}",
            "start_time": start_time.isoformat() + "Z",
            "end_time": (start_time + timedelta(seconds=duration)).isoformat() + "Z",
            "duration": duration if call_status == "completed" else 0,
            "status": call_status,
            "disposition": call_status.upper().replace("-", " ")
        })

    # Apply filters
    filtered_calls = mock_calls

    if direction:
        filtered_calls = [c for c in filtered_calls if c["direction"] == direction]

    if start_date:
        start_dt = datetime.fromisoformat(start_date.replace("Z", ""))
        filtered_calls = [c for c in filtered_calls if datetime.fromisoformat(c["start_time"].replace("Z", "")) >= start_dt]

    if end_date:
        end_dt = datetime.fromisoformat(end_date.replace("Z", ""))
        filtered_calls = [c for c in filtered_calls if datetime.fromisoformat(c["start_time"].replace("Z", "")) <= end_dt]

    # Apply pagination
    total = len(filtered_calls)
    paginated_calls = filtered_calls[offset:offset + limit]

    return {
        "calls": paginated_calls,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": (offset + limit) < total
    }

@app.get("/metrics", response_model=Dict[str, Any])
async def get_metrics(
    period: str = Query(default="24h", pattern="^(1h|6h|24h|7d|30d)$")
):
    """
    Get system metrics for visualization
    Returns call volume, peer registrations, system performance
    """
    # Parse period
    hours_map = {"1h": 1, "6h": 6, "24h": 24, "7d": 168, "30d": 720}
    hours = hours_map.get(period, 24)

    # Generate mock metrics data
    data_points = min(hours, 48)  # Max 48 data points
    interval = hours * 60 // data_points  # Minutes between points

    metrics = {
        "period": period,
        "interval_minutes": interval,
        "call_volume": [],
        "peer_registrations": [],
        "system_load": [],
        "timestamps": []
    }

    current_time = datetime.utcnow()

    for i in range(data_points):
        timestamp = current_time - timedelta(minutes=interval * (data_points - i))

        # Simulate call volume (higher during business hours)
        hour = timestamp.hour
        base_calls = 5 if 9 <= hour <= 17 else 2
        call_count = base_calls + (i % 3)

        metrics["timestamps"].append(timestamp.isoformat() + "Z")
        metrics["call_volume"].append(call_count)
        metrics["peer_registrations"].append(10 + (i % 5))
        metrics["system_load"].append(round(0.3 + (i % 10) * 0.05, 2))

    return metrics

@app.get("/alerts", response_model=Dict[str, Any])
async def get_alerts():
    """
    Get system alerts and warnings
    Returns active alerts for monitoring
    """
    alerts = []

    if ami_client:
        try:
            # Check system health
            status_info = await ami_client.get_asterisk_status()

            # Check for high load
            if status_info.get("active_calls", 0) > 10:
                alerts.append({
                    "id": "high-call-volume",
                    "severity": "warning",
                    "title": "High Call Volume",
                    "message": f"{status_info['active_calls']} active calls detected",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                })

            # Check for no registered peers
            if status_info.get("sip_peers", 0) == 0:
                alerts.append({
                    "id": "no-peers",
                    "severity": "error",
                    "title": "No SIP Peers Registered",
                    "message": "No SIP endpoints are currently registered",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                })

        except Exception as e:
            logger.error(f"Error checking alerts: {e}")

    return {
        "alerts": alerts,
        "count": len(alerts)
    }

# Main entry point
if __name__ == "__main__":
    port = int(os.getenv("ASTERISK_API_PORT", 30040))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )
