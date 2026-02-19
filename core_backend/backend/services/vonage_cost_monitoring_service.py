"""
Vonage Cost Monitoring Service

Tracks and monitors Vonage API costs for calls, SMS, and other services.
Integrates with VAPI call analytics to provide comprehensive cost monitoring.
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


class VonageServiceType(Enum):
    """Vonage service types for cost tracking."""
    VOICE_CALL = "voice_call"
    SMS = "sms"
    VERIFY = "verify"
    NUMBER_INSIGHT = "number_insight"
    VOICE_API = "voice_api"


@dataclass
class VonageCostRecord:
    """Individual Vonage cost record."""
    service_type: VonageServiceType
    cost_amount: Decimal
    currency: str
    timestamp: datetime
    transaction_id: str
    phone_number: Optional[str] = None
    destination: Optional[str] = None
    duration: Optional[int] = None  # In seconds for calls
    message_count: Optional[int] = None  # For SMS
    vapi_call_id: Optional[str] = None  # Link to VAPI call
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class VonageCostSummary:
    """Summary of Vonage costs."""
    total_cost: Decimal
    currency: str
    call_costs: Decimal
    sms_costs: Decimal
    other_costs: Decimal
    total_calls: int
    total_sms: int
    period_start: datetime
    period_end: datetime
    cost_breakdown: Dict[str, Decimal]


class VonageCostMonitoringService:
    """Service for monitoring Vonage API costs and usage with wallet integration."""

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = "https://api.nexmo.com",
        wallet_service=None
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
        self.session = None
        self.wallet_service = wallet_service

        # Cost tracking storage (in production, use database)
        self.cost_records: List[VonageCostRecord] = []

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = httpx.AsyncClient()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.aclose()

    async def get_session(self) -> httpx.AsyncClient:
        """Get or create HTTP session."""
        if not self.session:
            self.session = httpx.AsyncClient()
        return self.session

    async def fetch_vonage_costs(
        self,
        start_date: datetime,
        end_date: datetime,
        service_type: Optional[VonageServiceType] = None
    ) -> List[VonageCostRecord]:
        """
        Fetch cost data from Vonage API.

        Args:
            start_date: Start of period
            end_date: End of period
            service_type: Filter by service type

        Returns:
            List of cost records
        """
        try:
            session = await self.get_session()

            # Vonage Reports API endpoint
            url = f"{self.base_url}/reports/records"

            params = {
                "api_key": self.api_key,
                "api_secret": self.api_secret,
                "date_start": start_date.strftime("%Y-%m-%d"),
                "date_end": end_date.strftime("%Y-%m-%d")
            }

            if service_type:
                params["product"] = service_type.value

            response = await session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                return await self._parse_vonage_cost_data(data)
            else:
                logger.error(f"Vonage API error: {response.status_code} - {response.text}")
                return []

        except Exception as e:
            logger.error(f"Error fetching Vonage costs: {str(e)}")
            return []

    async def _parse_vonage_cost_data(self, data: Dict[str, Any]) -> List[VonageCostRecord]:
        """Parse Vonage API response into cost records."""
        records = []

        try:
            # Parse different record types based on Vonage API structure
            if "records" in data:
                for record in data["records"]:
                    cost_record = await self._create_cost_record_from_api(record)
                    if cost_record:
                        records.append(cost_record)

            return records

        except Exception as e:
            logger.error(f"Error parsing Vonage cost data: {str(e)}")
            return []

    async def _create_cost_record_from_api(self, api_record: Dict[str, Any]) -> Optional[VonageCostRecord]:
        """Create cost record from API response."""
        try:
            # Map API fields to our cost record
            service_type = self._map_service_type(api_record.get("product", "voice_call"))

            return VonageCostRecord(
                service_type=service_type,
                cost_amount=Decimal(str(api_record.get("price", "0.0"))),
                currency=api_record.get("currency", "USD"),
                timestamp=datetime.fromisoformat(api_record.get("start_time", datetime.now().isoformat())),
                transaction_id=api_record.get("id", f"vonage_{int(datetime.now().timestamp())}"),
                phone_number=api_record.get("from"),
                destination=api_record.get("to"),
                duration=api_record.get("duration"),
                metadata=api_record
            )

        except Exception as e:
            logger.error(f"Error creating cost record: {str(e)}")
            return None

    def _map_service_type(self, product: str) -> VonageServiceType:
        """Map Vonage product names to our service types."""
        mapping = {
            "voice": VonageServiceType.VOICE_CALL,
            "sms": VonageServiceType.SMS,
            "verify": VonageServiceType.VERIFY,
            "ni": VonageServiceType.NUMBER_INSIGHT,
            "voice-api": VonageServiceType.VOICE_API
        }
        return mapping.get(product.lower(), VonageServiceType.VOICE_CALL)

    async def track_vapi_call_cost(
        self,
        vapi_call_id: str,
        phone_number: str,
        duration: int,
        user_id: str,
        assistant_id: Optional[str] = None,
        estimated_cost: Optional[Decimal] = None,
        auto_deduct: bool = True
    ) -> VonageCostRecord:
        """
        Track cost for a VAPI call using Vonage phone number with automatic wallet deduction.

        Args:
            vapi_call_id: VAPI call identifier
            phone_number: Vonage phone number used
            duration: Call duration in seconds
            user_id: User ID for wallet deduction
            assistant_id: Optional assistant ID for cost tracking
            estimated_cost: Estimated cost if known
            auto_deduct: Automatically deduct from wallet (default: True)

        Returns:
            Cost record for the call
        """
        try:
            # Calculate estimated cost if not provided
            if not estimated_cost:
                estimated_cost = await self._estimate_call_cost(phone_number, duration)

            cost_record = VonageCostRecord(
                service_type=VonageServiceType.VOICE_CALL,
                cost_amount=estimated_cost,
                currency="USD",
                timestamp=datetime.now(timezone.utc),
                transaction_id=f"vapi_call_{vapi_call_id}",
                phone_number=phone_number,
                duration=duration,
                vapi_call_id=vapi_call_id,
                metadata={
                    "source": "vapi_integration",
                    "estimated": True,
                    "assistant_id": assistant_id,
                    "user_id": user_id
                }
            )

            # Store the record
            self.cost_records.append(cost_record)

            # Automatically deduct from wallet if enabled and wallet service is available
            if auto_deduct and self.wallet_service:
                await self._deduct_from_wallet(
                    user_id=user_id,
                    cost_record=cost_record,
                    assistant_id=assistant_id
                )
                logger.info(f"Tracked and deducted VAPI call cost: {vapi_call_id} - ${estimated_cost}")
            else:
                logger.info(f"Tracked VAPI call cost (no deduction): {vapi_call_id} - ${estimated_cost}")

            return cost_record

        except Exception as e:
            logger.error(f"Error tracking VAPI call cost: {str(e)}")
            raise

    async def _estimate_call_cost(self, phone_number: str, duration: int) -> Decimal:
        """
        Estimate call cost based on Vonage pricing.

        Args:
            phone_number: Phone number called
            duration: Duration in seconds

        Returns:
            Estimated cost
        """
        try:
            # Vonage pricing (approximate)
            # US/Canada: $0.012/min, International varies

            minutes = max(1, (duration + 59) // 60)  # Round up to next minute

            # Simple pricing model (should be enhanced with actual rates)
            if phone_number.startswith("+1"):  # US/Canada
                rate_per_minute = Decimal("0.012")
            else:  # International (rough estimate)
                rate_per_minute = Decimal("0.05")

            estimated_cost = rate_per_minute * Decimal(str(minutes))
            return estimated_cost

        except Exception as e:
            logger.error(f"Error estimating call cost: {str(e)}")
            return Decimal("0.05")  # Default fallback

    async def _deduct_from_wallet(
        self,
        user_id: str,
        cost_record: VonageCostRecord,
        assistant_id: Optional[str] = None
    ) -> None:
        """
        Deduct cost from user's wallet and create transaction record.

        Args:
            user_id: User ID
            cost_record: Cost record with amount and metadata
            assistant_id: Optional assistant ID for tracking
        """
        try:
            if not self.wallet_service:
                logger.warning("Wallet service not available, skipping deduction")
                return

            # Create transaction metadata
            metadata = {
                "service": "vonage",
                "service_type": cost_record.service_type.value,
                "transaction_id": cost_record.transaction_id,
                "phone_number": cost_record.phone_number,
                "destination": cost_record.destination,
                "duration_seconds": cost_record.duration,
                "message_count": cost_record.message_count,
                "vapi_call_id": cost_record.vapi_call_id,
                "assistant_id": assistant_id,
                "timestamp": cost_record.timestamp.isoformat()
            }

            # Build description
            if cost_record.service_type == VonageServiceType.VOICE_CALL:
                description = f"Vonage voice call - {cost_record.duration}s to {cost_record.destination or 'unknown'}"
            elif cost_record.service_type == VonageServiceType.SMS:
                description = f"Vonage SMS - {cost_record.message_count} message(s) to {cost_record.destination}"
            else:
                description = f"Vonage {cost_record.service_type.value} service"

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

    async def track_sms_cost(
        self,
        destination: str,
        user_id: str,
        assistant_id: Optional[str] = None,
        message_count: int = 1,
        estimated_cost: Optional[Decimal] = None,
        auto_deduct: bool = True
    ) -> VonageCostRecord:
        """
        Track SMS cost with automatic wallet deduction.

        Args:
            destination: Destination phone number
            user_id: User ID for wallet deduction
            assistant_id: Optional assistant ID for cost tracking
            message_count: Number of SMS messages
            estimated_cost: Estimated cost if known
            auto_deduct: Automatically deduct from wallet (default: True)

        Returns:
            Cost record for SMS
        """
        try:
            if not estimated_cost:
                estimated_cost = await self._estimate_sms_cost(destination, message_count)

            cost_record = VonageCostRecord(
                service_type=VonageServiceType.SMS,
                cost_amount=estimated_cost,
                currency="USD",
                timestamp=datetime.now(timezone.utc),
                transaction_id=f"sms_{int(datetime.now().timestamp())}",
                destination=destination,
                message_count=message_count,
                metadata={
                    "source": "sms_tracking",
                    "estimated": True,
                    "assistant_id": assistant_id,
                    "user_id": user_id
                }
            )

            self.cost_records.append(cost_record)

            # Automatically deduct from wallet if enabled
            if auto_deduct and self.wallet_service:
                await self._deduct_from_wallet(
                    user_id=user_id,
                    cost_record=cost_record,
                    assistant_id=assistant_id
                )
                logger.info(f"Tracked and deducted SMS cost: {destination} - ${estimated_cost}")
            else:
                logger.info(f"Tracked SMS cost (no deduction): {destination} - ${estimated_cost}")

            return cost_record

        except Exception as e:
            logger.error(f"Error tracking SMS cost: {str(e)}")
            raise

    async def _estimate_sms_cost(self, destination: str, message_count: int) -> Decimal:
        """Estimate SMS cost."""
        try:
            # Vonage SMS pricing (approximate)
            if destination.startswith("+1"):  # US/Canada
                rate_per_sms = Decimal("0.0075")
            else:  # International
                rate_per_sms = Decimal("0.05")

            return rate_per_sms * Decimal(str(message_count))

        except Exception as e:
            logger.error(f"Error estimating SMS cost: {str(e)}")
            return Decimal("0.01")  # Default fallback

    async def get_cost_summary(
        self,
        start_date: datetime,
        end_date: datetime,
        include_estimates: bool = True
    ) -> VonageCostSummary:
        """
        Get cost summary for a period.

        Args:
            start_date: Start of period
            end_date: End of period
            include_estimates: Include estimated costs

        Returns:
            Cost summary
        """
        try:
            # Fetch real data from Vonage API
            api_records = await self.fetch_vonage_costs(start_date, end_date)

            # Combine with local tracked records if including estimates
            all_records = api_records
            if include_estimates:
                local_records = [
                    r for r in self.cost_records
                    if start_date <= r.timestamp <= end_date
                ]
                all_records.extend(local_records)

            # Calculate summary
            total_cost = sum(r.cost_amount for r in all_records)
            call_costs = sum(
                r.cost_amount for r in all_records
                if r.service_type in [VonageServiceType.VOICE_CALL, VonageServiceType.VOICE_API]
            )
            sms_costs = sum(
                r.cost_amount for r in all_records
                if r.service_type == VonageServiceType.SMS
            )
            other_costs = total_cost - call_costs - sms_costs

            total_calls = len([
                r for r in all_records
                if r.service_type in [VonageServiceType.VOICE_CALL, VonageServiceType.VOICE_API]
            ])
            total_sms = len([
                r for r in all_records
                if r.service_type == VonageServiceType.SMS
            ])

            # Cost breakdown by service type
            cost_breakdown = {}
            for service_type in VonageServiceType:
                service_cost = sum(
                    r.cost_amount for r in all_records
                    if r.service_type == service_type
                )
                cost_breakdown[service_type.value] = service_cost

            return VonageCostSummary(
                total_cost=total_cost,
                currency="USD",
                call_costs=call_costs,
                sms_costs=sms_costs,
                other_costs=other_costs,
                total_calls=total_calls,
                total_sms=total_sms,
                period_start=start_date,
                period_end=end_date,
                cost_breakdown=cost_breakdown
            )

        except Exception as e:
            logger.error(f"Error generating cost summary: {str(e)}")
            raise

    async def get_vapi_linked_costs(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[VonageCostRecord]:
        """Get costs linked to VAPI calls."""
        return [
            r for r in self.cost_records
            if r.vapi_call_id and start_date <= r.timestamp <= end_date
        ]

    async def link_cost_to_vapi_call(
        self,
        transaction_id: str,
        vapi_call_id: str
    ) -> bool:
        """Link an existing cost record to a VAPI call."""
        try:
            for record in self.cost_records:
                if record.transaction_id == transaction_id:
                    record.vapi_call_id = vapi_call_id
                    if not record.metadata:
                        record.metadata = {}
                    record.metadata["vapi_linked"] = True
                    return True
            return False

        except Exception as e:
            logger.error(f"Error linking cost to VAPI call: {str(e)}")
            return False


# Service instance
_vonage_cost_service = None

async def get_vonage_cost_service(wallet_service=None) -> VonageCostMonitoringService:
    """
    Get Vonage cost monitoring service instance.

    Args:
        wallet_service: Optional wallet service for automatic cost deductions

    Returns:
        VonageCostMonitoringService instance
    """
    global _vonage_cost_service

    if _vonage_cost_service is None:
        # Get credentials from environment or config
        import os
        api_key = os.getenv("VONAGE_API_KEY", "4109fdf7")  # From integration_api_keys.md
        api_secret = os.getenv("VONAGE_API_SECRET", "mativo3saMI3cAWG")  # From integration_api_keys.md

        _vonage_cost_service = VonageCostMonitoringService(
            api_key=api_key,
            api_secret=api_secret,
            wallet_service=wallet_service
        )
    elif wallet_service and not _vonage_cost_service.wallet_service:
        # Update wallet service if provided and not already set
        _vonage_cost_service.wallet_service = wallet_service

    return _vonage_cost_service