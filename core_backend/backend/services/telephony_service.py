"""
Telephony service that integrates shared telephony interfaces library.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from uuid import UUID, uuid4
import logging

from apps.shared.telephony import TelephonyEvent, TelephonyPort, ProviderManager, CallContext, ProviderHealth, ProviderSettings, CallResult
from apps.shared.storage import MemoryStorageBackend

logger = logging.getLogger(__name__)


class TelephonyService:
    """Service for telephony operations using shared libraries."""

    def __init__(self, storage_backend=None):
        """
        Initialize the telephony service.

        Args:
            storage_backend: Storage backend for telephony data. Defaults to in-memory.
        """
        if storage_backend is None:
            from apps.shared.storage.interfaces import StorageConfig
            config = StorageConfig(backend_type="memory", connection_string="memory://")
            storage_backend = MemoryStorageBackend(config)
        
        self.storage = storage_backend
        self.provider_manager = ProviderManager({})
        # Note: _ensure_initialized will be called when needed

    async def _ensure_initialized(self):
        """Ensure the telephony service is initialized."""
        try:
            # Initialize storage tables if needed
            await self.storage.create_table("telephony_events", {
                "event_id": "TEXT PRIMARY KEY",
                "call_id": "TEXT",
                "tenant_id": "TEXT",
                "event_type": "TEXT",
                "timestamp": "TEXT",
                "provider": "TEXT",
                "data": "TEXT"
            })
            
            await self.storage.create_table("call_contexts", {
                "call_id": "TEXT PRIMARY KEY",
                "tenant_id": "TEXT",
                "destination": "TEXT",
                "source": "TEXT",
                "campaign_id": "TEXT",
                "cost_preference": "TEXT",
                "quality_preference": "TEXT",
                "geographic_region": "TEXT",
                "metadata": "TEXT"
            })
            
            await self.storage.create_table("provider_settings", {
                "provider_id": "TEXT PRIMARY KEY",
                "api_key": "TEXT",
                "api_secret": "TEXT",
                "base_url": "TEXT",
                "timeout_seconds": "INTEGER",
                "retry_attempts": "INTEGER",
                "enabled": "BOOLEAN",
                "priority": "INTEGER",
                "cost_multiplier": "REAL",
                "max_concurrent_calls": "INTEGER",
                "webhook_url": "TEXT",
                "webhook_secret": "TEXT",
                "custom_settings": "TEXT"
            })
            
            await self.storage.create_table("call_results", {
                "call_id": "TEXT PRIMARY KEY",
                "tenant_id": "TEXT",
                "success": "BOOLEAN",
                "provider": "TEXT",
                "duration_seconds": "REAL",
                "cost_usd": "REAL",
                "status": "TEXT",
                "error_message": "TEXT",
                "metadata": "TEXT"
            })
        except Exception:
            # Tables might already exist
            pass

    async def create_telephony_event(
        self,
        call_id: str,
        tenant_id: str,
        event_type: str,
        provider: str,
        data: Optional[Dict[str, Any]] = None
    ) -> TelephonyEvent:
        """
        Create a new telephony event.

        Args:
            call_id: Call identifier
            tenant_id: Tenant identifier
            event_type: Type of event
            provider: Telephony provider name
            data: Event-specific data

        Returns:
            TelephonyEvent: Created telephony event
        """
        event = TelephonyEvent(
            event_type=event_type,
            call_id=call_id,
            timestamp=datetime.utcnow(),
            provider=provider,
            data=data or {}
        )
        
        await self.storage.insert("telephony_events", {
            "event_id": str(uuid4()),
            "call_id": event.call_id,
            "tenant_id": tenant_id,
            "event_type": event.event_type,
            "timestamp": event.timestamp.isoformat(),
            "provider": event.provider,
            "data": str(event.data)
        })
        
        logger.info(f"Created telephony event {event_type} for call {call_id}")
        return event

    async def get_call_events(self, call_id: str) -> List[TelephonyEvent]:
        """
        Get all events for a call.

        Args:
            call_id: Call identifier

        Returns:
            List[TelephonyEvent]: List of telephony events
        """
        results = await self.storage.query("telephony_events", {"call_id": call_id})
        events = []
        
        for result in results:
            event = TelephonyEvent(
                event_type=result["event_type"],
                call_id=result["call_id"],
                timestamp=datetime.fromisoformat(result["timestamp"]),
                provider=result["provider"],
                data=eval(result["data"]) if result["data"] else {}
            )
            events.append(event)
        
        return events

    async def create_call_context(
        self,
        call_id: str,
        tenant_id: str,
        destination: str,
        source: str,
        campaign_id: Optional[str] = None,
        cost_preference: str = "balanced",
        quality_preference: str = "balanced",
        geographic_region: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CallContext:
        """
        Create a call context.

        Args:
            call_id: Call identifier
            tenant_id: Tenant identifier
            destination: Destination phone number
            source: Source phone number
            campaign_id: Campaign identifier
            cost_preference: Cost preference (low, balanced, high)
            quality_preference: Quality preference (low, balanced, high)
            geographic_region: Geographic region
            metadata: Additional context data

        Returns:
            CallContext: Created call context
        """
        context = CallContext(
            destination=destination,
            source=source,
            tenant_id=tenant_id,
            campaign_id=campaign_id,
            cost_preference=cost_preference,
            quality_preference=quality_preference,
            geographic_region=geographic_region,
            metadata=metadata or {}
        )
        
        await self.storage.insert("call_contexts", {
            "call_id": call_id,
            "tenant_id": context.tenant_id,
            "destination": context.destination,
            "source": context.source,
            "campaign_id": context.campaign_id,
            "cost_preference": context.cost_preference,
            "quality_preference": context.quality_preference,
            "geographic_region": context.geographic_region,
            "metadata": str(context.metadata)
        })
        
        logger.info(f"Created call context for call {call_id}")
        return context

    async def get_call_context(self, call_id: str) -> Optional[CallContext]:
        """
        Get call context by ID.

        Args:
            call_id: Call identifier

        Returns:
            CallContext: Call context if found, None otherwise
        """
        results = await self.storage.query("call_contexts", {"call_id": call_id})
        if not results:
            return None
        
        result = results[0]  # Get the first (and should be only) result
        return CallContext(
            destination=result["destination"],
            source=result["source"],
            tenant_id=result["tenant_id"],
            campaign_id=result["campaign_id"],
            cost_preference=result["cost_preference"],
            quality_preference=result["quality_preference"],
            geographic_region=result["geographic_region"],
            metadata=eval(result["metadata"]) if result["metadata"] else {}
        )

    async def set_provider_settings(
        self,
        provider_id: str,
        api_key: str,
        base_url: str,
        api_secret: Optional[str] = None,
        timeout_seconds: int = 30,
        retry_attempts: int = 3,
        enabled: bool = True,
        priority: int = 5,
        cost_multiplier: float = 1.0,
        max_concurrent_calls: Optional[int] = None,
        webhook_url: Optional[str] = None,
        webhook_secret: Optional[str] = None,
        custom_settings: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Set provider settings.

        Args:
            provider_id: Provider identifier
            api_key: API key for provider
            base_url: Base URL for provider API
            api_secret: API secret for provider
            timeout_seconds: Request timeout in seconds
            retry_attempts: Number of retry attempts
            enabled: Whether provider is enabled
            priority: Provider priority (1-10, higher is better)
            cost_multiplier: Cost multiplier for this provider
            max_concurrent_calls: Maximum concurrent calls
            webhook_url: Webhook URL for events
            webhook_secret: Webhook secret for verification
            custom_settings: Provider-specific settings

        Returns:
            bool: True if set successfully
        """
        try:
            # Check if provider already exists
            existing = await self.storage.query("provider_settings", {"provider_id": provider_id})
            if existing:
                # Update existing provider
                await self.storage.update("provider_settings", provider_id, {
                    "api_key": api_key,
                    "api_secret": api_secret,
                    "base_url": base_url,
                    "timeout_seconds": timeout_seconds,
                    "retry_attempts": retry_attempts,
                    "enabled": enabled,
                    "priority": priority,
                    "cost_multiplier": cost_multiplier,
                    "max_concurrent_calls": max_concurrent_calls,
                    "webhook_url": webhook_url,
                    "webhook_secret": webhook_secret,
                    "custom_settings": str(custom_settings) if custom_settings else None
                })
            else:
                # Insert new provider
                await self.storage.insert("provider_settings", {
                    "id": provider_id,  # Use provider_id as the record ID
                    "provider_id": provider_id,
                    "api_key": api_key,
                    "api_secret": api_secret,
                    "base_url": base_url,
                    "timeout_seconds": timeout_seconds,
                    "retry_attempts": retry_attempts,
                    "enabled": enabled,
                    "priority": priority,
                    "cost_multiplier": cost_multiplier,
                    "max_concurrent_calls": max_concurrent_calls,
                    "webhook_url": webhook_url,
                    "webhook_secret": webhook_secret,
                    "custom_settings": str(custom_settings) if custom_settings else None
                })
            
            logger.info(f"Set provider settings for {provider_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to set provider settings for {provider_id}: {e}")
            return False

    async def get_provider_settings(self, provider_id: str) -> Optional[ProviderSettings]:
        """
        Get provider settings.

        Args:
            provider_id: Provider identifier

        Returns:
            ProviderSettings: Provider settings if found, None otherwise
        """
        results = await self.storage.query("provider_settings", {"provider_id": provider_id})
        if not results:
            return None
        
        result = results[0]  # Get the first (and should be only) result
        return ProviderSettings(
            provider_id=result["provider_id"],
            api_key=result["api_key"],
            api_secret=result["api_secret"],
            base_url=result["base_url"],
            timeout_seconds=result["timeout_seconds"],
            retry_attempts=result["retry_attempts"],
            enabled=result["enabled"],
            priority=result["priority"],
            cost_multiplier=result["cost_multiplier"],
            max_concurrent_calls=result["max_concurrent_calls"],
            webhook_url=result["webhook_url"],
            webhook_secret=result["webhook_secret"],
            custom_settings=eval(result["custom_settings"]) if result["custom_settings"] else {}
        )

    async def initiate_call(
        self,
        tenant_id: str,
        destination: str,
        source: str,
        campaign_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CallResult:
        """
        Initiate a new call.

        Args:
            tenant_id: Tenant identifier
            destination: Destination phone number
            source: Source phone number
            campaign_id: Campaign identifier
            metadata: Additional call metadata

        Returns:
            CallResult: Call result with call information
        """
        call_id = str(uuid4())
        
        # Create call context
        context = await self.create_call_context(
            call_id=call_id,
            tenant_id=tenant_id,
            destination=destination,
            source=source,
            campaign_id=campaign_id,
            metadata=metadata
        )
        
        # Get best provider (for now, use a default provider)
        provider_name = "default-provider"
        
        # Create initiation event
        await self.create_telephony_event(
            call_id=call_id,
            tenant_id=tenant_id,
            event_type="call_started",
            provider=provider_name,
            data={"destination": destination, "source": source}
        )
        
        logger.info(f"Initiated call {call_id} from {source} to {destination} for tenant {tenant_id}")
        
        return CallResult(
            call_id=call_id,
            success=True,
            provider=provider_name,
            status="initiated",
            metadata={"tenant_id": tenant_id, "campaign_id": campaign_id}
        )

    async def end_call(
        self,
        call_id: str,
        tenant_id: str,
        duration_seconds: Optional[float] = None,
        cost_usd: Optional[float] = None,
        status: str = "completed",
        error_message: Optional[str] = None
    ) -> bool:
        """
        End a call.

        Args:
            call_id: Call identifier
            tenant_id: Tenant identifier
            duration_seconds: Call duration in seconds
            cost_usd: Call cost in USD
            status: Call status
            error_message: Error message if call failed

        Returns:
            bool: True if call was ended successfully
        """
        # Create end event
        await self.create_telephony_event(
            call_id=call_id,
            tenant_id=tenant_id,
            event_type="call_ended",
            provider="unknown",
            data={"status": status, "duration_seconds": duration_seconds, "cost_usd": cost_usd}
        )
        
        # Store call result
        try:
            # Check if call result already exists
            existing = await self.storage.query("call_results", {"call_id": call_id})
            if existing:
                # Update existing call result
                await self.storage.update("call_results", call_id, {
                    "success": status == "completed",
                    "provider": "unknown",
                    "duration_seconds": duration_seconds,
                    "cost_usd": cost_usd,
                    "status": status,
                    "error_message": error_message,
                    "metadata": str({})
                })
            else:
                # Insert new call result
                await self.storage.insert("call_results", {
                    "id": call_id,  # Use call_id as the record ID
                    "call_id": call_id,
                    "tenant_id": tenant_id,
                    "success": status == "completed",
                    "provider": "unknown",
                    "duration_seconds": duration_seconds,
                    "cost_usd": cost_usd,
                    "status": status,
                    "error_message": error_message,
                    "metadata": str({})
                })
            
            logger.info(f"Ended call {call_id} with status {status}")
            return True
        except Exception as e:
            logger.error(f"Failed to end call {call_id}: {e}")
            return False

    async def get_call_result(self, call_id: str) -> Optional[CallResult]:
        """
        Get call result by ID.

        Args:
            call_id: Call identifier

        Returns:
            CallResult: Call result if found, None otherwise
        """
        results = await self.storage.query("call_results", {"call_id": call_id})
        if not results:
            return None
        
        result = results[0]  # Get the first (and should be only) result
        
        # Get events for this call
        events = await self.get_call_events(call_id)
        
        return CallResult(
            call_id=result["call_id"],
            success=result["success"],
            provider=result["provider"],
            duration_seconds=result["duration_seconds"],
            cost_usd=result["cost_usd"],
            status=result["status"],
            error_message=result["error_message"],
            events=events,
            metadata=eval(result["metadata"]) if result["metadata"] else {}
        )

    async def get_tenant_calls(
        self,
        tenant_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[CallResult]:
        """
        Get call results for a tenant.

        Args:
            tenant_id: Tenant identifier
            limit: Maximum number of calls to return
            offset: Number of calls to skip

        Returns:
            List[CallResult]: List of call results
        """
        results = await self.storage.query(
            "call_results",
            {"tenant_id": tenant_id},
            order_by="-call_id",
            limit=limit,
            offset=offset
        )
        
        call_results = []
        for result in results:
            # Get events for this call
            events = await self.get_call_events(result["call_id"])
            
            call_result = CallResult(
                call_id=result["call_id"],
                success=result["success"],
                provider=result["provider"],
                duration_seconds=result["duration_seconds"],
                cost_usd=result["cost_usd"],
                status=result["status"],
                error_message=result["error_message"],
                events=events,
                metadata=eval(result["metadata"]) if result["metadata"] else {}
            )
            call_results.append(call_result)
        
        return call_results

    async def get_call_statistics(
        self,
        tenant_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get call statistics for a tenant.

        Args:
            tenant_id: Tenant identifier
            start_date: Start date for statistics
            end_date: End date for statistics

        Returns:
            Dict[str, Any]: Call statistics
        """
        # Build query conditions
        conditions = {"tenant_id": tenant_id}
        
        results = await self.storage.query("call_results", conditions)
        
        total_calls = len(results)
        successful_calls = len([r for r in results if r["success"]])
        failed_calls = total_calls - successful_calls
        total_duration = sum(r["duration_seconds"] or 0 for r in results)
        total_cost = sum(r["cost_usd"] or 0 for r in results)
        
        # Group by provider
        provider_stats = {}
        for result in results:
            provider = result["provider"]
            if provider not in provider_stats:
                provider_stats[provider] = {"calls": 0, "duration": 0, "cost": 0}
            provider_stats[provider]["calls"] += 1
            provider_stats[provider]["duration"] += result["duration_seconds"] or 0
            provider_stats[provider]["cost"] += result["cost_usd"] or 0
        
        return {
            "total_calls": total_calls,
            "successful_calls": successful_calls,
            "failed_calls": failed_calls,
            "success_rate": (successful_calls / total_calls * 100) if total_calls > 0 else 0,
            "total_duration": total_duration,
            "total_cost": total_cost,
            "average_duration": (total_duration / total_calls) if total_calls > 0 else 0,
            "average_cost": (total_cost / total_calls) if total_calls > 0 else 0,
            "provider_stats": provider_stats
        }

    async def export_call_data(
        self,
        tenant_id: str,
        format: str = "json"
    ) -> str:
        """
        Export call data for a tenant.

        Args:
            tenant_id: Tenant identifier
            format: Export format (json/csv)

        Returns:
            str: Exported data
        """
        calls = await self.get_tenant_calls(tenant_id, limit=1000)
        
        if format.lower() == "json":
            import json
            data = []
            for call in calls:
                call_dict = {
                    "call_id": call.call_id,
                    "success": call.success,
                    "provider": call.provider,
                    "duration_seconds": call.duration_seconds,
                    "cost_usd": call.cost_usd,
                    "status": call.status,
                    "error_message": call.error_message,
                    "events": [event.dict() for event in call.events],
                    "metadata": call.metadata
                }
                data.append(call_dict)
            
            return json.dumps(data, indent=2)
        
        elif format.lower() == "csv":
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                "call_id", "success", "provider", "duration_seconds", "cost_usd",
                "status", "error_message", "event_count"
            ])
            
            # Write data
            for call in calls:
                writer.writerow([
                    call.call_id,
                    call.success,
                    call.provider,
                    call.duration_seconds or 0,
                    call.cost_usd or 0,
                    call.status,
                    call.error_message or "",
                    len(call.events)
                ])
            
            return output.getvalue()
        
        else:
            raise ValueError(f"Unsupported export format: {format}")

    async def cleanup_old_calls(self, days: int = 30) -> int:
        """
        Clean up old call data.

        Args:
            days: Number of days to keep call data

        Returns:
            int: Number of calls cleaned up
        """
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get old call results
        old_calls = await self.storage.query("call_results")
        # Filter by date (simple implementation for memory backend)
        old_calls = [call for call in old_calls if call.get("created_at", "") <= cutoff_date.isoformat()]
        
        # Delete old calls and their events
        deleted_count = 0
        for call in old_calls:
            call_id = call["call_id"]
            
            # Delete events first
            await self.storage.delete("telephony_events", {"call_id": call_id})
            
            # Delete call context
            await self.storage.delete("call_contexts", {"call_id": call_id})
            
            # Delete call result
            await self.storage.delete("call_results", {"call_id": call_id})
            deleted_count += 1
        
        logger.info(f"Cleaned up {deleted_count} old calls")
        return deleted_count
