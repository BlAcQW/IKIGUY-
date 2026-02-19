"""
Affiliate Commission Processor

Handles automatic commission calculation and distribution after successful
wallet transactions. Integrates with the affiliate service to attribute
earnings to referrers across multiple tiers.

Usage:
    After a successful wallet top-up/purchase, call:
    await process_transaction_commission(user_id, organization_id, amount, transaction_id)
"""

import logging
from typing import Optional, List, Dict, Any
from decimal import Decimal
from .affiliate_service import AffiliateService
from ..models.affiliate import CommissionRecord
from ..mongo import get_database

logger = logging.getLogger(__name__)


class AffiliateCommissionProcessor:
    """
    Processes affiliate commissions after successful transactions.

    This class provides a clean integration point for triggering
    commission calculations without tightly coupling the affiliate
    system to the payment processing flow.
    """

    def __init__(self, db=None):
        self.db = db
        self.affiliate_service = None  # Lazy initialization

    def _get_affiliate_service(self) -> AffiliateService:
        """Get or create affiliate service instance."""
        if self.affiliate_service is None:
            if self.db is None:
                self.db = get_database()
            self.affiliate_service = AffiliateService(self.db)
        return self.affiliate_service

    async def process_transaction_commission(
        self,
        user_id: str,
        organization_id: str,
        transaction_amount: Decimal,
        transaction_id: str,
        transaction_type: str = "wallet_topup"
    ) -> Dict[str, Any]:
        """
        Process affiliate commissions for a completed transaction.

        This method should be called after a successful wallet top-up or
        purchase to calculate and attribute commissions to the affiliate
        network.

        Args:
            user_id: ID of the user making the purchase
            organization_id: Organization ID
            transaction_amount: Amount of the transaction (in USD)
            transaction_id: Unique transaction identifier
            transaction_type: Type of transaction (wallet_topup, subscription, etc.)

        Returns:
            Dictionary containing:
                - success: bool
                - commissions_calculated: int (number of commission records created)
                - total_commission_amount: Decimal
                - commission_records: List[CommissionRecord]
                - error: Optional error message

        Example:
            >>> result = await processor.process_transaction_commission(
            ...     user_id="user123",
            ...     organization_id="org456",
            ...     transaction_amount=Decimal("100.00"),
            ...     transaction_id="txn789"
            ... )
            >>> print(f"Created {result['commissions_calculated']} commission records")
        """
        try:
            logger.info(
                f"Processing commission for transaction {transaction_id}: "
                f"user={user_id}, amount=${transaction_amount}"
            )

            # Get affiliate service instance
            affiliate_service = self._get_affiliate_service()

            # Check if user is a referred user (has an attribution record)
            # If not, no commissions to process
            attribution = await affiliate_service._get_attribution_for_user(
                user_id,
                organization_id
            )

            if not attribution:
                logger.info(
                    f"No referral attribution found for user {user_id}. "
                    "No commissions to calculate."
                )
                return {
                    "success": True,
                    "commissions_calculated": 0,
                    "total_commission_amount": Decimal("0.00"),
                    "commission_records": [],
                    "message": "User not referred by affiliate"
                }

            logger.info(
                f"User {user_id} was referred by affiliate {attribution.get('affiliate_id')} "
                f"via code {attribution.get('referral_code')}"
            )

            # Update attribution with first purchase date
            if not attribution.get("first_purchase_at"):
                from datetime import datetime
                await affiliate_service.attributions_collection.update_one(
                    {"_id": attribution["_id"]},
                    {"$set": {"first_purchase_at": datetime.utcnow()}}
                )

            # Get affiliate chain (up to 3 tiers)
            affiliate_chain = await affiliate_service._get_affiliate_chain(
                attribution["affiliate_id"],
                max_tiers=3
            )

            # Calculate commissions for each tier
            commission_records = []

            for tier_level, affiliate_id in enumerate(affiliate_chain, start=1):
                # Get affiliate profile for commission rate
                affiliate = await affiliate_service.profiles_collection.find_one({"user_id": affiliate_id})

                if not affiliate:
                    logger.warning(f"Affiliate {affiliate_id} not found, skipping tier {tier_level}")
                    continue

                # Get commission rate for this tier
                rate_key = f"tier{tier_level}_commission_rate"
                commission_rate = Decimal(str(affiliate.get(rate_key, 0)))

                if commission_rate == 0:
                    logger.info(f"Zero commission rate for affiliate {affiliate_id} tier {tier_level}")
                    continue

                # Calculate base commission
                commission_amount = transaction_amount * commission_rate

                # Check for active campaigns and apply bonus commission
                bonus_amount = Decimal("0.00")
                campaign_code = None

                # Check if transaction is part of an active campaign
                # Look for campaign via attribution's UTM campaign or referral link's campaign
                active_campaigns = await affiliate_service.get_active_campaigns(organization_id)

                for campaign in active_campaigns:
                    if campaign.get("affiliate_id") == affiliate_id:
                        # Check if this purchase is associated with the campaign
                        # You can match by UTM campaign, referral code, or time window
                        bonus_rate = Decimal(str(campaign.get("bonus_rate", 0)))
                        if bonus_rate > 0:
                            bonus_amount = transaction_amount * bonus_rate
                            campaign_code = campaign.get("campaign_code")
                            logger.info(
                                f"Applying campaign bonus: {bonus_rate*100}% = ${bonus_amount} "
                                f"for campaign {campaign_code}"
                            )

                            # Update campaign stats
                            from ..models.affiliate import REFERRAL_CAMPAIGNS_COLLECTION
                            await affiliate_service.db[REFERRAL_CAMPAIGNS_COLLECTION].update_one(
                                {"_id": campaign["id"]},
                                {
                                    "$inc": {
                                        "total_sales": float(transaction_amount),
                                        "total_conversions": 1,
                                        "total_bonus_earned": float(bonus_amount)
                                    },
                                    "$set": {"updated_at": datetime.utcnow()}
                                }
                            )
                            break

                # Add bonus to commission
                total_commission_with_bonus = commission_amount + bonus_amount
                commission_amount = total_commission_with_bonus

                # Create commission record
                from datetime import datetime
                from ..models.affiliate import CommissionRecord, CommissionStatus

                commission = CommissionRecord(
                    affiliate_id=affiliate_id,
                    organization_id=organization_id,
                    referred_user_id=user_id,
                    transaction_id=transaction_id,
                    sale_amount=transaction_amount,
                    commission_rate=commission_rate,
                    commission_amount=commission_amount,
                    tier_level=tier_level,
                    status=CommissionStatus.APPROVED,  # Auto-approve for now
                    approved_at=datetime.utcnow(),
                )

                comm_dict = commission.dict(by_alias=True)
                comm_dict["_id"] = comm_dict.pop("id")

                # Convert Decimals to float for MongoDB
                for key in ["sale_amount", "commission_rate", "commission_amount",
                           "tier1_commission_rate", "tier2_commission_rate", "tier3_commission_rate"]:
                    if key in comm_dict:
                        comm_dict[key] = float(comm_dict[key])

                result = await affiliate_service.commissions_collection.insert_one(comm_dict)
                commission.id = str(result.inserted_id)

                # Update affiliate stats
                await affiliate_service._update_affiliate_stats(
                    affiliate_id,
                    commission_amount=commission_amount,
                    sale_amount=transaction_amount
                )

                commission_records.append(commission)

                logger.info(
                    f"Created commission: {commission_amount} for affiliate {affiliate_id} "
                    f"(tier {tier_level}) from transaction {transaction_id}"
                )

            if not commission_records:
                logger.warning(
                    f"No commission records created for transaction {transaction_id}"
                )
                return {
                    "success": True,
                    "commissions_calculated": 0,
                    "total_commission_amount": Decimal("0.00"),
                    "commission_records": [],
                    "message": "No eligible affiliates in chain"
                }

            # Calculate total commission amount
            total_commission = sum(
                Decimal(str(record.commission_amount))
                for record in commission_records
            )

            logger.info(
                f"Successfully calculated {len(commission_records)} commissions "
                f"totaling ${total_commission} for transaction {transaction_id}"
            )

            return {
                "success": True,
                "commissions_calculated": len(commission_records),
                "total_commission_amount": total_commission,
                "commission_records": commission_records,
                "message": f"Successfully attributed to {len(commission_records)} affiliates"
            }

        except Exception as e:
            logger.error(
                f"Error processing commissions for transaction {transaction_id}: {e}",
                exc_info=True
            )
            return {
                "success": False,
                "commissions_calculated": 0,
                "total_commission_amount": Decimal("0.00"),
                "commission_records": [],
                "error": str(e)
            }

    async def process_batch_commissions(
        self,
        transactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Process commissions for multiple transactions in batch.

        Useful for backfilling commissions or processing failed transactions.

        Args:
            transactions: List of transaction dicts with keys:
                - user_id
                - organization_id
                - transaction_amount
                - transaction_id
                - transaction_type (optional)

        Returns:
            Dictionary with batch processing results
        """
        results = {
            "total_transactions": len(transactions),
            "successful": 0,
            "failed": 0,
            "total_commissions_created": 0,
            "total_commission_amount": Decimal("0.00"),
            "errors": []
        }

        for txn in transactions:
            try:
                result = await self.process_transaction_commission(
                    user_id=txn["user_id"],
                    organization_id=txn["organization_id"],
                    transaction_amount=Decimal(str(txn["transaction_amount"])),
                    transaction_id=txn["transaction_id"],
                    transaction_type=txn.get("transaction_type", "wallet_topup")
                )

                if result["success"]:
                    results["successful"] += 1
                    results["total_commissions_created"] += result["commissions_calculated"]
                    results["total_commission_amount"] += result["total_commission_amount"]
                else:
                    results["failed"] += 1
                    results["errors"].append({
                        "transaction_id": txn["transaction_id"],
                        "error": result.get("error", "Unknown error")
                    })

            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "transaction_id": txn.get("transaction_id", "unknown"),
                    "error": str(e)
                })
                logger.error(f"Error processing transaction: {e}", exc_info=True)

        logger.info(
            f"Batch processing complete: {results['successful']}/{results['total_transactions']} successful, "
            f"{results['total_commissions_created']} commissions created, "
            f"${results['total_commission_amount']} total"
        )

        return results


# Global instance for easy access
_processor = None

def get_commission_processor() -> AffiliateCommissionProcessor:
    """
    Get the global commission processor instance.

    Returns:
        AffiliateCommissionProcessor instance
    """
    global _processor
    if _processor is None:
        _processor = AffiliateCommissionProcessor()
    return _processor


# Convenience function for direct usage
async def process_transaction_commission(
    user_id: str,
    organization_id: str,
    transaction_amount: Decimal,
    transaction_id: str,
    transaction_type: str = "wallet_topup"
) -> Dict[str, Any]:
    """
    Convenience function to process transaction commissions.

    This is the recommended way to trigger commission processing
    from other services.

    Args:
        user_id: ID of the user making the purchase
        organization_id: Organization ID
        transaction_amount: Amount of the transaction
        transaction_id: Unique transaction identifier
        transaction_type: Type of transaction

    Returns:
        Commission processing result dictionary

    Example:
        from backend.services.affiliate_commission_processor import process_transaction_commission

        # After successful wallet top-up:
        await process_transaction_commission(
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            transaction_amount=Decimal("100.00"),
            transaction_id=transaction.id
        )
    """
    processor = get_commission_processor()
    return await processor.process_transaction_commission(
        user_id=user_id,
        organization_id=organization_id,
        transaction_amount=transaction_amount,
        transaction_id=transaction_id,
        transaction_type=transaction_type
    )
