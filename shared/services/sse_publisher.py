"""
Server-Sent Events (SSE) Publisher Service

This module provides a centralized SSE event broadcasting system for real-time
campaign updates across all apps (b2c-portal, inkwave, churchflow, automations).

Key Features:
- Generic event publishing for any campaign type (SMS, Voice, WhatsApp)
- Multi-subscriber support with per-campaign event streams
- Automatic connection management and cleanup
- Type-safe event definitions
- Memory-efficient with automatic cleanup of completed campaigns

Usage Example:
    from shared.services.sse_publisher import sse_publisher

    # Publish an event
    await sse_publisher.publish(
        campaign_id="abc123",
        event_type="sms_progress",
        data={"sent": 50, "total": 100}
    )

    # Subscribe to events
    async for event in sse_publisher.subscribe("abc123", "user456"):
        yield f"data: {json.dumps(event)}\n\n"
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Set, AsyncGenerator, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict
from pydantic import BaseModel

logger = logging.getLogger(__name__)


# ==================== Event Models ====================

class CampaignEvent(BaseModel):
    """Base event model for all campaign events"""
    campaign_id: str
    event_type: str
    data: Dict[str, Any]
    timestamp: str

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


@dataclass
class SSESubscriber:
    """Represents an active SSE subscriber"""
    campaign_id: str
    user_id: str
    queue: asyncio.Queue
    connected_at: datetime
    last_event_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        return {
            "campaign_id": self.campaign_id,
            "user_id": self.user_id,
            "connected_at": self.connected_at.isoformat(),
            "last_event_at": self.last_event_at.isoformat(),
            "connection_duration": (datetime.now() - self.connected_at).total_seconds()
        }


# ==================== SSE Publisher Service ====================

class SSEPublisher:
    """
    Centralized SSE event publisher for campaign real-time updates.

    This service manages event broadcasting to multiple subscribers across
    different campaigns. It handles connection lifecycle, event queuing,
    and automatic cleanup.

    Attributes:
        _subscribers: Dict mapping campaign_id to set of subscribers
        _event_queues: Dict mapping subscriber ID to event queue
        _cleanup_tasks: Dict of background cleanup tasks
        _max_queue_size: Maximum events in queue before dropping old ones
        _inactive_timeout: Seconds before timing out inactive connections
    """

    def __init__(
        self,
        max_queue_size: int = 100,
        inactive_timeout: int = 300  # 5 minutes
    ):
        """
        Initialize the SSE publisher.

        Args:
            max_queue_size: Maximum number of events to queue per subscriber
            inactive_timeout: Seconds before timing out inactive connections
        """
        self._subscribers: Dict[str, Set[SSESubscriber]] = defaultdict(set)
        self._event_queues: Dict[str, asyncio.Queue] = {}
        self._cleanup_tasks: Dict[str, asyncio.Task] = {}
        self._max_queue_size = max_queue_size
        self._inactive_timeout = inactive_timeout
        self._lock = asyncio.Lock()

        logger.info(f"SSEPublisher initialized: max_queue_size={max_queue_size}, "
                   f"inactive_timeout={inactive_timeout}s")

    async def subscribe(
        self,
        campaign_id: str,
        user_id: str,
        initial_data: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Subscribe to real-time events for a campaign.

        This creates an async generator that yields events as they are published.
        The connection is automatically cleaned up when the generator is closed.

        Args:
            campaign_id: Campaign to subscribe to
            user_id: User making the subscription (for auth/logging)
            initial_data: Optional initial data to send immediately

        Yields:
            Dict containing event data

        Example:
            async for event in sse_publisher.subscribe("abc123", "user456"):
                yield f"data: {json.dumps(event)}\n\n"
        """
        subscriber_id = f"{campaign_id}:{user_id}:{id(asyncio.current_task())}"
        queue = asyncio.Queue(maxsize=self._max_queue_size)

        subscriber = SSESubscriber(
            campaign_id=campaign_id,
            user_id=user_id,
            queue=queue,
            connected_at=datetime.now(),
            last_event_at=datetime.now()
        )

        async with self._lock:
            self._subscribers[campaign_id].add(subscriber)
            self._event_queues[subscriber_id] = queue

        logger.info(f"SSE subscriber added: campaign={campaign_id} user={user_id} "
                   f"total_subscribers={len(self._subscribers[campaign_id])}")

        try:
            # Send initial data if provided
            if initial_data:
                event = {
                    "campaign_id": campaign_id,
                    "event_type": "initial",
                    "data": initial_data,
                    "timestamp": datetime.now().isoformat()
                }
                yield event

            # Stream events from queue
            while True:
                try:
                    # Wait for next event with timeout
                    event = await asyncio.wait_for(
                        queue.get(),
                        timeout=30.0  # 30 second timeout for keep-alive
                    )

                    subscriber.last_event_at = datetime.now()
                    yield event

                except asyncio.TimeoutError:
                    # Send keep-alive comment
                    yield {"_keepalive": True}

                except asyncio.CancelledError:
                    logger.info(f"SSE subscriber cancelled: campaign={campaign_id} user={user_id}")
                    break

        finally:
            # Cleanup on disconnect
            await self._remove_subscriber(campaign_id, subscriber, subscriber_id)

    async def publish(
        self,
        campaign_id: str,
        event_type: str,
        data: Dict[str, Any],
        user_filter: Optional[Set[str]] = None
    ) -> int:
        """
        Publish an event to all subscribers of a campaign.

        Args:
            campaign_id: Campaign to publish to
            event_type: Type of event (e.g., "sms_progress", "call_completed")
            data: Event data payload
            user_filter: Optional set of user IDs to send to (None = all)

        Returns:
            Number of subscribers that received the event

        Example:
            await sse_publisher.publish(
                "abc123",
                "sms_progress",
                {"sent": 50, "total": 100, "failed": 2}
            )
        """
        if campaign_id not in self._subscribers or not self._subscribers[campaign_id]:
            logger.debug(f"No subscribers for campaign {campaign_id}, event {event_type} not published")
            return 0

        event = {
            "campaign_id": campaign_id,
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }

        published_count = 0
        disconnected_subscribers = []

        for subscriber in self._subscribers[campaign_id]:
            # Filter by user if specified
            if user_filter and subscriber.user_id not in user_filter:
                continue

            try:
                # Non-blocking put (drop if queue full)
                subscriber.queue.put_nowait(event)
                published_count += 1

            except asyncio.QueueFull:
                logger.warning(f"Queue full for subscriber: campaign={campaign_id} "
                             f"user={subscriber.user_id}, dropping event")
                # Mark for cleanup if queue consistently full
                if (datetime.now() - subscriber.last_event_at).total_seconds() > self._inactive_timeout:
                    disconnected_subscribers.append(subscriber)

            except Exception as e:
                logger.error(f"Error publishing to subscriber: campaign={campaign_id} "
                           f"user={subscriber.user_id} error={e}")
                disconnected_subscribers.append(subscriber)

        # Clean up disconnected subscribers
        for subscriber in disconnected_subscribers:
            subscriber_id = f"{campaign_id}:{subscriber.user_id}:*"
            await self._remove_subscriber(campaign_id, subscriber, subscriber_id)

        if published_count > 0:
            logger.debug(f"Published event: campaign={campaign_id} type={event_type} "
                        f"subscribers={published_count}")

        return published_count

    async def cleanup_campaign(self, campaign_id: str) -> None:
        """
        Clean up all subscribers for a completed campaign.

        This should be called when a campaign completes to immediately
        disconnect all subscribers and free resources.

        Args:
            campaign_id: Campaign to clean up
        """
        if campaign_id not in self._subscribers:
            return

        subscribers = list(self._subscribers[campaign_id])
        logger.info(f"Cleaning up campaign: campaign={campaign_id} "
                   f"subscribers={len(subscribers)}")

        # Send final event to all subscribers
        await self.publish(
            campaign_id,
            "campaign_completed",
            {"message": "Campaign has completed, closing connection"}
        )

        # Wait a moment for final event to be sent
        await asyncio.sleep(0.5)

        # Remove all subscribers
        async with self._lock:
            for subscriber in subscribers:
                subscriber_id = f"{campaign_id}:{subscriber.user_id}:*"
                if subscriber_id in self._event_queues:
                    del self._event_queues[subscriber_id]

            if campaign_id in self._subscribers:
                del self._subscribers[campaign_id]

        logger.info(f"Campaign cleanup complete: campaign={campaign_id}")

    async def _remove_subscriber(
        self,
        campaign_id: str,
        subscriber: SSESubscriber,
        subscriber_id: str
    ) -> None:
        """
        Remove a subscriber and clean up resources.

        Args:
            campaign_id: Campaign ID
            subscriber: Subscriber to remove
            subscriber_id: Unique subscriber ID
        """
        async with self._lock:
            if campaign_id in self._subscribers:
                self._subscribers[campaign_id].discard(subscriber)

                # Remove campaign key if no subscribers left
                if not self._subscribers[campaign_id]:
                    del self._subscribers[campaign_id]

            # Clean up queue
            if subscriber_id in self._event_queues:
                queue = self._event_queues[subscriber_id]
                # Clear remaining events
                while not queue.empty():
                    try:
                        queue.get_nowait()
                    except asyncio.QueueEmpty:
                        break
                del self._event_queues[subscriber_id]

        connection_duration = (datetime.now() - subscriber.connected_at).total_seconds()
        logger.info(f"SSE subscriber removed: campaign={campaign_id} "
                   f"user={subscriber.user_id} duration={connection_duration:.1f}s")

    def get_subscriber_count(self, campaign_id: str) -> int:
        """
        Get the number of active subscribers for a campaign.

        Args:
            campaign_id: Campaign to check

        Returns:
            Number of active subscribers
        """
        return len(self._subscribers.get(campaign_id, set()))

    def get_active_campaigns(self) -> Set[str]:
        """
        Get set of campaigns with active subscribers.

        Returns:
            Set of campaign IDs
        """
        return set(self._subscribers.keys())

    def get_stats(self) -> Dict[str, Any]:
        """
        Get current statistics about the SSE publisher.

        Returns:
            Dict with subscriber counts and connection info
        """
        total_subscribers = sum(len(subs) for subs in self._subscribers.values())

        return {
            "total_subscribers": total_subscribers,
            "active_campaigns": len(self._subscribers),
            "campaigns": {
                campaign_id: len(subscribers)
                for campaign_id, subscribers in self._subscribers.items()
            },
            "max_queue_size": self._max_queue_size,
            "inactive_timeout": self._inactive_timeout
        }


# ==================== Global Instance ====================

# Singleton instance for use across the application
sse_publisher = SSEPublisher(
    max_queue_size=100,
    inactive_timeout=300  # 5 minutes
)


# ==================== Utility Functions ====================

async def publish_sms_progress(
    campaign_id: str,
    total: int,
    sent: int,
    delivered: int,
    failed: int,
    pending: int,
    total_cost: float
) -> int:
    """
    Convenience function to publish SMS campaign progress.

    Args:
        campaign_id: Campaign ID
        total: Total recipients
        sent: Messages sent
        delivered: Messages delivered
        failed: Messages failed
        pending: Messages pending
        total_cost: Total cost in USD

    Returns:
        Number of subscribers notified
    """
    return await sse_publisher.publish(
        campaign_id,
        "sms_progress",
        {
            "progress": {
                "total_recipients": total,
                "sent": sent,
                "delivered": delivered,
                "failed": failed,
                "pending": pending
            },
            "total_cost": total_cost
        }
    )


async def publish_voice_progress(
    campaign_id: str,
    calls_made: int,
    calls_total: int,
    success_count: int,
    failed_count: int,
    current_cost: float
) -> int:
    """
    Convenience function to publish voice campaign progress.

    Args:
        campaign_id: Campaign ID
        calls_made: Total calls made
        calls_total: Total calls to make
        success_count: Successful calls
        failed_count: Failed calls
        current_cost: Current cost in USD

    Returns:
        Number of subscribers notified
    """
    success_rate = (success_count / calls_made * 100) if calls_made > 0 else 0

    return await sse_publisher.publish(
        campaign_id,
        "voice_progress",
        {
            "calls_made": calls_made,
            "calls_total": calls_total,
            "success_count": success_count,
            "failed_count": failed_count,
            "success_rate": round(success_rate, 2),
            "current_cost": round(current_cost, 2)
        }
    )


async def publish_call_completed(
    campaign_id: str,
    call_id: str,
    contact_name: str,
    phone_number: str,
    duration: int,
    status: str,
    transcript_available: bool,
    error_message: Optional[str] = None
) -> int:
    """
    Convenience function to publish individual call completion.

    Args:
        campaign_id: Campaign ID
        call_id: Unique call ID
        contact_name: Contact name
        phone_number: Phone number called
        duration: Call duration in seconds
        status: Call status (success, failed)
        transcript_available: Whether transcript is available
        error_message: Optional error message if failed

    Returns:
        Number of subscribers notified
    """
    return await sse_publisher.publish(
        campaign_id,
        "call_completed",
        {
            "call_id": call_id,
            "contact_name": contact_name,
            "phone_number": phone_number,
            "duration": duration,
            "status": status,
            "transcript_available": transcript_available,
            "error_message": error_message
        }
    )
