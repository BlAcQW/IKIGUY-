"""
Internal Usage Tracking API

Provides usage analytics for billing and monitoring purposes.
Organization-scoped and multi-tenant aware.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from datetime import datetime, timedelta
from bson import ObjectId

from ..auth import get_current_user_mongo
from ..middleware.organization_context import (
    get_organization_context,
    validate_organization_access,
    get_user_organization_filter
)
from ..mongo import get_collection

router = APIRouter(prefix="/internal", tags=["internal"])


@router.get("/usage")
async def get_usage_data(
    request: Request,
    tenant_id: Optional[str] = Query(None, description="Legacy tenant ID parameter"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    current_user: Dict[str, Any] = Depends(get_current_user_mongo),
    org_id: Optional[str] = Depends(get_organization_context)
):
    """
    Get usage analytics for billing purposes.

    Returns:
    - minutes: Total call minutes
    - stt_calls: Number of speech-to-text calls
    - tts_calls: Number of text-to-speech calls
    - telephony_cost: Total telephony costs
    - stt_cost: STT costs
    - tts_cost: TTS costs
    - automation_cost: Automation execution costs
    - automation_calls: Number of automation calls

    Organization-scoped. Requires authentication.
    """
    try:
        # Validate organization access
        if org_id:
            await validate_organization_access(org_id, current_user)

        # Get organization filter
        user_id = current_user.get("id") or current_user.get("sub")
        is_universal_admin = current_user.get("is_universal_admin", False)

        # Build query with organization filter
        org_filter = get_user_organization_filter(current_user, org_id) if not is_universal_admin else {}

        # Parse date range
        if not end_date:
            end_dt = datetime.utcnow()
        else:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

        if not start_date:
            start_dt = end_dt - timedelta(days=30)  # Default to 30 days
        else:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))

        # Get vapi_calls collection for call analytics
        vapi_calls = get_collection("vapi_calls")

        # Build query
        query = {**org_filter}
        query["created_at"] = {"$gte": start_dt, "$lte": end_dt}

        # Aggregate call data
        pipeline = [
            {"$match": query},
            {"$group": {
                "_id": None,
                "total_calls": {"$sum": 1},
                "total_duration": {"$sum": {"$ifNull": ["$duration", 0]}},
                "total_cost": {"$sum": {"$ifNull": ["$vonage_cost", 0]}},
                # Count different call types based on metadata
                "telephony_calls": {
                    "$sum": {
                        "$cond": [
                            {"$ne": ["$customer_phone", None]},
                            1,
                            0
                        ]
                    }
                }
            }}
        ]

        result_cursor = vapi_calls.aggregate(pipeline)
        result_list = await result_cursor.to_list(length=1)
        result = result_list[0] if result_list else {}

        # Calculate metrics
        total_calls = result.get("total_calls", 0)
        total_duration = result.get("total_duration", 0)  # in seconds
        total_cost = result.get("total_cost", 0)
        telephony_calls = result.get("telephony_calls", 0)

        # Convert duration to minutes
        minutes = total_duration / 60 if total_duration else 0

        # Estimate cost breakdown (simplified - can be enhanced with actual data)
        # Assuming typical cost distribution for voice AI services
        telephony_cost = total_cost * 0.6 if total_cost else 0  # 60% telephony
        stt_cost = total_cost * 0.2 if total_cost else 0  # 20% STT
        tts_cost = total_cost * 0.15 if total_cost else 0  # 15% TTS
        automation_cost = total_cost * 0.05 if total_cost else 0  # 5% automation/infra

        return {
            "minutes": round(minutes, 2),
            "stt_calls": total_calls,  # Every call uses STT
            "tts_calls": total_calls,  # Every call uses TTS
            "telephony_cost": round(telephony_cost, 2),
            "stt_cost": round(stt_cost, 2),
            "tts_cost": round(tts_cost, 2),
            "automation_cost": round(automation_cost, 2),
            "automation_calls": total_calls,
            "total_cost": round(total_cost, 2),
            "total_calls": total_calls,
            "period": {
                "start_date": start_dt.isoformat(),
                "end_date": end_dt.isoformat()
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get usage data: {str(e)}")
