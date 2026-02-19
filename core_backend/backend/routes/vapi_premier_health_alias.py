"""
VAPI Premier Health Webhook Alias

This module provides an alias route for /vapi/webhooks/premier-health
that forwards to the actual Premier Health webhook handler.

This is needed because VAPI is configured to call /vapi/webhooks/premier-health
but our actual handler is at /premier-health/vapi-webhook.
"""

from fastapi import APIRouter, BackgroundTasks, Request
from ..routes.premier_health import handle_vapi_webhook, VAPIWebhookRequest
import logging
import json

logger = logging.getLogger(__name__)

# Create router WITHOUT prefix so we can use the full path
router = APIRouter(tags=["VAPI Premier Health Alias"])


@router.post("/vapi/webhooks/premier-health")
async def vapi_premier_health_webhook_alias(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Alias route for VAPI Premier Health webhook.

    Forwards requests from /vapi/webhooks/premier-health
    to the actual Premier Health webhook handler.

    This exists because VAPI is configured with this URL pattern
    but our actual handler uses a different path.
    """
    try:
        # Get the request body
        body = await request.body()
        payload = json.loads(body.decode())

        logger.info("🔀 Forwarding request from /vapi/webhooks/premier-health to premier_health handler")

        # Parse into VAPIWebhookRequest model
        webhook_request = VAPIWebhookRequest(**payload)

        # Forward to the actual handler
        result = await handle_vapi_webhook(webhook_request, background_tasks)

        logger.info("✅ Successfully forwarded and processed webhook")
        return result

    except Exception as e:
        logger.error(f"❌ Error in webhook alias: {str(e)}")
        return {
            "error": f"Webhook alias error: {str(e)}",
            "message": {
                "type": "assistant",
                "content": "I apologize, but I'm having trouble processing your request right now. Please try again."
            }
        }
