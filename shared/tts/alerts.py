"""
TTS Alert Manager

Monitors TTS provider health and sends email notifications for failures.
Includes 30-minute cooldown to prevent alert spam.

Usage:
    from apps.shared.tts.alerts import TTSAlertManager, AlertType
    from motor.motor_asyncio import AsyncIOMotorClient

    client = AsyncIOMotorClient("mongodb://localhost:27017")
    alert_manager = TTSAlertManager(
        database=client.tts_alerts,
        smtp_config={
            "host": "smtp.gmail.com",
            "port": 587,
            "username": "alerts@example.com",
            "password": "password",
            "from_address": "alerts@example.com"
        }
    )

    # Send alert
    await alert_manager.send_alert(
        alert_type=AlertType.PROVIDER_DOWN,
        message="Coqui XTTS provider is offline",
        metadata={"provider": "coqui_xtts"},
        recipients=["admin@example.com"]
    )

Author: KasaAI Team
Date: 2025-11-23
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from enum import Enum
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, EmailStr

logger = logging.getLogger(__name__)


class AlertType(str, Enum):
    """Types of TTS alerts."""
    PROVIDER_DOWN = "provider_down"
    HIGH_LATENCY = "high_latency"
    QUOTA_EXCEEDED = "quota_exceeded"
    SYNTHESIS_FAILED = "synthesis_failed"
    CACHE_ERROR = "cache_error"
    BILLING_ERROR = "billing_error"


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class Alert(BaseModel):
    """Alert record."""
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    metadata: Dict[str, Any]
    recipients: List[str]
    sent_at: datetime
    cooldown_until: datetime


class TTSAlertManager:
    """
    Manages TTS system alerts and notifications.

    Features:
    - SMTP email notifications
    - 30-minute cooldown per alert type
    - Alert history tracking
    - HTML email templates
    """

    def __init__(
        self,
        database: AsyncIOMotorDatabase,
        smtp_config: Optional[Dict[str, Any]] = None,
        cooldown_minutes: int = 30,
        collection_name: str = "tts_alerts"
    ):
        """
        Initialize TTS alert manager.

        Args:
            database: Motor AsyncIO MongoDB database instance
            smtp_config: SMTP configuration dict with keys:
                - host: SMTP server hostname
                - port: SMTP server port
                - username: SMTP username
                - password: SMTP password
                - from_address: Email from address
                - use_tls: Use TLS (default: True)
            cooldown_minutes: Cooldown period in minutes (default: 30)
            collection_name: MongoDB collection for alert history
        """
        self.database = database
        self.smtp_config = smtp_config
        self.cooldown_minutes = cooldown_minutes
        self.collection_name = collection_name

        # Alert history collection
        self.alerts_collection = database[collection_name]

        # Validate SMTP config
        if smtp_config:
            required_keys = ["host", "port", "username", "password", "from_address"]
            missing_keys = [k for k in required_keys if k not in smtp_config]
            if missing_keys:
                logger.warning(
                    f"SMTP config missing keys: {missing_keys}. "
                    "Email notifications will be disabled."
                )
                self.smtp_config = None

        logger.info(
            f"TTSAlertManager initialized: "
            f"smtp={'enabled' if self.smtp_config else 'disabled'}, "
            f"cooldown={cooldown_minutes}min"
        )

    async def ensure_indexes(self):
        """
        Create indexes for alert history.

        Should be called once at application startup.
        """
        # Index on alert_type and sent_at for cooldown checks
        await self.alerts_collection.create_index(
            [("alert_type", 1), ("sent_at", -1)],
            name="alert_type_sent_at_index"
        )

        # Index on cooldown_until for cleanup queries
        await self.alerts_collection.create_index(
            "cooldown_until",
            name="cooldown_until_index"
        )

        logger.info("Alert indexes created successfully")

    async def check_cooldown(self, alert_type: AlertType) -> bool:
        """
        Check if alert type is in cooldown period.

        Args:
            alert_type: Type of alert to check

        Returns:
            True if in cooldown (should NOT send), False if OK to send
        """
        try:
            # Find most recent alert of this type
            recent_alert = await self.alerts_collection.find_one(
                {"alert_type": alert_type.value},
                sort=[("sent_at", -1)]
            )

            if not recent_alert:
                logger.debug(f"No cooldown for {alert_type.value} (no previous alerts)")
                return False

            # Check if still in cooldown
            cooldown_until = recent_alert["cooldown_until"]
            now = datetime.utcnow()

            if now < cooldown_until:
                remaining = (cooldown_until - now).total_seconds() / 60
                logger.debug(
                    f"Alert {alert_type.value} in cooldown "
                    f"({remaining:.1f} minutes remaining)"
                )
                return True

            logger.debug(f"Cooldown expired for {alert_type.value}, OK to send")
            return False

        except Exception as e:
            logger.error(f"Cooldown check error: {str(e)}")
            # On error, allow sending (fail open)
            return False

    async def send_alert(
        self,
        alert_type: AlertType,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
        recipients: Optional[List[str]] = None,
        severity: AlertSeverity = AlertSeverity.ERROR,
        force: bool = False
    ) -> bool:
        """
        Send alert notification.

        Args:
            alert_type: Type of alert
            message: Alert message
            metadata: Additional alert metadata
            recipients: Email recipients (uses default if not provided)
            severity: Alert severity level
            force: Force send even if in cooldown

        Returns:
            True if alert was sent, False if skipped (cooldown or error)
        """
        try:
            # Check cooldown
            if not force and await self.check_cooldown(alert_type):
                logger.info(f"Alert {alert_type.value} skipped (in cooldown)")
                return False

            # Prepare alert
            now = datetime.utcnow()
            cooldown_until = now + timedelta(minutes=self.cooldown_minutes)

            # Default recipients (admin email from metadata or config)
            if not recipients:
                recipients = metadata.get("recipients", ["admin@ailabsafrica.com"])

            alert = Alert(
                alert_type=alert_type,
                severity=severity,
                message=message,
                metadata=metadata or {},
                recipients=recipients,
                sent_at=now,
                cooldown_until=cooldown_until
            )

            # Send email notification
            if self.smtp_config:
                email_sent = await self._send_email(alert)
                if not email_sent:
                    logger.warning(f"Failed to send email for alert: {alert_type.value}")
            else:
                logger.warning("SMTP not configured, alert logged but not emailed")

            # Save to alert history
            await self.alerts_collection.insert_one(alert.dict())

            logger.info(
                f"Alert sent: type={alert_type.value}, severity={severity.value}, "
                f"recipients={len(recipients)}"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to send alert: {str(e)}")
            return False

    async def get_alert_history(
        self,
        hours: int = 24,
        alert_type: Optional[AlertType] = None,
        severity: Optional[AlertSeverity] = None,
        limit: int = 100
    ) -> List[Alert]:
        """
        Get alert history.

        Args:
            hours: Number of hours to look back (default: 24)
            alert_type: Filter by alert type (optional)
            severity: Filter by severity (optional)
            limit: Maximum alerts to return

        Returns:
            List of alerts
        """
        try:
            # Build query
            query = {
                "sent_at": {"$gte": datetime.utcnow() - timedelta(hours=hours)}
            }

            if alert_type:
                query["alert_type"] = alert_type.value

            if severity:
                query["severity"] = severity.value

            # Query alerts
            cursor = self.alerts_collection.find(query).sort("sent_at", -1).limit(limit)

            alerts = []
            async for alert_doc in cursor:
                alerts.append(Alert(**alert_doc))

            logger.debug(f"Retrieved {len(alerts)} alerts from last {hours}h")

            return alerts

        except Exception as e:
            logger.error(f"Failed to retrieve alert history: {str(e)}")
            return []

    async def clear_old_alerts(self, days: int = 30) -> int:
        """
        Clear alerts older than specified days.

        Args:
            days: Delete alerts older than this many days

        Returns:
            Number of alerts deleted
        """
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)

            result = await self.alerts_collection.delete_many({
                "sent_at": {"$lt": cutoff}
            })

            count = result.deleted_count

            if count > 0:
                logger.info(f"Deleted {count} alerts older than {days} days")

            return count

        except Exception as e:
            logger.error(f"Failed to clear old alerts: {str(e)}")
            return 0

    async def _send_email(self, alert: Alert) -> bool:
        """
        Send email notification via SMTP.

        Args:
            alert: Alert to send

        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.smtp_config:
            logger.warning("SMTP not configured, cannot send email")
            return False

        try:
            # Create email
            msg = MIMEMultipart("alternative")
            msg["Subject"] = self._get_email_subject(alert)
            msg["From"] = self.smtp_config["from_address"]
            msg["To"] = ", ".join(alert.recipients)

            # Generate email body (HTML and plain text)
            html_body = self._generate_html_email(alert)
            text_body = self._generate_text_email(alert)

            # Attach both versions
            msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            # Send via SMTP
            use_tls = self.smtp_config.get("use_tls", True)

            with smtplib.SMTP(self.smtp_config["host"], self.smtp_config["port"]) as server:
                if use_tls:
                    server.starttls()

                server.login(self.smtp_config["username"], self.smtp_config["password"])
                server.sendmail(
                    self.smtp_config["from_address"],
                    alert.recipients,
                    msg.as_string()
                )

            logger.info(f"Email sent to {len(alert.recipients)} recipients")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False

    def _get_email_subject(self, alert: Alert) -> str:
        """Generate email subject line."""
        severity_emoji = {
            AlertSeverity.INFO: "ℹ️",
            AlertSeverity.WARNING: "⚠️",
            AlertSeverity.ERROR: "❌",
            AlertSeverity.CRITICAL: "🚨"
        }

        emoji = severity_emoji.get(alert.severity, "📢")

        return f"{emoji} TTS Alert: {alert.alert_type.value.replace('_', ' ').title()}"

    def _generate_text_email(self, alert: Alert) -> str:
        """Generate plain text email body."""
        metadata_str = "\n".join(f"  - {k}: {v}" for k, v in alert.metadata.items())

        return f"""
TTS System Alert

Type: {alert.alert_type.value}
Severity: {alert.severity.value}
Time: {alert.sent_at.strftime('%Y-%m-%d %H:%M:%S UTC')}

Message:
{alert.message}

Details:
{metadata_str}

---
This alert will not be sent again for {self.cooldown_minutes} minutes.

KasaAI TTS Alert System
        """.strip()

    def _generate_html_email(self, alert: Alert) -> str:
        """Generate HTML email body."""
        severity_colors = {
            AlertSeverity.INFO: "#0066cc",
            AlertSeverity.WARNING: "#ff9900",
            AlertSeverity.ERROR: "#cc0000",
            AlertSeverity.CRITICAL: "#990000"
        }

        color = severity_colors.get(alert.severity, "#333333")

        metadata_rows = "".join(
            f"<tr><td style='padding: 5px; border-bottom: 1px solid #ddd;'><strong>{k}:</strong></td>"
            f"<td style='padding: 5px; border-bottom: 1px solid #ddd;'>{v}</td></tr>"
            for k, v in alert.metadata.items()
        )

        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9f9f9;">
        <div style="background-color: {color}; color: white; padding: 15px; border-radius: 5px 5px 0 0;">
            <h2 style="margin: 0;">TTS System Alert</h2>
        </div>

        <div style="background-color: white; padding: 20px; border-radius: 0 0 5px 5px;">
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                <tr>
                    <td style="padding: 5px; border-bottom: 1px solid #ddd;"><strong>Type:</strong></td>
                    <td style="padding: 5px; border-bottom: 1px solid #ddd;">{alert.alert_type.value.replace('_', ' ').title()}</td>
                </tr>
                <tr>
                    <td style="padding: 5px; border-bottom: 1px solid #ddd;"><strong>Severity:</strong></td>
                    <td style="padding: 5px; border-bottom: 1px solid #ddd;">{alert.severity.value.upper()}</td>
                </tr>
                <tr>
                    <td style="padding: 5px; border-bottom: 1px solid #ddd;"><strong>Time:</strong></td>
                    <td style="padding: 5px; border-bottom: 1px solid #ddd;">{alert.sent_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</td>
                </tr>
            </table>

            <div style="background-color: #f5f5f5; padding: 15px; border-left: 4px solid {color}; margin-bottom: 20px;">
                <p style="margin: 0;"><strong>Message:</strong></p>
                <p style="margin: 10px 0 0 0;">{alert.message}</p>
            </div>

            <h3 style="margin-top: 20px; margin-bottom: 10px;">Details</h3>
            <table style="width: 100%; border-collapse: collapse;">
                {metadata_rows}
            </table>

            <div style="margin-top: 30px; padding: 15px; background-color: #fff3cd; border-left: 4px solid #ffc107;">
                <p style="margin: 0; font-size: 14px;">
                    <strong>Note:</strong> This alert will not be sent again for {self.cooldown_minutes} minutes to prevent spam.
                </p>
            </div>
        </div>

        <div style="margin-top: 20px; text-align: center; font-size: 12px; color: #666;">
            <p>KasaAI TTS Alert System</p>
        </div>
    </div>
</body>
</html>
        """.strip()
