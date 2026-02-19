"""
Zapier Webhook Integration Service for ChurchFlow

Sends webhook events to Zapier when ChurchFlow events occur.
Enables connecting ChurchFlow to 5000+ apps via Zapier.
"""

import asyncio
import logging
import hmac
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorDatabase
import aiohttp

from app.models.integration import (
    IntegrationConfig,
    ZapierWebhookConfig,
    WebhookDelivery,
    WebhookEventType,
    IntegrationStatus,
    IntegrationType
)

logger = logging.getLogger(__name__)


class ZapierWebhookService:
    """
    Send webhook events to Zapier for workflow automation.

    Features:
    - Event-driven webhooks
    - Retry on failure with exponential backoff
    - Webhook delivery tracking
    - HMAC signature verification
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize Zapier Webhook Service.

        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.integrations_collection = db.integrations
        self.deliveries_collection = db.webhook_deliveries

    async def get_active_webhooks(
        self,
        organization_id: str,
        event_type: WebhookEventType
    ) -> List[IntegrationConfig]:
        """
        Get active Zapier webhooks for a specific event type.

        Args:
            organization_id: Organization ID
            event_type: Event type to filter by

        Returns:
            List of active webhook configurations
        """
        cursor = self.integrations_collection.find({
            "organization_id": organization_id,
            "integration_type": IntegrationType.ZAPIER,
            "status": IntegrationStatus.ACTIVE,
            f"zapier_webhook.enabled_events": event_type
        })

        configs = []
        async for config_data in cursor:
            config_data["id"] = str(config_data.pop("_id"))
            configs.append(IntegrationConfig(**config_data))

        return configs

    async def save_webhook_config(
        self,
        organization_id: str,
        config: ZapierWebhookConfig
    ) -> IntegrationConfig:
        """
        Save or update Zapier webhook configuration.

        Args:
            organization_id: Organization ID
            config: Zapier webhook configuration

        Returns:
            Saved integration config
        """
        integration = IntegrationConfig(
            organization_id=organization_id,
            integration_type=IntegrationType.ZAPIER,
            status=IntegrationStatus.ACTIVE,
            zapier_webhook=config,
            updated_at=datetime.utcnow()
        )

        # Upsert integration config
        result = await self.integrations_collection.update_one(
            {
                "organization_id": organization_id,
                "integration_type": IntegrationType.ZAPIER,
                "zapier_webhook.webhook_url": str(config.webhook_url)
            },
            {"$set": integration.dict(exclude={"id"})},
            upsert=True
        )

        if result.upserted_id:
            integration.id = str(result.upserted_id)

        logger.info(f"Saved Zapier webhook for org {organization_id}")
        return integration

    async def trigger_webhook(
        self,
        organization_id: str,
        event_type: WebhookEventType,
        payload: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Trigger webhooks for a specific event.

        Args:
            organization_id: Organization ID
            event_type: Event type
            payload: Event payload

        Returns:
            List of delivery results
        """
        # Get active webhooks for this event type
        webhooks = await self.get_active_webhooks(organization_id, event_type)

        if not webhooks:
            logger.debug(f"No active webhooks for {event_type} in org {organization_id}")
            return []

        # Trigger all webhooks concurrently
        tasks = [
            self._send_webhook(
                organization_id=organization_id,
                webhook_url=str(webhook.zapier_webhook.webhook_url),
                event_type=event_type,
                payload=payload,
                config=webhook.zapier_webhook
            )
            for webhook in webhooks
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        delivery_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Webhook {i} failed: {result}")
                delivery_results.append({
                    "success": False,
                    "error": str(result),
                    "webhook_url": str(webhooks[i].zapier_webhook.webhook_url)
                })
            else:
                delivery_results.append(result)

        return delivery_results

    async def _send_webhook(
        self,
        organization_id: str,
        webhook_url: str,
        event_type: WebhookEventType,
        payload: Dict[str, Any],
        config: ZapierWebhookConfig,
        attempt: int = 1
    ) -> Dict[str, Any]:
        """
        Send a webhook to Zapier.

        Args:
            organization_id: Organization ID
            webhook_url: Webhook URL
            event_type: Event type
            payload: Event payload
            config: Webhook configuration
            attempt: Attempt number (for retries)

        Returns:
            Delivery result
        """
        # Prepare payload
        webhook_payload = {
            "event_type": event_type,
            "organization_id": organization_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": payload
        }

        # Add HMAC signature if secret key is configured
        headers = {"Content-Type": "application/json"}
        if config.secret_key:
            signature = self._generate_signature(webhook_payload, config.secret_key)
            headers["X-Zapier-Signature"] = signature

        delivery = WebhookDelivery(
            organization_id=organization_id,
            webhook_url=webhook_url,
            event_type=event_type,
            payload=webhook_payload,
            attempt_number=attempt,
            max_attempts=config.max_retries + 1
        )

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=webhook_payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=config.timeout_seconds)
                ) as response:
                    response_body = await response.text()

                    delivery.status_code = response.status
                    delivery.response_body = response_body[:1000]  # Limit response size

                    if 200 <= response.status < 300:
                        delivery.success = True
                        delivery.delivered_at = datetime.utcnow()

                        logger.info(f"Webhook delivered successfully to {webhook_url} (attempt {attempt})")
                    else:
                        delivery.success = False
                        delivery.error_message = f"HTTP {response.status}: {response_body[:200]}"

                        logger.warning(f"Webhook delivery failed: {delivery.error_message}")

        except asyncio.TimeoutError:
            delivery.success = False
            delivery.error_message = f"Timeout after {config.timeout_seconds}s"
            logger.error(f"Webhook timeout: {webhook_url}")

        except Exception as e:
            delivery.success = False
            delivery.error_message = str(e)
            logger.error(f"Webhook error: {e}")

        # Save delivery record
        await self.deliveries_collection.insert_one(
            delivery.dict(exclude={"id"})
        )

        # Retry if failed and retries are enabled
        if not delivery.success and config.retry_on_failure and attempt < config.max_retries + 1:
            # Exponential backoff: 2^attempt seconds
            retry_delay = 2 ** attempt
            delivery.next_retry_at = datetime.utcnow() + timedelta(seconds=retry_delay)

            logger.info(f"Scheduling retry {attempt + 1} in {retry_delay}s")

            await asyncio.sleep(retry_delay)

            return await self._send_webhook(
                organization_id=organization_id,
                webhook_url=webhook_url,
                event_type=event_type,
                payload=payload,
                config=config,
                attempt=attempt + 1
            )

        return {
            "success": delivery.success,
            "webhook_url": webhook_url,
            "status_code": delivery.status_code,
            "attempt": attempt,
            "error": delivery.error_message
        }

    def _generate_signature(self, payload: Dict[str, Any], secret: str) -> str:
        """
        Generate HMAC signature for webhook verification.

        Args:
            payload: Webhook payload
            secret: Secret key

        Returns:
            HMAC signature (hex)
        """
        import json
        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()

        return signature

    async def get_delivery_history(
        self,
        organization_id: str,
        event_type: Optional[WebhookEventType] = None,
        webhook_url: Optional[str] = None,
        limit: int = 50
    ) -> List[WebhookDelivery]:
        """
        Get webhook delivery history.

        Args:
            organization_id: Organization ID
            event_type: Optional event type filter
            webhook_url: Optional webhook URL filter
            limit: Maximum deliveries to return

        Returns:
            List of webhook deliveries
        """
        query = {"organization_id": organization_id}

        if event_type:
            query["event_type"] = event_type

        if webhook_url:
            query["webhook_url"] = webhook_url

        cursor = self.deliveries_collection.find(query).sort(
            "created_at", -1
        ).limit(limit)

        deliveries = []
        async for delivery_data in cursor:
            delivery_data["id"] = str(delivery_data.pop("_id"))
            deliveries.append(WebhookDelivery(**delivery_data))

        return deliveries

    async def get_delivery_stats(
        self,
        organization_id: str,
        webhook_url: Optional[str] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get delivery statistics.

        Args:
            organization_id: Organization ID
            webhook_url: Optional webhook URL filter
            days: Number of days to analyze

        Returns:
            Delivery statistics
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        match_stage = {
            "organization_id": organization_id,
            "created_at": {"$gte": start_date}
        }

        if webhook_url:
            match_stage["webhook_url"] = webhook_url

        pipeline = [
            {"$match": match_stage},
            {
                "$group": {
                    "_id": None,
                    "total_deliveries": {"$sum": 1},
                    "successful_deliveries": {
                        "$sum": {"$cond": ["$success", 1, 0]}
                    },
                    "failed_deliveries": {
                        "$sum": {"$cond": ["$success", 0, 1]}
                    },
                    "avg_attempts": {"$avg": "$attempt_number"}
                }
            }
        ]

        result = await self.deliveries_collection.aggregate(pipeline).to_list(length=1)

        if not result:
            return {
                "total_deliveries": 0,
                "successful_deliveries": 0,
                "failed_deliveries": 0,
                "success_rate": 0.0,
                "avg_attempts": 0.0
            }

        stats = result[0]
        total = stats["total_deliveries"]
        successful = stats["successful_deliveries"]

        return {
            "total_deliveries": total,
            "successful_deliveries": successful,
            "failed_deliveries": stats["failed_deliveries"],
            "success_rate": successful / total if total > 0 else 0.0,
            "avg_attempts": round(stats["avg_attempts"], 2)
        }

    async def delete_webhook_config(
        self,
        organization_id: str,
        webhook_url: str
    ) -> bool:
        """
        Delete a webhook configuration.

        Args:
            organization_id: Organization ID
            webhook_url: Webhook URL

        Returns:
            True if successful
        """
        result = await self.integrations_collection.delete_one({
            "organization_id": organization_id,
            "integration_type": IntegrationType.ZAPIER,
            "zapier_webhook.webhook_url": webhook_url
        })

        logger.info(f"Deleted webhook {webhook_url} for org {organization_id}")
        return result.deleted_count > 0

    async def test_webhook(
        self,
        organization_id: str,
        webhook_url: str
    ) -> Dict[str, Any]:
        """
        Test a webhook with sample data.

        Args:
            organization_id: Organization ID
            webhook_url: Webhook URL

        Returns:
            Test result
        """
        test_payload = {
            "test": True,
            "message": "This is a test webhook from ChurchFlow",
            "organization_id": organization_id,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Get webhook config
        config_data = await self.integrations_collection.find_one({
            "organization_id": organization_id,
            "integration_type": IntegrationType.ZAPIER,
            "zapier_webhook.webhook_url": webhook_url
        })

        if not config_data:
            return {
                "success": False,
                "error": "Webhook configuration not found"
            }

        config_data["id"] = str(config_data.pop("_id"))
        integration = IntegrationConfig(**config_data)

        # Send test webhook
        result = await self._send_webhook(
            organization_id=organization_id,
            webhook_url=webhook_url,
            event_type=WebhookEventType.REGISTRATION_CREATED,  # Use a standard event type for testing
            payload=test_payload,
            config=integration.zapier_webhook,
            attempt=1
        )

        return result
