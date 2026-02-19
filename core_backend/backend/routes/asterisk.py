"""
Asterisk Telephony Routes

This module provides endpoints for Asterisk telephony operations including
call origination, channel management, dial plan operations, and CDR (Call Detail Record)
webhooks for cost tracking.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import logging
import subprocess
import asyncio
from datetime import datetime, timedelta
import os

from ..schemas.cdr import CDRStatsResponse, CDRStatsRequest
from ..services.cdr_stats_service import get_cdr_stats_service

logger = logging.getLogger(__name__)

# MongoDB setup for CDR storage
try:
    from ..mongo import get_database
    MONGO_AVAILABLE = True
except ImportError:
    MONGO_AVAILABLE = False
    logger.warning("MongoDB not available for Asterisk CDR storage")

router = APIRouter(prefix="/asterisk", tags=["Asterisk"])


class CallOriginateRequest(BaseModel):
    """Request model for originating a call via Asterisk."""
    destination: str = Field(..., description="Destination number to call")
    source_number: Optional[str] = Field("0308249843", description="Source caller ID")
    context: str = Field("from-internal", description="Asterisk dialplan context")
    timeout: int = Field(60, description="Call timeout in seconds", ge=10, le=300)
    priority: int = Field(1, description="Dialplan priority")
    variables: Optional[Dict[str, str]] = Field(None, description="Channel variables")


class CallOriginateResponse(BaseModel):
    """Response model for call origination."""
    success: bool
    message: str
    call_id: Optional[str] = None
    destination: str
    status: str


def execute_asterisk_command(command: str) -> tuple[bool, str]:
    """
    Execute an Asterisk CLI command via docker.

    Args:
        command: Asterisk CLI command to execute

    Returns:
        Tuple of (success: bool, output: str)
    """
    try:
        result = subprocess.run(
            ['docker', 'exec', 'kasaai-asterisk-proxy', 'asterisk', '-rx', command],
            capture_output=True,
            text=True,
            timeout=10
        )

        output = result.stdout.strip()
        error_output = result.stderr.strip()
        success = result.returncode == 0

        logger.info(f"Asterisk command: {command}")
        logger.info(f"Command stdout: {output}")
        logger.info(f"Command stderr: {error_output}")
        logger.info(f"Command returncode: {result.returncode}")

        return success, output
    except subprocess.TimeoutExpired:
        logger.error(f"Asterisk command timed out: {command}")
        return False, "Command timed out"
    except Exception as e:
        logger.error(f"Error executing Asterisk command: {e}")
        return False, str(e)


@router.post("/call/originate", response_model=CallOriginateResponse)
async def originate_call(request: CallOriginateRequest):
    """
    Originate a call via Asterisk.

    This endpoint initiates an outbound call through Asterisk's channel originate feature.
    The call will route through the specified dialplan context (default: from-internal)
    which will use the Ant Cellular trunk for outbound calling.

    Example:
        ```json
        {
            "destination": "0244123456",
            "source_number": "0308249843",
            "context": "from-internal",
            "timeout": 60
        }
        ```
    """
    logger.info(f"Call origination requested to {request.destination}")

    try:
        # Validate destination number (basic validation)
        if not request.destination or len(request.destination) < 4:
            raise HTTPException(
                status_code=400,
                detail="Invalid destination number"
            )

        # Build the channel originate command with async flag
        # Direct PJSIP origination through Ant Cellular trunk
        # When call is answered, wait 5 seconds then hangup (so user knows it's a test)
        # Format: channel originate PJSIP/<number>@<trunk> application <app> <args>
        # Note: async keyword tells Asterisk to return immediately without waiting
        asterisk_command = f"channel originate PJSIP/{request.destination}@ant-cellular application Wait 5 async"

        # Execute the command
        success, output = execute_asterisk_command(asterisk_command)

        # For async originate, success means command was accepted, not that call connected
        if not success or "error" in output.lower():
            logger.error(f"Call origination failed: {output}")
            return CallOriginateResponse(
                success=False,
                message=f"Failed to originate call: {output}",
                destination=request.destination,
                status="failed"
            )

        logger.info(f"Call originated successfully to {request.destination}")
        return CallOriginateResponse(
            success=True,
            message=f"Call initiated successfully to {request.destination}",
            call_id=None,  # Could parse from output if needed
            destination=request.destination,
            status="initiated"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error originating call: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal error originating call: {str(e)}"
        )


@router.get("/status")
async def get_asterisk_status():
    """
    Get Asterisk system status.

    Returns information about Asterisk uptime, active channels, and calls.
    """
    try:
        # Get core show status
        success, output = execute_asterisk_command("core show calls")

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to get Asterisk status"
            )

        # Parse the output
        lines = output.split('\n')
        active_calls = 0

        for line in lines:
            if "active call" in line.lower():
                parts = line.split()
                if parts:
                    try:
                        active_calls = int(parts[0])
                    except (ValueError, IndexError):
                        pass

        return {
            "status": "healthy",
            "active_calls": active_calls,
            "timestamp": asyncio.get_event_loop().time()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Asterisk status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get status: {str(e)}"
        )


@router.get("/channels")
async def get_active_channels():
    """
    Get list of active channels in Asterisk.
    """
    try:
        success, output = execute_asterisk_command("core show channels")

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to get channels"
            )

        return {
            "success": True,
            "output": output,
            "timestamp": asyncio.get_event_loop().time()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting channels: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get channels: {str(e)}"
        )


# ==================== CDR (Call Detail Record) Webhook ====================

class AsteriskCDR(BaseModel):
    """Model for Asterisk CDR webhook data."""
    uniqueid: str = Field(..., description="Unique call identifier")
    src: str = Field(..., description="Source/caller number")
    dst: str = Field(..., description="Destination number")
    dcontext: Optional[str] = Field(None, description="Destination context")
    clid: Optional[str] = Field(None, description="Caller ID")
    channel: Optional[str] = Field(None, description="Channel name")
    dstchannel: Optional[str] = Field(None, description="Destination channel")
    lastapp: Optional[str] = Field(None, description="Last application")
    lastdata: Optional[str] = Field(None, description="Last application data")
    start: Optional[str] = Field(None, description="Call start time")
    answer: Optional[str] = Field(None, description="Call answer time")
    end: Optional[str] = Field(None, description="Call end time")
    duration: int = Field(0, description="Total duration in seconds")
    billsec: int = Field(0, description="Billable seconds")
    disposition: str = Field("FAILED", description="Call disposition (ANSWERED, NO ANSWER, BUSY, FAILED)")
    amaflags: Optional[str] = Field(None, description="AMA flags")
    userfield: Optional[str] = Field(None, description="User field")
    accountcode: Optional[str] = Field(None, description="Account code")
    # Additional fields for phone tracking
    phone_id: Optional[str] = Field(None, description="Phone ID for credit tracking")
    phone_number: Optional[str] = Field(None, description="Phone number for credit tracking")


class CDRResponse(BaseModel):
    """Response model for CDR webhook."""
    success: bool
    message: str
    call_id: str
    cost_deducted: Optional[float] = None
    new_balance: Optional[float] = None


# Default cost per minute for MTN Ghana (GHC)
DEFAULT_COST_PER_MINUTE = 0.15


async def find_phone_by_number(phone_number: str) -> Optional[Dict[str, Any]]:
    """
    Find a phone record by number in the managed_phone_numbers collection.

    Args:
        phone_number: Phone number to search for (with or without country code)

    Returns:
        Phone document if found, None otherwise
    """
    if not MONGO_AVAILABLE:
        return None

    try:
        db = get_database()
        phones_collection = db["managed_phone_numbers"]

        # Try exact match first
        phone = await phones_collection.find_one({"number": phone_number})
        if phone:
            return phone

        # Try with +233 prefix
        if not phone_number.startswith("+"):
            phone = await phones_collection.find_one({"number": f"+233{phone_number}"})
            if phone:
                return phone

        # Try stripping +233 and matching last digits
        clean_number = phone_number.replace("+233", "").replace("+", "")
        cursor = phones_collection.find({})
        phones = await cursor.to_list(length=100)
        for p in phones:
            stored_number = p.get("number", "").replace("+233", "").replace("+", "")
            if stored_number.endswith(clean_number[-8:]) or clean_number.endswith(stored_number[-8:]):
                return p

        return None
    except Exception as e:
        logger.error(f"Error finding phone by number: {e}")
        return None


async def process_cdr_cost(cdr_data: Dict[str, Any], phone_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process CDR data and deduct credit from phone balance.

    Args:
        cdr_data: CDR record from Asterisk
        phone_record: Phone record from MongoDB

    Returns:
        Dict with cost_deducted and new_balance
    """
    try:
        if not MONGO_AVAILABLE:
            return {"cost_deducted": 0, "new_balance": 0}

        db = get_database()
        phones_collection = db["managed_phone_numbers"]
        transactions_collection = db["phone_credit_transactions"]

        # Calculate cost
        billsec = cdr_data.get("billsec", 0)
        if billsec <= 0:
            return {"cost_deducted": 0, "new_balance": phone_record.get("credit_balance", 0)}

        cost_per_minute = phone_record.get("cost_per_minute", DEFAULT_COST_PER_MINUTE)
        minutes = billsec / 60.0
        cost = minutes * cost_per_minute

        # Get current balance
        current_balance = phone_record.get("credit_balance", 0)
        new_balance = current_balance - cost

        # Update phone balance and usage stats
        await phones_collection.update_one(
            {"id": phone_record["id"]},
            {
                "$set": {
                    "credit_balance": new_balance,
                    "updated_at": datetime.utcnow()
                },
                "$inc": {
                    "total_minutes_used": minutes,
                    "total_cost_spent": cost
                }
            }
        )

        # Create transaction record
        transaction = {
            "id": f"txn_asterisk_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{cdr_data.get('uniqueid', 'unknown')[:8]}",
            "phone_id": phone_record["id"],
            "phone_number": phone_record.get("number"),
            "amount": -cost,
            "transaction_type": "debit",
            "timestamp": datetime.utcnow(),
            "balance_before": current_balance,
            "balance_after": new_balance,
            "call_id": cdr_data.get("uniqueid"),
            "call_duration_seconds": billsec,
            "call_duration_minutes": minutes,
            "notes": f"Asterisk call to {cdr_data.get('dst')}",
            "metadata": {
                "source": "asterisk_cdr",
                "disposition": cdr_data.get("disposition"),
                "dst": cdr_data.get("dst"),
                "src": cdr_data.get("src")
            }
        }
        await transactions_collection.insert_one(transaction)

        logger.info(f"📞 CDR Cost processed: {minutes:.2f} min × {cost_per_minute} = {cost:.2f} GHC. Balance: {current_balance:.2f} → {new_balance:.2f}")

        # Check for low balance alert
        low_threshold = phone_record.get("low_balance_threshold", 200)
        if new_balance < low_threshold and current_balance >= low_threshold:
            logger.warning(f"⚠️ Low balance alert for {phone_record.get('number')}: {new_balance:.2f} GHC < {low_threshold} GHC")

        return {"cost_deducted": cost, "new_balance": new_balance}

    except Exception as e:
        logger.error(f"Error processing CDR cost: {e}")
        return {"cost_deducted": 0, "new_balance": 0, "error": str(e)}


@router.post("/cdr/webhook", response_model=CDRResponse)
async def receive_cdr_webhook(cdr: AsteriskCDR, background_tasks: BackgroundTasks):
    """
    Receive CDR (Call Detail Record) webhook from Asterisk.

    This endpoint receives call completion data from Asterisk and:
    1. Stores the CDR in the asterisk_calls collection
    2. Deducts cost from the phone's credit balance
    3. Updates usage statistics

    Configure Asterisk to send CDR data to this endpoint using curl or HTTP POST.
    """
    try:
        logger.info(f"📞 CDR Webhook received: {cdr.uniqueid} | {cdr.src} → {cdr.dst} | Duration: {cdr.billsec}s | Disposition: {cdr.disposition}")

        if not MONGO_AVAILABLE:
            raise HTTPException(status_code=500, detail="MongoDB not available")

        db = get_database()
        asterisk_calls = db["asterisk_calls"]

        # Find the phone record for cost tracking
        # Check both source and destination to find our managed phone
        phone_record = None
        if cdr.phone_id:
            phones_collection = db["managed_phone_numbers"]
            phone_record = await phones_collection.find_one({"id": cdr.phone_id})

        if not phone_record and cdr.phone_number:
            phone_record = await find_phone_by_number(cdr.phone_number)

        if not phone_record:
            # Try to find by source or destination number
            phone_record = await find_phone_by_number(cdr.src)
            if not phone_record:
                phone_record = await find_phone_by_number(cdr.dst)

        # Determine call direction relative to the managed phone
        # If source matches our phone number = outbound, if destination matches = inbound
        call_direction = "unknown"
        if phone_record:
            managed_number = phone_record.get("number", "").replace("+", "").replace("233", "")[-9:]
            src_clean = cdr.src.replace("+", "").replace("233", "")[-9:] if cdr.src else ""
            dst_clean = cdr.dst.replace("+", "").replace("233", "")[-9:] if cdr.dst else ""

            if src_clean and managed_number and src_clean.endswith(managed_number[-8:]):
                call_direction = "outbound"  # Our phone made the call
            elif dst_clean and managed_number and dst_clean.endswith(managed_number[-8:]):
                call_direction = "inbound"   # Call came TO our phone

        # Store CDR record
        cdr_record = {
            "uniqueid": cdr.uniqueid,
            "src": cdr.src,
            "dst": cdr.dst,
            "direction": call_direction,  # Track call direction
            "dcontext": cdr.dcontext,
            "clid": cdr.clid,
            "channel": cdr.channel,
            "dstchannel": cdr.dstchannel,
            "lastapp": cdr.lastapp,
            "lastdata": cdr.lastdata,
            "start": cdr.start,
            "answer": cdr.answer,
            "end": cdr.end,
            "duration": cdr.duration,
            "billsec_seconds": cdr.billsec,
            "disposition": cdr.disposition,
            "amaflags": cdr.amaflags,
            "userfield": cdr.userfield,
            "accountcode": cdr.accountcode,
            "phone_id": phone_record["id"] if phone_record else None,
            "phone_number": phone_record.get("number") if phone_record else cdr.src,
            "created_at": datetime.utcnow(),
            "cost_ghc": 0  # Will be updated below
        }

        # Process cost if we have a phone record and call was answered
        cost_result = {"cost_deducted": 0, "new_balance": 0}
        if phone_record and cdr.disposition == "ANSWERED" and cdr.billsec > 0:
            cost_result = await process_cdr_cost(cdr.model_dump(), phone_record)
            cdr_record["cost_ghc"] = cost_result.get("cost_deducted", 0)

        # Insert CDR record
        await asterisk_calls.insert_one(cdr_record)

        logger.info(f"✅ CDR stored: {cdr.uniqueid} | Cost: {cost_result.get('cost_deducted', 0):.2f} GHC")

        return CDRResponse(
            success=True,
            message=f"CDR processed for call {cdr.uniqueid}",
            call_id=cdr.uniqueid,
            cost_deducted=cost_result.get("cost_deducted"),
            new_balance=cost_result.get("new_balance")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing CDR webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cdr/recent")
async def get_recent_cdrs(limit: int = 20):
    """
    Get recent CDR records from the asterisk_calls collection.
    """
    try:
        if not MONGO_AVAILABLE:
            raise HTTPException(status_code=500, detail="MongoDB not available")

        db = get_database()
        asterisk_calls = db["asterisk_calls"]

        # Use to_list() for async Motor cursor
        cursor = asterisk_calls.find({}).sort("created_at", -1).limit(limit)
        records = await cursor.to_list(length=limit)
        for doc in records:
            doc["_id"] = str(doc["_id"])
            if "created_at" in doc and hasattr(doc["created_at"], "isoformat"):
                doc["created_at"] = doc["created_at"].isoformat()

        return {
            "success": True,
            "count": len(records),
            "records": records
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching recent CDRs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cdr/manual")
async def manual_cdr_entry(
    phone_number: str,
    duration_seconds: int,
    disposition: str = "ANSWERED",
    destination: str = "unknown"
):
    """
    Manually add a CDR entry for testing or correction purposes.

    This is useful when Asterisk CDR webhook fails but you need to track a call.
    """
    try:
        if not MONGO_AVAILABLE:
            raise HTTPException(status_code=500, detail="MongoDB not available")

        # Find phone record
        phone_record = await find_phone_by_number(phone_number)
        if not phone_record:
            raise HTTPException(status_code=404, detail=f"Phone number {phone_number} not found in managed phones")

        # Create CDR data
        cdr_data = {
            "uniqueid": f"manual_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "src": phone_number,
            "dst": destination,
            "billsec": duration_seconds,
            "disposition": disposition,
            "duration": duration_seconds
        }

        db = get_database()
        asterisk_calls = db["asterisk_calls"]

        # Process cost
        cost_result = {"cost_deducted": 0, "new_balance": phone_record.get("credit_balance", 0)}
        if disposition == "ANSWERED" and duration_seconds > 0:
            cost_result = await process_cdr_cost(cdr_data, phone_record)

        # Store CDR
        cdr_record = {
            **cdr_data,
            "phone_id": phone_record["id"],
            "phone_number": phone_record.get("number"),
            "created_at": datetime.utcnow(),
            "cost_ghc": cost_result.get("cost_deducted", 0),
            "manual_entry": True
        }
        await asterisk_calls.insert_one(cdr_record)

        return {
            "success": True,
            "message": f"Manual CDR entry created",
            "call_id": cdr_data["uniqueid"],
            "cost_deducted": cost_result.get("cost_deducted"),
            "new_balance": cost_result.get("new_balance")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating manual CDR: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cdr/stats/{phone_number}", response_model=CDRStatsResponse)
async def get_call_stats(
    phone_number: str,
    days: int = Query(default=30, ge=1, le=365, description="Number of days to include"),
    page: int = Query(default=1, ge=1, description="Page number for recent calls"),
    per_page: int = Query(default=20, ge=1, le=100, description="Results per page"),
    include_unanswered: bool = Query(default=False, description="Include unanswered calls"),
):
    """
    Get comprehensive call statistics for a specific phone number.

    Features:
    - Summary statistics (total calls, minutes, cost)
    - Breakdown by outbound destinations
    - Breakdown by inbound sources
    - Daily usage trends
    - Paginated recent calls list
    - Credit balance and remaining minutes

    Uses optimized single-query aggregation with caching.
    """
    try:
        if not MONGO_AVAILABLE:
            raise HTTPException(status_code=500, detail="MongoDB not available")

        db = get_database()
        service = get_cdr_stats_service(db)

        stats = await service.get_stats(
            phone_number=phone_number,
            days=days,
            page=page,
            per_page=per_page,
            include_unanswered=include_unanswered,
        )

        return stats

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching call stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cdr/all-stats")
async def get_all_phone_stats(days: int = 30):
    """
    Get call statistics for all managed phone numbers.

    Returns summary and breakdown for each phone.
    """
    try:
        if not MONGO_AVAILABLE:
            raise HTTPException(status_code=500, detail="MongoDB not available")

        db = get_database()
        asterisk_calls = db["asterisk_calls"]
        phones_collection = db["managed_phone_numbers"]

        # Date range filter
        from_date = datetime.utcnow() - timedelta(days=days)

        # Get all phones
        phones_cursor = phones_collection.find({})
        phones = await phones_cursor.to_list(length=100)

        phone_stats = []
        for phone in phones:
            phone_id = phone.get("id")

            # Get stats for this phone
            stats_pipeline = [
                {
                    "$match": {
                        "phone_id": phone_id,
                        "created_at": {"$gte": from_date},
                        "disposition": "ANSWERED"
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_calls": {"$sum": 1},
                        "total_minutes": {"$sum": {"$divide": ["$billsec_seconds", 60]}},
                        "total_cost": {"$sum": "$cost_ghc"}
                    }
                }
            ]

            stats = {"total_calls": 0, "total_minutes": 0, "total_cost": 0}
            async for result in asterisk_calls.aggregate(stats_pipeline):
                stats = {
                    "total_calls": result.get("total_calls", 0),
                    "total_minutes": round(result.get("total_minutes", 0), 2),
                    "total_cost": round(result.get("total_cost", 0), 2)
                }

            # Top destinations
            dest_pipeline = [
                {
                    "$match": {
                        "phone_id": phone_id,
                        "created_at": {"$gte": from_date},
                        "disposition": "ANSWERED"
                    }
                },
                {
                    "$group": {
                        "_id": "$dst",
                        "minutes": {"$sum": {"$divide": ["$billsec_seconds", 60]}}
                    }
                },
                {"$sort": {"minutes": -1}},
                {"$limit": 5}
            ]

            top_destinations = []
            async for dest in asterisk_calls.aggregate(dest_pipeline):
                top_destinations.append({
                    "number": dest.get("_id"),
                    "minutes": round(dest.get("minutes", 0), 2)
                })

            phone_stats.append({
                "phone_id": phone_id,
                "phone_number": phone.get("number"),
                "provider": phone.get("provider"),
                "credit_balance": phone.get("credit_balance", 0),
                "stats": stats,
                "top_destinations": top_destinations
            })

        return {
            "success": True,
            "period_days": days,
            "phone_count": len(phone_stats),
            "phones": phone_stats
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching all phone stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Asterisk Voice AI Calls ====================

from ..services.asterisk_voice_service import (
    AsteriskVoiceCallRequest,
    AsteriskVoiceCallResponse,
    get_asterisk_voice_service,
)


@router.post("/voice-call/originate", response_model=AsteriskVoiceCallResponse)
async def originate_voice_ai_call(request: AsteriskVoiceCallRequest):
    """
    Originate an AI voice call through Asterisk.

    This is an alternative to VAPI that uses our own infrastructure:
    - Asterisk for call handling
    - Local TTS providers (Kokoro, F5-TTS, etc.)
    - Local ASR (Faster Whisper)
    - Local or external LLM (Ollama, OpenAI, etc.)

    Cost: $0 for TTS/ASR when using local providers.
    """
    service = get_asterisk_voice_service()
    return await service.originate_voice_call(request)


@router.get("/voice-call/{call_id}")
async def get_voice_call_status(call_id: str):
    """Get status of an Asterisk voice AI call."""
    service = get_asterisk_voice_service()
    call = await service.get_call_status(call_id)
    if not call:
        raise HTTPException(status_code=404, detail=f"Call {call_id} not found")
    return call


@router.post("/voice-call/{call_id}/end")
async def end_voice_call(call_id: str):
    """End an active Asterisk voice AI call."""
    service = get_asterisk_voice_service()
    success = await service.end_call(call_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Call {call_id} not found or already ended")
    return {"success": True, "message": f"Call {call_id} ended"}


@router.get("/voice-calls/active")
async def get_active_voice_calls():
    """Get list of active Asterisk voice AI calls."""
    service = get_asterisk_voice_service()
    calls = await service.get_active_calls()
    return {"calls": calls, "count": len(calls)}
