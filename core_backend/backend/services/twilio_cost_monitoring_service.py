"""
Twilio Cost Monitoring Service

Tracks and monitors Twilio API costs for calls, SMS, and other services.
Integrates with wallet service for automatic cost deductions.
"""

import asyncio
import httpx
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from decimal import Decimal
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class TwilioServiceType(Enum):
    """Twilio service types for cost tracking."""
    VOICE_CALL = "voice_call"
    SMS = "sms"
    MMS = "mms"
    WHATSAPP = "whatsapp"
    PROGRAMMABLE_VOICE = "programmable_voice"
    VERIFY = "verify"


@dataclass
class TwilioCostRecord:
    """Individual Twilio cost record."""
    service_type: TwilioServiceType
    cost_amount: Decimal
    currency: str
    timestamp: datetime
    transaction_id: str
    from_number: Optional[str] = None
    to_number: Optional[str] = None
    duration: Optional[int] = None  # In seconds for calls
    message_count: Optional[int] = None  # For SMS/MMS
    status: Optional[str] = None
    vapi_call_id: Optional[str] = None  # Link to VAPI call
    assistant_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TwilioCostSummary:
    """Summary of Twilio costs."""
    total_cost: Decimal
    currency: str
    call_costs: Decimal
    sms_costs: Decimal
    mms_costs: Decimal
    whatsapp_costs: Decimal
    other_costs: Decimal
    total_calls: int
    total_messages: int
    period_start: datetime
    period_end: datetime
    cost_breakdown: Dict[str, Decimal]


class TwilioCostMonitoringService:
    """Service for monitoring Twilio API costs and usage with wallet integration."""

    def __init__(
        self,
        account_sid: str,
        auth_token: str,
        base_url: str = "https://api.twilio.com",
        wallet_service=None
    ):
        """
        Initialize Twilio cost monitoring service.

        Args:
            account_sid: Twilio account SID
            auth_token: Twilio auth token
            base_url: Twilio API base URL
            wallet_service: Optional wallet service for automatic deductions
        """
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.base_url = base_url
        self.wallet_service = wallet_service
        self.session = None

        # Cost tracking storage (in production, use database)
        self.cost_records: List[TwilioCostRecord] = []

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = httpx.AsyncClient(
            auth=(self.account_sid, self.auth_token)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.aclose()

    async def get_session(self) -> httpx.AsyncClient:
        """Get or create HTTP session."""
        if not self.session:
            self.session = httpx.AsyncClient(
                auth=(self.account_sid, self.auth_token)
            )
        return self.session

    async def track_voice_call_cost(
        self,
        call_sid: str,
        from_number: str,
        to_number: str,
        duration: int,
        user_id: str,
        assistant_id: Optional[str] = None,
        vapi_call_id: Optional[str] = None,
        estimated_cost: Optional[Decimal] = None,
        auto_deduct: bool = True
    ) -> TwilioCostRecord:
        """
        Track cost for a Twilio voice call with automatic wallet deduction.

        Args:
            call_sid: Twilio call SID
            from_number: Calling number
            to_number: Destination number
            duration: Call duration in seconds
            user_id: User ID for wallet deduction
            assistant_id: Optional assistant ID for cost tracking
            vapi_call_id: Optional VAPI call ID for linkage
            estimated_cost: Estimated cost if known
            auto_deduct: Automatically deduct from wallet (default: True)

        Returns:
            Cost record for the call
        """
        try:
            # Calculate estimated cost if not provided
            if not estimated_cost:
                estimated_cost = await self._estimate_call_cost(to_number, duration)

            cost_record = TwilioCostRecord(
                service_type=TwilioServiceType.VOICE_CALL,
                cost_amount=estimated_cost,
                currency="USD",
                timestamp=datetime.now(timezone.utc),
                transaction_id=call_sid,
                from_number=from_number,
                to_number=to_number,
                duration=duration,
                vapi_call_id=vapi_call_id,
                assistant_id=assistant_id,
                metadata={
                    "source": "twilio_voice",
                    "estimated": True,
                    "user_id": user_id
                }
            )

            # Store the record
            self.cost_records.append(cost_record)

            # Automatically deduct from wallet if enabled
            if auto_deduct and self.wallet_service:
                await self._deduct_from_wallet(
                    user_id=user_id,
                    cost_record=cost_record
                )
                logger.info(f"Tracked and deducted Twilio call cost: {call_sid} - ${estimated_cost}")
            else:
                logger.info(f"Tracked Twilio call cost (no deduction): {call_sid} - ${estimated_cost}")

            return cost_record

        except Exception as e:
            logger.error(f"Error tracking Twilio call cost: {str(e)}")
            raise

    async def track_sms_cost(
        self,
        message_sid: str,
        from_number: str,
        to_number: str,
        user_id: str,
        assistant_id: Optional[str] = None,
        message_count: int = 1,
        estimated_cost: Optional[Decimal] = None,
        auto_deduct: bool = True
    ) -> TwilioCostRecord:
        """
        Track SMS cost with automatic wallet deduction.

        Args:
            message_sid: Twilio message SID
            from_number: Sending number
            to_number: Destination number
            user_id: User ID for wallet deduction
            assistant_id: Optional assistant ID for cost tracking
            message_count: Number of SMS segments
            estimated_cost: Estimated cost if known
            auto_deduct: Automatically deduct from wallet (default: True)

        Returns:
            Cost record for SMS
        """
        try:
            if not estimated_cost:
                estimated_cost = await self._estimate_sms_cost(to_number, message_count)

            cost_record = TwilioCostRecord(
                service_type=TwilioServiceType.SMS,
                cost_amount=estimated_cost,
                currency="USD",
                timestamp=datetime.now(timezone.utc),
                transaction_id=message_sid,
                from_number=from_number,
                to_number=to_number,
                message_count=message_count,
                assistant_id=assistant_id,
                metadata={
                    "source": "twilio_sms",
                    "estimated": True,
                    "user_id": user_id
                }
            )

            self.cost_records.append(cost_record)

            # Automatically deduct from wallet if enabled
            if auto_deduct and self.wallet_service:
                await self._deduct_from_wallet(
                    user_id=user_id,
                    cost_record=cost_record
                )
                logger.info(f"Tracked and deducted Twilio SMS cost: {message_sid} - ${estimated_cost}")
            else:
                logger.info(f"Tracked Twilio SMS cost (no deduction): {message_sid} - ${estimated_cost}")

            return cost_record

        except Exception as e:
            logger.error(f"Error tracking Twilio SMS cost: {str(e)}")
            raise

    async def track_whatsapp_cost(
        self,
        message_sid: str,
        from_number: str,
        to_number: str,
        user_id: str,
        assistant_id: Optional[str] = None,
        estimated_cost: Optional[Decimal] = None,
        auto_deduct: bool = True
    ) -> TwilioCostRecord:
        """
        Track WhatsApp message cost with automatic wallet deduction.

        Args:
            message_sid: Twilio message SID
            from_number: Sending WhatsApp number
            to_number: Destination WhatsApp number
            user_id: User ID for wallet deduction
            assistant_id: Optional assistant ID for cost tracking
            estimated_cost: Estimated cost if known
            auto_deduct: Automatically deduct from wallet (default: True)

        Returns:
            Cost record for WhatsApp message
        """
        try:
            if not estimated_cost:
                estimated_cost = await self._estimate_whatsapp_cost()

            cost_record = TwilioCostRecord(
                service_type=TwilioServiceType.WHATSAPP,
                cost_amount=estimated_cost,
                currency="USD",
                timestamp=datetime.now(timezone.utc),
                transaction_id=message_sid,
                from_number=from_number,
                to_number=to_number,
                message_count=1,
                assistant_id=assistant_id,
                metadata={
                    "source": "twilio_whatsapp",
                    "estimated": True,
                    "user_id": user_id
                }
            )

            self.cost_records.append(cost_record)

            # Automatically deduct from wallet if enabled
            if auto_deduct and self.wallet_service:
                await self._deduct_from_wallet(
                    user_id=user_id,
                    cost_record=cost_record
                )
                logger.info(f"Tracked and deducted Twilio WhatsApp cost: {message_sid} - ${estimated_cost}")
            else:
                logger.info(f"Tracked Twilio WhatsApp cost (no deduction): {message_sid} - ${estimated_cost}")

            return cost_record

        except Exception as e:
            logger.error(f"Error tracking Twilio WhatsApp cost: {str(e)}")
            raise

    async def _deduct_from_wallet(
        self,
        user_id: str,
        cost_record: TwilioCostRecord
    ) -> None:
        """
        Deduct cost from user's wallet and create transaction record.

        Args:
            user_id: User ID
            cost_record: Cost record with amount and metadata
        """
        try:
            if not self.wallet_service:
                logger.warning("Wallet service not available, skipping deduction")
                return

            # Create transaction metadata
            metadata = {
                "service": "twilio",
                "service_type": cost_record.service_type.value,
                "transaction_id": cost_record.transaction_id,
                "from_number": cost_record.from_number,
                "to_number": cost_record.to_number,
                "duration_seconds": cost_record.duration,
                "message_count": cost_record.message_count,
                "vapi_call_id": cost_record.vapi_call_id,
                "assistant_id": cost_record.assistant_id,
                "timestamp": cost_record.timestamp.isoformat()
            }

            # Build description
            if cost_record.service_type == TwilioServiceType.VOICE_CALL:
                description = f"Twilio voice call - {cost_record.duration}s to {cost_record.to_number}"
            elif cost_record.service_type == TwilioServiceType.SMS:
                description = f"Twilio SMS - {cost_record.message_count} segment(s) to {cost_record.to_number}"
            elif cost_record.service_type == TwilioServiceType.WHATSAPP:
                description = f"Twilio WhatsApp message to {cost_record.to_number}"
            else:
                description = f"Twilio {cost_record.service_type.value} service"

            # Deduct from wallet
            from ..models.wallet import Currency
            wallet = await self.wallet_service.get_or_create_wallet(user_id, Currency.USD)

            await self.wallet_service.debit(
                wallet_id=wallet.id,
                amount=cost_record.cost_amount,
                description=description,
                metadata=metadata,
                allow_negative=False  # Reason: Prevent overdrafts
            )

            logger.info(f"Deducted ${cost_record.cost_amount} from wallet for user {user_id}")

        except Exception as e:
            logger.error(f"Failed to deduct from wallet: {e}", exc_info=True)
            # Re-raise to ensure the caller knows the deduction failed
            raise

    async def _estimate_call_cost(self, to_number: str, duration: int) -> Decimal:
        """
        Estimate call cost based on Twilio pricing.

        Args:
            to_number: Phone number called
            duration: Duration in seconds

        Returns:
            Estimated cost
        """
        try:
            # Twilio pricing (approximate)
            # US/Canada outbound: $0.013/min
            # US/Canada inbound: $0.0085/min
            # International varies widely

            minutes = max(1, (duration + 59) // 60)  # Round up to next minute

            # Simple pricing model (should be enhanced with actual rates)
            if to_number.startswith("+1"):  # US/Canada
                rate_per_minute = Decimal("0.013")
            else:  # International (rough estimate)
                rate_per_minute = Decimal("0.08")

            estimated_cost = rate_per_minute * Decimal(str(minutes))
            return estimated_cost

        except Exception as e:
            logger.error(f"Error estimating call cost: {str(e)}")
            return Decimal("0.05")  # Default fallback

    async def _estimate_sms_cost(self, to_number: str, message_count: int) -> Decimal:
        """Estimate SMS cost."""
        try:
            # Twilio SMS pricing (approximate)
            # US/Canada: $0.0079 per segment outbound
            # International varies

            if to_number.startswith("+1"):  # US/Canada
                rate_per_segment = Decimal("0.0079")
            else:  # International
                rate_per_segment = Decimal("0.10")

            return rate_per_segment * Decimal(str(message_count))

        except Exception as e:
            logger.error(f"Error estimating SMS cost: {str(e)}")
            return Decimal("0.01")  # Default fallback

    async def _estimate_whatsapp_cost(self) -> Decimal:
        """Estimate WhatsApp message cost."""
        try:
            # Twilio WhatsApp pricing (approximate)
            # Business-initiated: $0.005 per message
            # User-initiated: Free for first 1000 messages/month

            return Decimal("0.005")

        except Exception as e:
            logger.error(f"Error estimating WhatsApp cost: {str(e)}")
            return Decimal("0.005")  # Default

    async def get_cost_summary(
        self,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[str] = None
    ) -> TwilioCostSummary:
        """
        Get cost summary for a period.

        Args:
            start_date: Start of period
            end_date: End of period
            user_id: Optional user ID filter

        Returns:
            Cost summary
        """
        try:
            # Filter records by date and user
            filtered_records = [
                r for r in self.cost_records
                if start_date <= r.timestamp <= end_date
                and (not user_id or r.metadata.get("user_id") == user_id)
            ]

            # Calculate summary
            total_cost = sum(r.cost_amount for r in filtered_records)
            call_costs = sum(
                r.cost_amount for r in filtered_records
                if r.service_type in [TwilioServiceType.VOICE_CALL, TwilioServiceType.PROGRAMMABLE_VOICE]
            )
            sms_costs = sum(
                r.cost_amount for r in filtered_records
                if r.service_type == TwilioServiceType.SMS
            )
            mms_costs = sum(
                r.cost_amount for r in filtered_records
                if r.service_type == TwilioServiceType.MMS
            )
            whatsapp_costs = sum(
                r.cost_amount for r in filtered_records
                if r.service_type == TwilioServiceType.WHATSAPP
            )
            other_costs = total_cost - call_costs - sms_costs - mms_costs - whatsapp_costs

            total_calls = len([
                r for r in filtered_records
                if r.service_type in [TwilioServiceType.VOICE_CALL, TwilioServiceType.PROGRAMMABLE_VOICE]
            ])
            total_messages = len([
                r for r in filtered_records
                if r.service_type in [TwilioServiceType.SMS, TwilioServiceType.MMS, TwilioServiceType.WHATSAPP]
            ])

            # Cost breakdown by service type
            cost_breakdown = {}
            for service_type in TwilioServiceType:
                service_cost = sum(
                    r.cost_amount for r in filtered_records
                    if r.service_type == service_type
                )
                cost_breakdown[service_type.value] = service_cost

            return TwilioCostSummary(
                total_cost=total_cost,
                currency="USD",
                call_costs=call_costs,
                sms_costs=sms_costs,
                mms_costs=mms_costs,
                whatsapp_costs=whatsapp_costs,
                other_costs=other_costs,
                total_calls=total_calls,
                total_messages=total_messages,
                period_start=start_date,
                period_end=end_date,
                cost_breakdown=cost_breakdown
            )

        except Exception as e:
            logger.error(f"Error generating cost summary: {str(e)}")
            raise


# Service instance
_twilio_cost_service = None

async def get_twilio_cost_service(wallet_service=None) -> TwilioCostMonitoringService:
    """
    Get Twilio cost monitoring service instance.

    Args:
        wallet_service: Optional wallet service for automatic cost deductions

    Returns:
        TwilioCostMonitoringService instance
    """
    global _twilio_cost_service

    if _twilio_cost_service is None:
        # Get credentials from environment or config
        import os
        account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")

        if not account_sid or not auth_token:
            logger.warning("Twilio credentials not configured in environment")

        _twilio_cost_service = TwilioCostMonitoringService(
            account_sid=account_sid,
            auth_token=auth_token,
            wallet_service=wallet_service
        )
    elif wallet_service and not _twilio_cost_service.wallet_service:
        # Update wallet service if provided and not already set
        _twilio_cost_service.wallet_service = wallet_service

    return _twilio_cost_service


# Export main classes and functions
__all__ = [
    "TwilioServiceType",
    "TwilioCostRecord",
    "TwilioCostSummary",
    "TwilioCostMonitoringService",
    "get_twilio_cost_service"
]
