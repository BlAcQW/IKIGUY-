"""
Fraud Detection Admin API

Endpoints for managing fraud detection, reviewing flagged transactions,
and configuring fraud rules.

Author: KasaAI Team
Date: 2025-10-30
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
import logging

from ..auth import get_current_user_mongo
from ..mongo import get_database

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/fraud", tags=["admin", "fraud-detection"])


def is_admin_user(user: dict) -> bool:
    """Check if user has admin privileges."""
    user_email = user.get("email", "")
    admin_emails = [
        "ailabsafrica@gmail.com",
        "admin@ailabsafrica.com",
        "support@ailabsafrica.com",
        "alfred.anyan@gmail.com"
    ]

    return (user_email in admin_emails or
            user.get("user_metadata", {}).get("role") == "admin" or
            user.get("app_metadata", {}).get("role") == "admin")


# ============================================================================
# FRAUD DETECTION ENDPOINTS
# ============================================================================

@router.get("/review-queue")
async def get_fraud_review_queue(
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get transactions flagged for fraud review (ADMIN ONLY).

    Returns transactions that triggered fraud detection rules
    and require manual review before processing.

    Query Params:
        limit: Maximum number of flagged transactions to return (1-200)

    Returns:
        List of fraud checks pending review with details
    """
    # Verify admin access
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required to access fraud review queue"
        )

    try:
        from apps.shared.integration.wallet.fraud_detection_service import FraudDetectionService

        db = get_database()
        fraud_service = FraudDetectionService(db)

        # Get review queue
        checks = await fraud_service.get_review_queue(limit=limit)

        # Convert to dict for response
        checks_data = [
            {
                "id": check.id,
                "transaction_id": check.transaction_id,
                "wallet_id": check.wallet_id,
                "user_id": check.user_id,
                "risk_score": check.risk_score,
                "risk_level": check.risk_level.value,
                "triggered_rules": check.triggered_rules,
                "decision": check.decision.value,
                "action_taken": check.action_taken.value,
                "requires_review": check.requires_review,
                "status": check.status.value,
                "created_at": check.created_at.isoformat() if check.created_at else None,
                "metadata": check.metadata
            }
            for check in checks
        ]

        return {
            "success": True,
            "count": len(checks_data),
            "checks": checks_data
        }

    except Exception as e:
        logger.error(f"Error getting fraud review queue: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get fraud review queue: {str(e)}"
        )


@router.post("/approve/{fraud_check_id}")
async def approve_flagged_transaction(
    fraud_check_id: str,
    notes: Optional[str] = None,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Approve a transaction flagged for fraud review (ADMIN ONLY).

    Marks the fraud check as reviewed and approved, allowing
    the transaction to proceed.

    Path Params:
        fraud_check_id: ID of the fraud check to approve

    Body:
        notes: Optional review notes explaining the approval

    Returns:
        Success confirmation
    """
    # Verify admin access
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required to approve flagged transactions"
        )

    try:
        from apps.shared.integration.wallet.fraud_detection_service import FraudDetectionService

        db = get_database()
        fraud_service = FraudDetectionService(db)

        # Approve transaction
        reviewer_id = current_user.get("id") or current_user.get("sub")
        success = await fraud_service.approve_transaction(
            fraud_check_id=fraud_check_id,
            reviewer_id=reviewer_id,
            notes=notes
        )

        if success:
            logger.info(f"✅ Fraud check {fraud_check_id} approved by {current_user.get('email')}")
            return {
                "success": True,
                "message": "Transaction approved",
                "fraud_check_id": fraud_check_id,
                "reviewed_by": reviewer_id
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Fraud check not found or already reviewed"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving transaction: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to approve transaction: {str(e)}"
        )


@router.post("/reject/{fraud_check_id}")
async def reject_flagged_transaction(
    fraud_check_id: str,
    reason: str,
    notes: Optional[str] = None,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Reject a transaction flagged for fraud review (ADMIN ONLY).

    Marks the fraud check as reviewed and rejected, blocking
    the transaction permanently.

    Path Params:
        fraud_check_id: ID of the fraud check to reject

    Body:
        reason: Reason for rejection (required)
        notes: Optional additional notes

    Returns:
        Success confirmation
    """
    # Verify admin access
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required to reject flagged transactions"
        )

    try:
        from apps.shared.integration.wallet.fraud_detection_service import FraudDetectionService

        db = get_database()
        fraud_service = FraudDetectionService(db)

        # Reject transaction
        reviewer_id = current_user.get("id") or current_user.get("sub")
        success = await fraud_service.reject_transaction(
            fraud_check_id=fraud_check_id,
            reviewer_id=reviewer_id,
            rejection_reason=reason,
            notes=notes
        )

        if success:
            logger.info(f"❌ Fraud check {fraud_check_id} rejected by {current_user.get('email')}: {reason}")
            return {
                "success": True,
                "message": "Transaction rejected",
                "fraud_check_id": fraud_check_id,
                "reviewed_by": reviewer_id,
                "rejection_reason": reason
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Fraud check not found or already reviewed"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting transaction: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reject transaction: {str(e)}"
        )


@router.get("/statistics")
async def get_fraud_statistics(
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get fraud detection statistics (ADMIN ONLY).

    Returns aggregated statistics on fraud checks,
    detection rates, and rule effectiveness.

    Query Params:
        days: Number of days to include (1-365)

    Returns:
        Fraud detection statistics and metrics
    """
    # Verify admin access
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required to view fraud statistics"
        )

    try:
        from datetime import timedelta

        db = get_database()
        start_date = datetime.utcnow() - timedelta(days=days)

        # Get fraud check counts by decision
        pipeline = [
            {"$match": {"created_at": {"$gte": start_date}}},
            {"$group": {
                "_id": "$decision",
                "count": {"$sum": 1},
                "avg_risk_score": {"$avg": "$risk_score"}
            }}
        ]
        decision_stats = await db.fraud_checks.aggregate(pipeline).to_list(length=None)

        # Get counts by risk level
        pipeline = [
            {"$match": {"created_at": {"$gte": start_date}}},
            {"$group": {
                "_id": "$risk_level",
                "count": {"$sum": 1}
            }}
        ]
        risk_level_stats = await db.fraud_checks.aggregate(pipeline).to_list(length=None)

        # Get most triggered rules
        pipeline = [
            {"$match": {"created_at": {"$gte": start_date}}},
            {"$unwind": "$triggered_rules"},
            {"$group": {
                "_id": "$triggered_rules",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        rule_stats = await db.fraud_checks.aggregate(pipeline).to_list(length=None)

        # Get pending review count
        pending_count = await db.fraud_checks.count_documents({
            "requires_review": True,
            "status": "pending"
        })

        return {
            "success": True,
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": datetime.utcnow().isoformat(),
            "statistics": {
                "pending_review": pending_count,
                "by_decision": {item["_id"]: item for item in decision_stats},
                "by_risk_level": {item["_id"]: item for item in risk_level_stats},
                "top_triggered_rules": rule_stats
            }
        }

    except Exception as e:
        logger.error(f"Error getting fraud statistics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get fraud statistics: {str(e)}"
        )


@router.get("/rules")
async def get_fraud_rules(
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get all configured fraud detection rules (ADMIN ONLY).

    Returns list of active fraud detection rules with their
    conditions and actions.

    Returns:
        List of fraud rules
    """
    # Verify admin access
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required to view fraud rules"
        )

    try:
        from apps.shared.integration.wallet.fraud_detection_service import FraudDetectionService

        db = get_database()
        fraud_service = FraudDetectionService(db)

        # Get default rules
        default_rules = fraud_service.default_rules

        # Convert to dict for response
        rules_data = [
            {
                "id": rule.id,
                "name": rule.name,
                "description": rule.description,
                "rule_type": rule.rule_type.value,
                "condition": rule.condition,
                "risk_score": rule.risk_score,
                "action": rule.action.value,
                "is_active": rule.is_active
            }
            for rule in default_rules
        ]

        return {
            "success": True,
            "count": len(rules_data),
            "rules": rules_data
        }

    except Exception as e:
        logger.error(f"Error getting fraud rules: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get fraud rules: {str(e)}"
        )
