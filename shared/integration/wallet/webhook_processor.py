"""
Webhook Processor - Handle Payment Provider Webhooks

This module provides webhook processing capabilities with:
- Signature verification
- Automatic retry with exponential backoff
- Failed event logging
- Manual retry interface
- Duplicate event detection

Author: KasaAI Team
Date: 2025-10-27
"""

import logging
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

from .models import (
    PaymentProvider,
    TransactionStatus,
    WebhookEvent,
)
from .exceptions import (
    InvalidWebhookSignatureError,
    TransactionNotFoundError,
    ProviderAPIError,
)
from .wallet_service import WalletService
from .providers.base import BasePaymentProvider


logger = logging.getLogger(__name__)


class WebhookStatus(str, Enum):
    """Webhook processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class WebhookProcessor:
    """
    Process payment provider webhooks with retry logic.

    This processor:
    1. Verifies webhook signatures
    2. Prevents duplicate processing
    3. Processes webhooks with automatic retries
    4. Logs all webhook events for audit trail
    5. Supports manual retry for failed webhooks

    Example:
        ```python
        # Initialize
        webhook_processor = WebhookProcessor(
            wallet_service=wallet_service,
            database=db
        )

        # Register providers (same instances as WalletService)
        webhook_processor.register_provider(PaymentProvider.STRIPE, stripe_provider)

        # Process webhook from Stripe
        result = await webhook_processor.process_webhook(
            provider=PaymentProvider.STRIPE,
            payload={"id": "evt_123", ...},
            signature="stripe_signature",
            raw_payload=raw_body,
            headers=request_headers
        )
        ```
    """

    def __init__(
        self,
        wallet_service: WalletService,
        database,
        max_retries: int = 5,
        initial_retry_delay: int = 60,  # seconds
        max_retry_delay: int = 3600,  # 1 hour
    ):
        """
        Initialize webhook processor.

        Args:
            wallet_service: WalletService instance
            database: MongoDB database instance
            max_retries: Maximum number of retry attempts
            initial_retry_delay: Initial retry delay in seconds
            max_retry_delay: Maximum retry delay in seconds (for exponential backoff)
        """
        self.wallet_service = wallet_service
        self.db = database
        self.webhook_events_collection = database.webhook_events
        self.max_retries = max_retries
        self.initial_retry_delay = initial_retry_delay
        self.max_retry_delay = max_retry_delay

        # Provider registry (shared with WalletService)
        self.providers: Dict[PaymentProvider, BasePaymentProvider] = {}

        logger.info(
            f"WebhookProcessor initialized with max_retries={max_retries}, "
            f"initial_delay={initial_retry_delay}s"
        )

    def register_provider(
        self,
        provider: PaymentProvider,
        provider_instance: BasePaymentProvider
    ) -> None:
        """
        Register a payment provider.

        Args:
            provider: Payment provider enum
            provider_instance: Initialized provider instance
        """
        self.providers[provider] = provider_instance
        logger.info(f"Registered webhook provider: {provider.value}")

    def get_provider(self, provider: PaymentProvider) -> BasePaymentProvider:
        """Get registered provider instance."""
        if provider not in self.providers:
            # Try to get from WalletService
            return self.wallet_service.get_provider(provider)
        return self.providers[provider]

    async def _save_webhook_event(
        self,
        provider: PaymentProvider,
        event_id: str,
        event_type: str,
        payload: Dict[str, Any],
        status: WebhookStatus,
        transaction_id: Optional[str] = None,
        error_message: Optional[str] = None,
        retry_count: int = 0,
        next_retry_at: Optional[datetime] = None
    ) -> WebhookEvent:
        """
        Save webhook event to database.

        Args:
            provider: Payment provider
            event_id: Provider's event ID
            event_type: Event type from provider
            payload: Raw webhook payload
            status: Processing status
            transaction_id: Associated transaction ID
            error_message: Error message if failed
            retry_count: Number of retry attempts
            next_retry_at: Next retry timestamp

        Returns:
            WebhookEvent instance
        """
        webhook_event = WebhookEvent(
            provider=provider,
            event_id=event_id,
            event_type=event_type,
            payload=payload,
            status=status.value,
            transaction_id=transaction_id,
            error_message=error_message,
            retry_count=retry_count,
            next_retry_at=next_retry_at,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        await self.webhook_events_collection.insert_one(webhook_event.dict())

        logger.info(
            f"Saved webhook event: provider={provider.value}, "
            f"event_id={event_id}, status={status.value}"
        )

        return webhook_event

    async def _update_webhook_event(
        self,
        event_id: str,
        status: WebhookStatus,
        transaction_id: Optional[str] = None,
        error_message: Optional[str] = None,
        retry_count: Optional[int] = None,
        next_retry_at: Optional[datetime] = None,
        processed_at: Optional[datetime] = None
    ) -> None:
        """
        Update webhook event status.

        Args:
            event_id: Provider's event ID
            status: New status
            transaction_id: Transaction ID if processed
            error_message: Error message if failed
            retry_count: Updated retry count
            next_retry_at: Next retry timestamp
            processed_at: Processing completion timestamp
        """
        update_data = {
            "status": status.value,
            "updated_at": datetime.utcnow(),
        }

        if transaction_id:
            update_data["transaction_id"] = transaction_id
        if error_message:
            update_data["error_message"] = error_message
        if retry_count is not None:
            update_data["retry_count"] = retry_count
        if next_retry_at:
            update_data["next_retry_at"] = next_retry_at
        if processed_at:
            update_data["processed_at"] = processed_at

        await self.webhook_events_collection.update_one(
            {"event_id": event_id},
            {"$set": update_data}
        )

        logger.info(f"Updated webhook event {event_id} to status {status.value}")

    async def _check_duplicate_event(self, event_id: str) -> Optional[WebhookEvent]:
        """
        Check if webhook event was already processed.

        Args:
            event_id: Provider's event ID

        Returns:
            WebhookEvent if found, None otherwise
        """
        event_dict = await self.webhook_events_collection.find_one({
            "event_id": event_id
        })

        if event_dict:
            return WebhookEvent(**event_dict)

        return None

    def _calculate_next_retry(self, retry_count: int) -> datetime:
        """
        Calculate next retry timestamp using exponential backoff.

        Formula: delay = min(initial_delay * (2 ^ retry_count), max_delay)

        Args:
            retry_count: Current retry count

        Returns:
            Next retry timestamp
        """
        delay = min(
            self.initial_retry_delay * (2 ** retry_count),
            self.max_retry_delay
        )

        next_retry = datetime.utcnow() + timedelta(seconds=delay)

        logger.debug(
            f"Calculated next retry: retry_count={retry_count}, "
            f"delay={delay}s, next_retry={next_retry}"
        )

        return next_retry

    async def process_webhook(
        self,
        provider: PaymentProvider,
        payload: Dict[str, Any],
        signature: Optional[str] = None,
        raw_payload: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        skip_signature_verification: bool = False
    ) -> Dict[str, Any]:
        """
        Process webhook from payment provider.

        This method:
        1. Checks for duplicate events
        2. Verifies webhook signature
        3. Processes webhook event
        4. Saves event to database
        5. Updates transaction status
        6. Schedules retry if processing fails

        Args:
            provider: Payment provider
            payload: Webhook payload (parsed JSON)
            signature: Webhook signature
            raw_payload: Raw webhook body (for signature verification)
            headers: Request headers
            skip_signature_verification: Skip signature check (for testing)

        Returns:
            Dict with processing result:
            {
                "success": bool,
                "event_id": str,
                "transaction_id": Optional[str],
                "message": str,
                "status": str
            }

        Raises:
            InvalidWebhookSignatureError: If signature verification fails

        Example:
            ```python
            result = await webhook_processor.process_webhook(
                provider=PaymentProvider.STRIPE,
                payload=webhook_payload,
                signature=request.headers.get("Stripe-Signature"),
                raw_payload=request.body,
                headers=request.headers
            )

            if result["success"]:
                return {"status": "ok"}
            else:
                return {"status": "error", "message": result["message"]}
            ```
        """
        # Get provider instance
        try:
            provider_instance = self.get_provider(provider)
        except Exception as e:
            logger.error(f"Provider not configured: {provider.value}")
            return {
                "success": False,
                "event_id": None,
                "transaction_id": None,
                "message": f"Provider not configured: {str(e)}",
                "status": WebhookStatus.FAILED.value
            }

        # Extract event ID and type from payload
        # This is provider-specific
        event_id = payload.get("id") or payload.get("event_id") or payload.get("data", {}).get("id")
        event_type = payload.get("type") or payload.get("event") or payload.get("event_type")

        if not event_id:
            logger.error("Webhook payload missing event ID")
            return {
                "success": False,
                "event_id": None,
                "transaction_id": None,
                "message": "Webhook payload missing event ID",
                "status": WebhookStatus.FAILED.value
            }

        # Check for duplicate event
        existing_event = await self._check_duplicate_event(event_id)
        if existing_event:
            logger.info(f"Duplicate webhook event detected: {event_id}")
            return {
                "success": True,
                "event_id": event_id,
                "transaction_id": existing_event.transaction_id,
                "message": "Duplicate event (already processed)",
                "status": existing_event.status
            }

        # Verify webhook signature (unless skipped)
        if not skip_signature_verification:
            try:
                is_valid = await provider_instance.verify_webhook(
                    payload=payload,
                    signature=signature,
                    raw_payload=raw_payload,
                    headers=headers
                )

                if not is_valid:
                    logger.error(f"Invalid webhook signature from {provider.value}")
                    await self._save_webhook_event(
                        provider=provider,
                        event_id=event_id,
                        event_type=event_type,
                        payload=payload,
                        status=WebhookStatus.FAILED,
                        error_message="Invalid webhook signature"
                    )
                    raise InvalidWebhookSignatureError(provider=provider.value)

            except Exception as e:
                logger.error(f"Signature verification error: {e}")
                await self._save_webhook_event(
                    provider=provider,
                    event_id=event_id,
                    event_type=event_type,
                    payload=payload,
                    status=WebhookStatus.FAILED,
                    error_message=f"Signature verification error: {str(e)}"
                )
                raise

        # Save webhook event as pending
        await self._save_webhook_event(
            provider=provider,
            event_id=event_id,
            event_type=event_type,
            payload=payload,
            status=WebhookStatus.PENDING
        )

        # Process webhook
        try:
            # Update status to processing
            await self._update_webhook_event(
                event_id=event_id,
                status=WebhookStatus.PROCESSING
            )

            # Process with provider
            success, transaction_id, provider_data = await provider_instance.process_webhook(payload)

            if success and transaction_id:
                # Update transaction based on webhook result
                await self._handle_webhook_success(
                    provider=provider,
                    transaction_id=transaction_id,
                    provider_data=provider_data or {}
                )

                # Update webhook event as completed
                await self._update_webhook_event(
                    event_id=event_id,
                    status=WebhookStatus.COMPLETED,
                    transaction_id=transaction_id,
                    processed_at=datetime.utcnow()
                )

                logger.info(
                    f"Webhook processed successfully: event={event_id}, "
                    f"transaction={transaction_id}"
                )

                return {
                    "success": True,
                    "event_id": event_id,
                    "transaction_id": transaction_id,
                    "message": "Webhook processed successfully",
                    "status": WebhookStatus.COMPLETED.value
                }

            else:
                # Processing failed
                error_msg = provider_data.get("error") if provider_data else "Unknown error"
                logger.error(
                    f"Webhook processing failed: event={event_id}, error={error_msg}"
                )

                # Schedule retry
                next_retry = self._calculate_next_retry(0)
                await self._update_webhook_event(
                    event_id=event_id,
                    status=WebhookStatus.RETRYING,
                    error_message=error_msg,
                    retry_count=0,
                    next_retry_at=next_retry
                )

                return {
                    "success": False,
                    "event_id": event_id,
                    "transaction_id": transaction_id,
                    "message": f"Webhook processing failed: {error_msg}",
                    "status": WebhookStatus.RETRYING.value
                }

        except Exception as e:
            logger.error(f"Webhook processing error: {e}", exc_info=True)

            # Schedule retry
            next_retry = self._calculate_next_retry(0)
            await self._update_webhook_event(
                event_id=event_id,
                status=WebhookStatus.RETRYING,
                error_message=str(e),
                retry_count=0,
                next_retry_at=next_retry
            )

            return {
                "success": False,
                "event_id": event_id,
                "transaction_id": None,
                "message": f"Webhook processing error: {str(e)}",
                "status": WebhookStatus.RETRYING.value
            }

    async def _handle_webhook_success(
        self,
        provider: PaymentProvider,
        transaction_id: str,
        provider_data: Dict[str, Any]
    ) -> None:
        """
        Handle successful webhook processing.

        Args:
            provider: Payment provider
            transaction_id: Transaction ID
            provider_data: Provider-specific data

        Raises:
            TransactionNotFoundError: If transaction not found
        """
        # Get transaction
        try:
            transaction = await self.wallet_service.get_transaction(transaction_id)
        except TransactionNotFoundError:
            logger.error(f"Transaction not found: {transaction_id}")
            raise

        # Extract status from provider data
        status = provider_data.get("status", "succeeded")
        provider_transaction_id = provider_data.get("provider_transaction_id")

        # Update transaction based on status
        if status in ["succeeded", "completed", "success"]:
            # Mark deposit as successful
            await self.wallet_service.process_deposit_success(
                transaction_id=transaction_id,
                provider_transaction_id=provider_transaction_id or transaction.provider_transaction_id,
                provider_response=provider_data
            )

        elif status in ["failed", "canceled", "cancelled"]:
            # Mark deposit as failed
            failure_reason = provider_data.get("failure_reason") or provider_data.get("error") or "Payment failed"
            await self.wallet_service.process_deposit_failure(
                transaction_id=transaction_id,
                reason=failure_reason,
                provider_response=provider_data
            )

        else:
            logger.warning(
                f"Unknown webhook status for transaction {transaction_id}: {status}"
            )

    async def retry_failed_webhooks(self) -> int:
        """
        Retry failed webhook events that are due for retry.

        This method should be called periodically (e.g., every minute)
        to process webhooks that failed and are scheduled for retry.

        Returns:
            Number of webhooks retried

        Example:
            ```python
            # In a background task or cron job
            while True:
                retried_count = await webhook_processor.retry_failed_webhooks()
                logger.info(f"Retried {retried_count} failed webhooks")
                await asyncio.sleep(60)  # Check every minute
            ```
        """
        # Find webhooks due for retry
        now = datetime.utcnow()
        cursor = self.webhook_events_collection.find({
            "status": WebhookStatus.RETRYING.value,
            "next_retry_at": {"$lte": now},
            "retry_count": {"$lt": self.max_retries}
        })

        retry_count = 0

        async for event_dict in cursor:
            event = WebhookEvent(**event_dict)

            logger.info(
                f"Retrying webhook: event_id={event.event_id}, "
                f"retry_count={event.retry_count + 1}/{self.max_retries}"
            )

            try:
                # Retry processing
                provider_instance = self.get_provider(event.provider)

                success, transaction_id, provider_data = await provider_instance.process_webhook(
                    event.payload
                )

                if success and transaction_id:
                    # Retry successful
                    await self._handle_webhook_success(
                        provider=event.provider,
                        transaction_id=transaction_id,
                        provider_data=provider_data or {}
                    )

                    await self._update_webhook_event(
                        event_id=event.event_id,
                        status=WebhookStatus.COMPLETED,
                        transaction_id=transaction_id,
                        processed_at=datetime.utcnow()
                    )

                    logger.info(f"Webhook retry successful: {event.event_id}")
                    retry_count += 1

                else:
                    # Retry failed
                    new_retry_count = event.retry_count + 1

                    if new_retry_count >= self.max_retries:
                        # Max retries reached, mark as permanently failed
                        await self._update_webhook_event(
                            event_id=event.event_id,
                            status=WebhookStatus.FAILED,
                            error_message=f"Max retries ({self.max_retries}) reached",
                            retry_count=new_retry_count
                        )
                        logger.error(
                            f"Webhook retry failed permanently: {event.event_id} "
                            f"(max retries reached)"
                        )
                    else:
                        # Schedule next retry
                        next_retry = self._calculate_next_retry(new_retry_count)
                        await self._update_webhook_event(
                            event_id=event.event_id,
                            status=WebhookStatus.RETRYING,
                            retry_count=new_retry_count,
                            next_retry_at=next_retry
                        )
                        logger.info(
                            f"Webhook retry failed, will retry again: {event.event_id}"
                        )

            except Exception as e:
                logger.error(f"Error retrying webhook {event.event_id}: {e}", exc_info=True)

                new_retry_count = event.retry_count + 1

                if new_retry_count >= self.max_retries:
                    # Max retries reached
                    await self._update_webhook_event(
                        event_id=event.event_id,
                        status=WebhookStatus.FAILED,
                        error_message=str(e),
                        retry_count=new_retry_count
                    )
                else:
                    # Schedule next retry
                    next_retry = self._calculate_next_retry(new_retry_count)
                    await self._update_webhook_event(
                        event_id=event.event_id,
                        status=WebhookStatus.RETRYING,
                        error_message=str(e),
                        retry_count=new_retry_count,
                        next_retry_at=next_retry
                    )

        logger.info(f"Retried {retry_count} webhooks")
        return retry_count

    async def get_failed_webhooks(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> List[WebhookEvent]:
        """
        Get list of permanently failed webhooks.

        Args:
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            List of failed webhook events
        """
        cursor = self.webhook_events_collection.find({
            "status": WebhookStatus.FAILED.value
        }).sort("created_at", -1).skip(offset).limit(limit)

        failed_webhooks = []
        async for doc in cursor:
            failed_webhooks.append(WebhookEvent(**doc))

        return failed_webhooks

    async def manually_retry_webhook(self, event_id: str) -> Dict[str, Any]:
        """
        Manually retry a failed webhook.

        This is useful for debugging or retrying after fixing an issue.

        Args:
            event_id: Webhook event ID

        Returns:
            Processing result

        Example:
            ```python
            # Admin endpoint to manually retry
            result = await webhook_processor.manually_retry_webhook(
                event_id="evt_123"
            )
            ```
        """
        event_dict = await self.webhook_events_collection.find_one({
            "event_id": event_id
        })

        if not event_dict:
            return {
                "success": False,
                "message": f"Webhook event not found: {event_id}"
            }

        event = WebhookEvent(**event_dict)

        logger.info(f"Manual retry requested for webhook: {event_id}")

        # Reset status to retrying
        await self._update_webhook_event(
            event_id=event_id,
            status=WebhookStatus.RETRYING,
            next_retry_at=datetime.utcnow()
        )

        # Process immediately
        return await self.process_webhook(
            provider=event.provider,
            payload=event.payload,
            skip_signature_verification=True  # Skip signature check for manual retry
        )
