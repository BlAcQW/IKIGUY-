"""
Call Completion Webhook Handler
Handles VAPI and other provider call completion webhooks
Auto-deducts credit from phone numbers and integrates with billing system
"""

import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# Import phone manager for credit deduction
from .phone_numbers import phone_manager

# Import billing service for organization billing
try:
    from apps.shared.services.billing_service import get_billing_service
    BILLING_AVAILABLE = True
except ImportError:
    BILLING_AVAILABLE = False
    logger.warning("Billing service not available")

# Import usage calculator
try:
    from apps.shared.integration.usage_calculator import UsageCalculator, ServiceType
    USAGE_CALCULATOR_AVAILABLE = True
except ImportError:
    USAGE_CALCULATOR_AVAILABLE = False
    logger.warning("Usage calculator not available")


class CallCompletionWebhook(BaseModel):
    """VAPI call completion webhook payload"""
    call_id: str
    status: str  # completed, failed, no-answer, busy, cancelled
    duration_seconds: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    from_number: Optional[str] = None
    to_number: Optional[str] = None
    assistant_id: Optional[str] = None
    phone_number_id: Optional[str] = None  # VAPI phone number ID

    # Cost information (if available from VAPI)
    cost: Optional[float] = None
    cost_currency: Optional[str] = "USD"

    # Campaign information
    campaign_id: Optional[str] = None
    organization_id: Optional[str] = None

    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)


async def process_call_completion(
    webhook: CallCompletionWebhook,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Process call completion and deduct credit from phone number.

    Args:
        webhook: Call completion webhook data
        background_tasks: FastAPI background tasks

    Returns:
        Processing result
    """
    result = {
        "call_id": webhook.call_id,
        "status": "processed",
        "actions": []
    }

    try:
        # Only process completed calls with duration
        if webhook.status not in ["completed", "answered"] or not webhook.duration_seconds:
            logger.info(f"Skipping call {webhook.call_id}: status={webhook.status}, duration={webhook.duration_seconds}")
            result["status"] = "skipped"
            result["reason"] = "No billable duration"
            return result

        # Find the phone number by ID or number
        phone = None
        if webhook.phone_number_id and webhook.phone_number_id in phone_manager.phone_numbers:
            phone = phone_manager.phone_numbers[webhook.phone_number_id]
        elif webhook.from_number:
            # Search by phone number
            for p in phone_manager.phone_numbers.values():
                if p.number == webhook.from_number:
                    phone = p
                    break

        if not phone:
            logger.warning(f"Phone number not found for call {webhook.call_id}")
            result["status"] = "warning"
            result["reason"] = "Phone number not found"
            return result

        # Calculate cost based on duration and phone's cost_per_minute
        duration_minutes = webhook.duration_seconds / 60.0
        cost = duration_minutes * phone.cost_per_minute

        # Deduct credit from phone number
        try:
            transaction = phone_manager.deduct_credit(
                phone_number_id=phone.id,
                amount=cost,
                call_id=webhook.call_id,
                call_duration_seconds=webhook.duration_seconds,
                campaign_id=webhook.campaign_id
            )

            result["actions"].append({
                "type": "credit_deduction",
                "phone_id": phone.id,
                "amount": cost,
                "currency": phone.currency,
                "transaction_id": transaction.id,
                "balance_after": phone.credit_balance
            })

            logger.info(
                f"Deducted {cost} {phone.currency} from {phone.number} "
                f"for call {webhook.call_id}. Balance: {phone.credit_balance}"
            )

            # Check for low balance alert
            if phone.low_balance_threshold and phone.credit_balance < phone.low_balance_threshold:
                result["actions"].append({
                    "type": "low_balance_alert",
                    "phone_id": phone.id,
                    "balance": phone.credit_balance,
                    "threshold": phone.low_balance_threshold
                })
                logger.warning(
                    f"Low balance alert for {phone.number}: "
                    f"{phone.credit_balance} < {phone.low_balance_threshold}"
                )

        except Exception as e:
            logger.error(f"Failed to deduct credit: {e}")
            result["actions"].append({
                "type": "credit_deduction_error",
                "error": str(e)
            })

        # Integrate with billing service (if available and organization_id provided)
        if BILLING_AVAILABLE and webhook.organization_id:
            background_tasks.add_task(
                record_billing,
                webhook=webhook,
                phone=phone,
                cost=cost
            )
            result["actions"].append({
                "type": "billing_queued",
                "organization_id": webhook.organization_id
            })

        return result

    except Exception as e:
        logger.error(f"Error processing call completion: {e}")
        result["status"] = "error"
        result["error"] = str(e)
        return result


async def record_billing(
    webhook: CallCompletionWebhook,
    phone: Any,
    cost: float
):
    """
    Record billing for organization (background task).

    Args:
        webhook: Call completion webhook
        phone: Phone number object
        cost: Calculated cost
    """
    try:
        # Get MongoDB client
        mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017/")
        client = AsyncIOMotorClient(mongodb_url)
        db_name = os.getenv("MONGODB_DB_NAME", "kasaai_core")
        db = client[db_name]

        # Get billing service
        billing_service = get_billing_service(db)

        # Create billing record
        call_doc = {
            "call_id": webhook.call_id,
            "duration": webhook.duration_seconds,
            "vapi_cost": cost,
            "started_at": webhook.start_time,
            "ended_at": webhook.end_time,
            "status": webhook.status,
            "customer_number": webhook.to_number,
            "automation_id": webhook.campaign_id,
            "assistant_id": webhook.assistant_id,
            "metadata": webhook.metadata
        }

        billing_id = await billing_service.create_billing_record_from_call(
            call_doc=call_doc,
            organization_id=webhook.organization_id,
            automation_name=webhook.metadata.get("campaign_name", "Unknown Campaign")
        )

        if billing_id:
            logger.info(f"Created billing record {billing_id} for call {webhook.call_id}")

        # Close MongoDB connection
        client.close()

    except Exception as e:
        logger.error(f"Error recording billing: {e}")


# Webhook Endpoints

@router.post("/vapi/call-completed")
async def vapi_call_completed(
    webhook: CallCompletionWebhook,
    background_tasks: BackgroundTasks
):
    """
    VAPI call completion webhook endpoint.
    Automatically deducts credit from phone number.
    """
    logger.info(f"Received VAPI call completion webhook for call {webhook.call_id}")

    result = await process_call_completion(webhook, background_tasks)

    return {
        "success": True,
        "message": "Call completion processed",
        "result": result
    }


@router.post("/generic/call-completed")
async def generic_call_completed(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Generic call completion webhook endpoint for other providers.
    Accepts flexible JSON payload and maps to CallCompletionWebhook.
    """
    try:
        data = await request.json()
        logger.info(f"Received generic call completion webhook: {data.get('call_id', 'unknown')}")

        # Map generic webhook to our format
        webhook = CallCompletionWebhook(
            call_id=data.get("call_id") or data.get("id") or data.get("sid", "unknown"),
            status=data.get("status", "completed"),
            duration_seconds=data.get("duration") or data.get("duration_seconds"),
            start_time=data.get("start_time") or data.get("started_at"),
            end_time=data.get("end_time") or data.get("ended_at"),
            from_number=data.get("from_number") or data.get("from") or data.get("caller"),
            to_number=data.get("to_number") or data.get("to") or data.get("callee"),
            phone_number_id=data.get("phone_number_id") or data.get("phone_id"),
            campaign_id=data.get("campaign_id") or data.get("automation_id"),
            organization_id=data.get("organization_id") or data.get("tenant_id"),
            cost=data.get("cost") or data.get("price"),
            metadata=data
        )

        result = await process_call_completion(webhook, background_tasks)

        return {
            "success": True,
            "message": "Call completion processed",
            "result": result
        }

    except Exception as e:
        logger.error(f"Error processing generic webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def webhook_health():
    """Health check endpoint for webhook service"""
    return {
        "status": "healthy",
        "billing_available": BILLING_AVAILABLE,
        "usage_calculator_available": USAGE_CALCULATOR_AVAILABLE,
        "phone_manager_loaded": len(phone_manager.phone_numbers) > 0
    }
