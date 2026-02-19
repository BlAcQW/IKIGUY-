"""
Fraud Detection Service for Wallet System

This service detects and prevents fraudulent transactions using pattern analysis,
velocity checks, and anomaly detection.

Author: KasaAI Team
Date: 2025-10-27
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from decimal import Decimal
import uuid

from motor.motor_asyncio import AsyncIOMotorDatabase

from .fraud_models import (
    FraudRule,
    FraudCheck,
    UserRiskProfile,
    VelocityCheck,
    AmountAnomalyCheck,
    PatternAnomalyCheck,
    FraudRuleType,
    FraudAction,
    FraudCheckDecision,
    FraudCheckStatus,
    RiskLevel,
)
from .models import Transaction, Wallet, TransactionType, TransactionStatus


logger = logging.getLogger(__name__)


class FraudDetectionService:
    """
    Service for fraud detection and prevention.

    Analyzes transactions for suspicious patterns using velocity checks,
    amount anomalies, and behavioral pattern analysis.
    """

    def __init__(self, database: AsyncIOMotorDatabase):
        """
        Initialize fraud detection service.

        Args:
            database: MongoDB database connection
        """
        self.db = database

        # Collections
        self.fraud_checks_collection = database["fraud_checks"]
        self.fraud_rules_collection = database["fraud_rules"]
        self.user_risk_profiles_collection = database["user_risk_profiles"]
        self.transactions_collection = database["transactions"]

        # Default fraud rules (can be overridden in database)
        self.default_rules = self._get_default_rules()

        logger.info("FraudDetectionService initialized")

    # ==================== Main Fraud Check ====================

    async def check_transaction(
        self,
        transaction: Transaction,
        wallet: Wallet,
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> FraudCheck:
        """
        Perform fraud check on a transaction.

        Args:
            transaction: Transaction to check
            wallet: Associated wallet
            additional_context: Additional context (IP, device, etc.)

        Returns:
            FraudCheck with decision and risk score
        """
        try:
            # Get or create user risk profile
            risk_profile = await self.get_user_risk_profile(wallet.user_id, wallet.id)

            # Initialize fraud check
            fraud_check = FraudCheck(
                id=str(uuid.uuid4()),
                transaction_id=transaction.id,
                wallet_id=wallet.id,
                user_id=wallet.user_id,
                risk_score=0,
                risk_level=RiskLevel.LOW,
                triggered_rules=[],
                rule_details=[],
                decision=FraudCheckDecision.APPROVED,
                action_taken=FraudAction.APPROVE,
                transaction_data={
                    "amount": float(transaction.amount),
                    "currency": transaction.currency.value,
                    "type": transaction.transaction_type.value,
                },
                user_risk_profile={
                    "total_transactions": risk_profile.total_transactions,
                    "risk_score": risk_profile.risk_score,
                    "trusted": risk_profile.trusted,
                },
            )

            # Skip checks for trusted users
            if risk_profile.trusted:
                logger.info(f"User {wallet.user_id} is trusted, skipping fraud checks")
                await self.fraud_checks_collection.insert_one(fraud_check.dict())
                return fraud_check

            # Run fraud checks
            total_risk_score = 0
            triggered_rules = []

            # 1. Velocity checks
            velocity_score, velocity_rules = await self._check_velocity(
                wallet.user_id, transaction
            )
            total_risk_score += velocity_score
            triggered_rules.extend(velocity_rules)

            # 2. Amount anomaly detection
            amount_score, amount_rules = await self._check_amount_anomaly(
                wallet.user_id, transaction, risk_profile
            )
            total_risk_score += amount_score
            triggered_rules.extend(amount_rules)

            # 3. Pattern analysis
            pattern_score, pattern_rules = await self._check_pattern_anomaly(
                wallet.user_id, wallet, transaction, risk_profile
            )
            total_risk_score += pattern_score
            triggered_rules.extend(pattern_rules)

            # 4. Apply custom rules from database
            custom_score, custom_rules = await self._check_custom_rules(
                transaction, wallet, risk_profile, additional_context
            )
            total_risk_score += custom_score
            triggered_rules.extend(custom_rules)

            # Cap risk score at 100
            total_risk_score = min(total_risk_score, 100)

            # Update fraud check with results
            fraud_check.risk_score = total_risk_score
            fraud_check.risk_level = self._calculate_risk_level(total_risk_score)
            fraud_check.triggered_rules = [r["rule_id"] for r in triggered_rules]
            fraud_check.rule_details = triggered_rules

            # Determine action based on risk score
            fraud_check.decision, fraud_check.action_taken = self._determine_action(
                total_risk_score, triggered_rules
            )

            # Set review flag for medium/high risk
            if fraud_check.risk_score >= 31:
                fraud_check.requires_review = True
                fraud_check.status = FraudCheckStatus.PENDING

            # Save fraud check
            await self.fraud_checks_collection.insert_one(fraud_check.dict())

            # Update user risk profile
            await self._update_user_risk_profile_after_check(
                wallet.user_id, transaction, fraud_check
            )

            logger.info(
                f"Fraud check completed: transaction={transaction.id}, "
                f"risk_score={total_risk_score}, decision={fraud_check.decision.value}"
            )

            return fraud_check

        except Exception as e:
            logger.error(f"Error in fraud check: {e}")
            # Return a safe default (approve with low risk)
            return FraudCheck(
                id=str(uuid.uuid4()),
                transaction_id=transaction.id,
                wallet_id=wallet.id,
                user_id=wallet.user_id,
                risk_score=0,
                risk_level=RiskLevel.LOW,
                decision=FraudCheckDecision.APPROVED,
                action_taken=FraudAction.APPROVE,
            )

    # ==================== Velocity Checks ====================

    async def _check_velocity(
        self, user_id: str, transaction: Transaction
    ) -> Tuple[int, List[Dict[str, Any]]]:
        """
        Check transaction velocity (frequency).

        Returns:
            Tuple of (risk_score, triggered_rules)
        """
        risk_score = 0
        triggered_rules = []

        now = datetime.utcnow()

        # Count transactions in different time windows
        windows = [
            ("5_minutes", 5, 3, 30),  # More than 3 in 5 min = +30 risk
            ("1_hour", 60, 10, 20),  # More than 10 in 1 hour = +20 risk
            ("24_hours", 24 * 60, 50, 15),  # More than 50 in 24 hours = +15 risk
        ]

        for window_name, minutes, threshold, score in windows:
            time_window_start = now - timedelta(minutes=minutes)

            count = await self.transactions_collection.count_documents(
                {
                    "user_id": user_id,
                    "created_at": {"$gte": time_window_start},
                    "status": {"$in": [TransactionStatus.COMPLETED.value, TransactionStatus.PENDING.value]},
                }
            )

            if count >= threshold:
                risk_score += score
                triggered_rules.append(
                    {
                        "rule_id": f"velocity_{window_name}",
                        "rule_name": f"High Velocity {window_name.replace('_', ' ').title()}",
                        "rule_type": FraudRuleType.VELOCITY.value,
                        "score": score,
                        "details": {
                            "transaction_count": count,
                            "threshold": threshold,
                            "time_window_minutes": minutes,
                        },
                    }
                )

        # Check for failed transaction velocity
        failed_count_1h = await self.transactions_collection.count_documents(
            {
                "user_id": user_id,
                "created_at": {"$gte": now - timedelta(hours=1)},
                "status": TransactionStatus.FAILED.value,
            }
        )

        if failed_count_1h >= 5:
            risk_score += 50
            triggered_rules.append(
                {
                    "rule_id": "velocity_failed_attempts",
                    "rule_name": "Multiple Failed Attempts",
                    "rule_type": FraudRuleType.VELOCITY.value,
                    "score": 50,
                    "details": {
                        "failed_count": failed_count_1h,
                        "threshold": 5,
                        "time_window_hours": 1,
                    },
                }
            )

        return risk_score, triggered_rules

    # ==================== Amount Anomaly Detection ====================

    async def _check_amount_anomaly(
        self, user_id: str, transaction: Transaction, risk_profile: UserRiskProfile
    ) -> Tuple[int, List[Dict[str, Any]]]:
        """
        Check for unusual transaction amounts.

        Returns:
            Tuple of (risk_score, triggered_rules)
        """
        risk_score = 0
        triggered_rules = []

        amount = transaction.amount

        # Check if transaction amount is significantly higher than average
        if risk_profile.average_amount > 0:
            multiplier = float(amount / risk_profile.average_amount)

            if multiplier >= 5:
                score = 40
                risk_score += score
                triggered_rules.append(
                    {
                        "rule_id": "amount_5x_average",
                        "rule_name": "Amount 5x Average",
                        "rule_type": FraudRuleType.AMOUNT.value,
                        "score": score,
                        "details": {
                            "amount": float(amount),
                            "average": float(risk_profile.average_amount),
                            "multiplier": multiplier,
                        },
                    }
                )

        # Check for large transactions on new accounts
        account_age_days = (datetime.utcnow() - risk_profile.account_created_at).days

        if account_age_days < 7 and amount > 1000:
            score = 60
            risk_score += score
            triggered_rules.append(
                {
                    "rule_id": "large_amount_new_account",
                    "rule_name": "Large Transaction on New Account",
                    "rule_type": FraudRuleType.AMOUNT.value,
                    "score": score,
                    "details": {
                        "amount": float(amount),
                        "account_age_days": account_age_days,
                        "threshold_amount": 1000,
                    },
                }
            )

        # Check for withdrawal of large percentage of balance
        if transaction.transaction_type == TransactionType.WITHDRAWAL:
            # Get current wallet balance
            wallet_doc = await self.db.wallets.find_one({"user_id": user_id})
            if wallet_doc:
                balance = Decimal(str(wallet_doc.get("balance", 0)))
                if balance > 0:
                    withdrawal_percentage = float((amount / balance) * 100)

                    if withdrawal_percentage >= 80:
                        score = 30
                        risk_score += score
                        triggered_rules.append(
                            {
                                "rule_id": "withdrawal_large_percentage",
                                "rule_name": "Withdrawal >80% of Balance",
                                "rule_type": FraudRuleType.AMOUNT.value,
                                "score": score,
                                "details": {
                                    "amount": float(amount),
                                    "balance": float(balance),
                                    "percentage": withdrawal_percentage,
                                },
                            }
                        )

        return risk_score, triggered_rules

    # ==================== Pattern Analysis ====================

    async def _check_pattern_anomaly(
        self,
        user_id: str,
        wallet: Wallet,
        transaction: Transaction,
        risk_profile: UserRiskProfile,
    ) -> Tuple[int, List[Dict[str, Any]]]:
        """
        Check for unusual behavioral patterns.

        Returns:
            Tuple of (risk_score, triggered_rules)
        """
        risk_score = 0
        triggered_rules = []

        # Check transaction time (unusual hours)
        current_hour = datetime.utcnow().hour
        if current_hour >= 2 and current_hour <= 5:  # 2 AM - 5 AM
            score = 20
            risk_score += score
            triggered_rules.append(
                {
                    "rule_id": "pattern_unusual_time",
                    "rule_name": "Transaction at Unusual Time",
                    "rule_type": FraudRuleType.PATTERN.value,
                    "score": score,
                    "details": {
                        "hour": current_hour,
                        "typical_hours": risk_profile.common_transaction_times,
                    },
                }
            )

        # Check for rapid account creation + large transaction
        account_age_minutes = (
            datetime.utcnow() - risk_profile.account_created_at
        ).total_seconds() / 60

        if account_age_minutes < 60 and transaction.amount > 100:
            score = 70
            risk_score += score
            triggered_rules.append(
                {
                    "rule_id": "pattern_rapid_transaction",
                    "rule_name": "Rapid Account Creation + Large Transaction",
                    "rule_type": FraudRuleType.PATTERN.value,
                    "score": score,
                    "details": {
                        "account_age_minutes": account_age_minutes,
                        "amount": float(transaction.amount),
                    },
                }
            )

        # Check for multiple payment methods added recently
        payment_methods_count = await self.db.payment_methods.count_documents(
            {
                "wallet_id": wallet.id,
                "created_at": {"$gte": datetime.utcnow() - timedelta(hours=24)},
                "is_active": True,
            }
        )

        if payment_methods_count >= 3:
            score = 40
            risk_score += score
            triggered_rules.append(
                {
                    "rule_id": "pattern_multiple_payment_methods",
                    "rule_name": "Multiple Payment Methods Added in 24h",
                    "rule_type": FraudRuleType.PATTERN.value,
                    "score": score,
                    "details": {
                        "payment_methods_count": payment_methods_count,
                        "threshold": 3,
                    },
                }
            )

        return risk_score, triggered_rules

    # ==================== Custom Rules ====================

    async def _check_custom_rules(
        self,
        transaction: Transaction,
        wallet: Wallet,
        risk_profile: UserRiskProfile,
        additional_context: Optional[Dict[str, Any]],
    ) -> Tuple[int, List[Dict[str, Any]]]:
        """
        Check custom rules defined in database.

        Returns:
            Tuple of (risk_score, triggered_rules)
        """
        risk_score = 0
        triggered_rules = []

        # Get enabled custom rules
        cursor = self.fraud_rules_collection.find({"enabled": True}).sort("priority", -1)

        async for rule_doc in cursor:
            rule = FraudRule(**rule_doc)

            # Evaluate rule condition
            if self._evaluate_rule_condition(
                rule, transaction, wallet, risk_profile, additional_context
            ):
                risk_score += rule.risk_score
                triggered_rules.append(
                    {
                        "rule_id": rule.id,
                        "rule_name": rule.name,
                        "rule_type": rule.rule_type.value,
                        "score": rule.risk_score,
                        "details": rule.condition,
                    }
                )

        return risk_score, triggered_rules

    def _evaluate_rule_condition(
        self,
        rule: FraudRule,
        transaction: Transaction,
        wallet: Wallet,
        risk_profile: UserRiskProfile,
        additional_context: Optional[Dict[str, Any]],
    ) -> bool:
        """
        Evaluate if a rule condition is met.

        This is a simplified version. In production, you'd use a more sophisticated
        rule engine.
        """
        try:
            condition = rule.condition

            # Example: Check if amount exceeds threshold
            if "amount_threshold" in condition:
                if transaction.amount > Decimal(str(condition["amount_threshold"])):
                    return True

            # Example: Check if user has minimum transaction count
            if "min_transactions" in condition:
                if risk_profile.total_transactions < condition["min_transactions"]:
                    return True

            # Add more condition types as needed

            return False

        except Exception as e:
            logger.error(f"Error evaluating rule {rule.id}: {e}")
            return False

    # ==================== Risk Profile Management ====================

    async def get_user_risk_profile(
        self, user_id: str, wallet_id: str
    ) -> UserRiskProfile:
        """
        Get or create user's risk profile.

        Args:
            user_id: User ID
            wallet_id: Wallet ID

        Returns:
            UserRiskProfile
        """
        try:
            profile_data = await self.user_risk_profiles_collection.find_one(
                {"user_id": user_id}
            )

            if profile_data:
                return UserRiskProfile(**profile_data)

            # Create new profile
            new_profile = UserRiskProfile(
                user_id=user_id,
                wallet_id=wallet_id,
                account_created_at=datetime.utcnow(),
            )

            await self.user_risk_profiles_collection.insert_one(new_profile.dict())

            return new_profile

        except Exception as e:
            logger.error(f"Error getting risk profile for user {user_id}: {e}")
            # Return default profile
            return UserRiskProfile(
                user_id=user_id,
                wallet_id=wallet_id,
                account_created_at=datetime.utcnow(),
            )

    async def _update_user_risk_profile_after_check(
        self, user_id: str, transaction: Transaction, fraud_check: FraudCheck
    ):
        """Update user risk profile after fraud check."""
        try:
            # Increment fraud check count
            updates = {
                "$inc": {
                    "fraud_checks_count": 1,
                },
                "$set": {
                    "updated_at": datetime.utcnow(),
                    "risk_score": fraud_check.risk_score,
                    "risk_level": fraud_check.risk_level.value,
                },
            }

            # Increment flagged/blocked counts
            if fraud_check.decision == FraudCheckDecision.FLAGGED:
                updates["$inc"]["flagged_transactions_count"] = 1
            elif fraud_check.decision == FraudCheckDecision.BLOCKED:
                updates["$inc"]["blocked_transactions_count"] = 1

            await self.user_risk_profiles_collection.update_one(
                {"user_id": user_id}, updates, upsert=True
            )

        except Exception as e:
            logger.error(f"Error updating risk profile for user {user_id}: {e}")

    # ==================== Helper Methods ====================

    def _calculate_risk_level(self, risk_score: int) -> RiskLevel:
        """Calculate risk level from score."""
        if risk_score <= 30:
            return RiskLevel.LOW
        elif risk_score <= 60:
            return RiskLevel.MEDIUM
        elif risk_score <= 80:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL

    def _determine_action(
        self, risk_score: int, triggered_rules: List[Dict[str, Any]]
    ) -> Tuple[FraudCheckDecision, FraudAction]:
        """
        Determine action to take based on risk score.

        Returns:
            Tuple of (decision, action)
        """
        if risk_score <= 30:
            return FraudCheckDecision.APPROVED, FraudAction.APPROVE

        elif risk_score <= 60:
            return FraudCheckDecision.FLAGGED, FraudAction.ALERT

        elif risk_score <= 80:
            return FraudCheckDecision.PENDING_REVIEW, FraudAction.REVIEW

        else:  # 81-100
            return FraudCheckDecision.BLOCKED, FraudAction.BLOCK

    def _get_default_rules(self) -> List[FraudRule]:
        """Get default fraud detection rules."""
        return [
            FraudRule(
                id="default_velocity_5min",
                name="High Velocity 5 Minutes",
                description="More than 3 transactions in 5 minutes",
                rule_type=FraudRuleType.VELOCITY,
                condition={"transaction_count": 3, "time_window_minutes": 5},
                risk_score=30,
                action=FraudAction.ALERT,
            ),
            FraudRule(
                id="default_amount_5x",
                name="Amount 5x Average",
                description="Transaction amount is 5x user's average",
                rule_type=FraudRuleType.AMOUNT,
                condition={"multiplier": 5},
                risk_score=40,
                action=FraudAction.REVIEW,
            ),
            FraudRule(
                id="default_new_account_large",
                name="Large Transaction on New Account",
                description="Transaction > $1000 on account < 7 days old",
                rule_type=FraudRuleType.PATTERN,
                condition={"amount_threshold": 1000, "account_age_days": 7},
                risk_score=60,
                action=FraudAction.REVIEW,
            ),
        ]

    # ==================== Review Queue ====================

    async def get_review_queue(self, limit: int = 50) -> List[FraudCheck]:
        """
        Get fraud checks pending manual review.

        Args:
            limit: Maximum number of checks to return

        Returns:
            List of FraudCheck objects
        """
        try:
            cursor = (
                self.fraud_checks_collection.find(
                    {
                        "requires_review": True,
                        "status": FraudCheckStatus.PENDING.value,
                    }
                )
                .sort("created_at", -1)
                .limit(limit)
            )

            checks = []
            async for check_data in cursor:
                checks.append(FraudCheck(**check_data))

            return checks

        except Exception as e:
            logger.error(f"Error getting review queue: {e}")
            return []

    async def approve_transaction(
        self, fraud_check_id: str, reviewer_id: str, notes: Optional[str] = None
    ) -> bool:
        """
        Approve a flagged transaction.

        Args:
            fraud_check_id: Fraud check ID
            reviewer_id: ID of reviewer
            notes: Optional review notes

        Returns:
            True if successful
        """
        try:
            result = await self.fraud_checks_collection.update_one(
                {"id": fraud_check_id},
                {
                    "$set": {
                        "status": FraudCheckStatus.REVIEWED.value,
                        "decision": FraudCheckDecision.APPROVED.value,
                        "reviewed_by": reviewer_id,
                        "reviewed_at": datetime.utcnow(),
                        "review_notes": notes,
                        "review_decision": "approved",
                    }
                },
            )

            return result.modified_count > 0

        except Exception as e:
            logger.error(f"Error approving transaction {fraud_check_id}: {e}")
            return False

    async def reject_transaction(
        self, fraud_check_id: str, reviewer_id: str, notes: Optional[str] = None
    ) -> bool:
        """
        Reject a flagged transaction.

        Args:
            fraud_check_id: Fraud check ID
            reviewer_id: ID of reviewer
            notes: Optional review notes

        Returns:
            True if successful
        """
        try:
            result = await self.fraud_checks_collection.update_one(
                {"id": fraud_check_id},
                {
                    "$set": {
                        "status": FraudCheckStatus.REVIEWED.value,
                        "decision": FraudCheckDecision.BLOCKED.value,
                        "reviewed_by": reviewer_id,
                        "reviewed_at": datetime.utcnow(),
                        "review_notes": notes,
                        "review_decision": "rejected",
                    }
                },
            )

            return result.modified_count > 0

        except Exception as e:
            logger.error(f"Error rejecting transaction {fraud_check_id}: {e}")
            return False
