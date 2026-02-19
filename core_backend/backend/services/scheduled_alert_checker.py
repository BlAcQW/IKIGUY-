"""
Scheduled Alert Checker Service

Periodically checks profit margins and sends alerts when thresholds are exceeded.
Runs as a background task using APScheduler.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
import asyncio

from ..mongo import get_database
from apps.shared.services.alert_service import AlertService
from ..services.analytics_service import analytics_service

logger = logging.getLogger(__name__)


class ScheduledAlertChecker:
    """
    Background service that periodically checks profit margins and sends alerts.
    """

    def __init__(self):
        """Initialize the alert checker."""
        self.last_check = None
        self.check_count = 0
        self.alerts_sent_count = 0

    async def check_margins_and_alert(self):
        """
        Check all profit margins and send alerts for threshold violations.

        This method is called periodically by the scheduler.
        """
        try:
            logger.info("🔍 Starting scheduled margin check...")
            check_start = datetime.utcnow()

            # Get database
            db = get_database()
            alert_service = AlertService(db)

            # Get profit margin analytics for last 24 hours
            # This gives us recent data to check
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(hours=24)

            # Get profit margin data
            try:
                profit_analytics = await analytics_service.get_profit_margin_analytics(
                    start_date=start_date,
                    end_date=end_date
                )
            except Exception as e:
                logger.error(f"Failed to get profit margin analytics: {e}")
                return

            if not profit_analytics:
                logger.warning("No profit analytics data available")
                return

            # Extract provider breakdown
            breakdown = profit_analytics.get("profit_analytics", {}).get("breakdown_by_provider", [])

            if not breakdown:
                logger.info("No provider data to check")
                return

            logger.info(f"Checking {len(breakdown)} providers for margin issues...")

            # Check each provider and send alerts if needed
            alert_result = await alert_service.check_and_send_alerts(
                provider_data=breakdown,
                tenant_id=None  # Check all organizations
            )

            # Update statistics
            alerts_sent = alert_result.get("total_sent", 0)
            alerts_suppressed = alert_result.get("total_suppressed", 0)

            self.last_check = check_start
            self.check_count += 1
            self.alerts_sent_count += alerts_sent

            # Log results
            check_duration = (datetime.utcnow() - check_start).total_seconds()

            logger.info(
                f"✅ Margin check complete: "
                f"{alerts_sent} alerts sent, "
                f"{alerts_suppressed} suppressed, "
                f"took {check_duration:.2f}s"
            )

            # Log details of sent alerts
            if alerts_sent > 0:
                for alert in alert_result.get("alerts_sent", []):
                    provider = alert.get("provider")
                    severity = alert.get("severity")
                    margin = alert.get("margin", 0)
                    logger.warning(
                        f"🚨 Alert sent: {provider} ({severity}) - Margin: {margin:.2f}%"
                    )

        except Exception as e:
            logger.error(f"Error in scheduled margin check: {e}", exc_info=True)

    def get_stats(self) -> dict:
        """
        Get statistics about the alert checker.

        Returns:
            Dict with checker statistics
        """
        return {
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "check_count": self.check_count,
            "alerts_sent_count": self.alerts_sent_count,
            "status": "active" if self.last_check else "not_started"
        }


# Global instance
alert_checker = ScheduledAlertChecker()


def schedule_alert_checks(scheduler):
    """
    Schedule periodic margin checks using APScheduler.

    Args:
        scheduler: APScheduler BackgroundScheduler instance
    """
    from apscheduler.triggers.cron import CronTrigger

    # Wrapper function for synchronous scheduler
    def run_check():
        """Wrapper to run async check in sync context."""
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(alert_checker.check_margins_and_alert())
            loop.close()
        except Exception as e:
            logger.error(f"Failed to run scheduled margin check: {e}", exc_info=True)

    # Schedule to run every hour at :00 minutes
    # Example: 00:00, 01:00, 02:00, etc.
    trigger = CronTrigger(minute=0, second=0)

    scheduler.add_job(
        run_check,
        trigger=trigger,
        id="margin_alert_checker",
        name="Profit Margin Alert Checker",
        replace_existing=True,
        max_instances=1,  # Only one instance at a time
        coalesce=True,    # If multiple missed, run once
        misfire_grace_time=300  # 5 minutes grace period
    )

    logger.info("✅ Scheduled alert checker configured (runs every hour)")


def get_alert_checker_stats() -> dict:
    """
    Get statistics about the alert checker.

    Returns:
        Dict with checker statistics
    """
    return alert_checker.get_stats()
