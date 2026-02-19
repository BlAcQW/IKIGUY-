"""
Alert Service for Cost Analytics

Sends automated alerts when profit margins drop below thresholds.
Supports email, Slack, and Discord notifications.

Features:
- Configurable thresholds
- Cooldown period to prevent spam
- Alert history tracking
- Multiple notification channels
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import httpx
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    CRITICAL = "critical"  # Negative margin
    HIGH = "high"  # <5% margin
    MEDIUM = "medium"  # 5-10% margin
    LOW = "low"  # 10-15% margin
    INFO = "info"  # Informational


class AlertChannel(str, Enum):
    """Alert delivery channels"""
    EMAIL = "email"
    SLACK = "slack"
    DISCORD = "discord"
    WEBHOOK = "webhook"


class AlertService:
    """
    Service for sending automated alerts based on profit margin thresholds.

    Prevents money loss by notifying admins when margins drop.
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize alert service.

        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.collection = db.alert_history
        self.config_collection = db.alert_configs

        # Default thresholds
        self.thresholds = {
            "critical": 0.0,  # Negative margin
            "high": 5.0,  # Less than 5%
            "medium": 10.0,  # Less than 10%
            "low": 15.0,  # Less than 15%
        }

        # Default cooldown: 24 hours per provider
        self.cooldown_hours = 24

    async def check_and_send_alerts(
        self,
        provider_data: List[Dict[str, Any]],
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check profit margins and send alerts if thresholds exceeded.

        Args:
            provider_data: List of provider breakdown data
            tenant_id: Optional organization ID filter

        Returns:
            Dict with alert summary
        """
        alerts_sent = []
        alerts_suppressed = []

        for provider in provider_data:
            margin = provider.get("profit_margin_percentage", 0)
            provider_name = provider.get("provider", "unknown")

            # Determine severity
            severity = self._get_severity(margin)

            if severity in [AlertSeverity.CRITICAL, AlertSeverity.HIGH]:
                # Check cooldown
                if await self._is_in_cooldown(provider_name, tenant_id):
                    alerts_suppressed.append({
                        "provider": provider_name,
                        "reason": "cooldown_period"
                    })
                    continue

                # Send alert
                try:
                    await self._send_alert(
                        provider=provider_name,
                        severity=severity,
                        margin=margin,
                        data=provider,
                        tenant_id=tenant_id
                    )

                    alerts_sent.append({
                        "provider": provider_name,
                        "severity": severity,
                        "margin": margin
                    })

                except Exception as e:
                    logger.error(f"Failed to send alert for {provider_name}: {e}")

        return {
            "alerts_sent": alerts_sent,
            "alerts_suppressed": alerts_suppressed,
            "total_sent": len(alerts_sent),
            "total_suppressed": len(alerts_suppressed)
        }

    def _get_severity(self, margin: float) -> AlertSeverity:
        """
        Determine alert severity based on margin.

        Args:
            margin: Profit margin percentage

        Returns:
            AlertSeverity level
        """
        if margin < self.thresholds["critical"]:
            return AlertSeverity.CRITICAL
        elif margin < self.thresholds["high"]:
            return AlertSeverity.HIGH
        elif margin < self.thresholds["medium"]:
            return AlertSeverity.MEDIUM
        elif margin < self.thresholds["low"]:
            return AlertSeverity.LOW
        else:
            return AlertSeverity.INFO

    async def _is_in_cooldown(
        self,
        provider: str,
        tenant_id: Optional[str] = None
    ) -> bool:
        """
        Check if alert for this provider is in cooldown period.

        Args:
            provider: Provider name
            tenant_id: Optional organization ID

        Returns:
            True if in cooldown, False otherwise
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=self.cooldown_hours)

        query = {
            "provider": provider,
            "sent_at": {"$gte": cutoff_time}
        }

        if tenant_id:
            query["tenant_id"] = tenant_id

        last_alert = await self.collection.find_one(query)
        return last_alert is not None

    async def _send_alert(
        self,
        provider: str,
        severity: AlertSeverity,
        margin: float,
        data: Dict[str, Any],
        tenant_id: Optional[str] = None
    ):
        """
        Send alert through all configured channels.

        Args:
            provider: Provider name
            severity: Alert severity
            margin: Profit margin percentage
            data: Full provider data
            tenant_id: Optional organization ID
        """
        # Get alert configuration
        config = await self._get_alert_config(tenant_id)

        # Build alert message
        message = self._build_alert_message(
            provider=provider,
            severity=severity,
            margin=margin,
            data=data
        )

        # Send through configured channels
        sent_channels = []

        if config.get("email_enabled", True):
            try:
                await self._send_email_alert(
                    config=config,
                    subject=message["subject"],
                    body=message["email_body"]
                )
                sent_channels.append(AlertChannel.EMAIL)
            except Exception as e:
                logger.error(f"Email alert failed: {e}")

        if config.get("slack_enabled", False):
            try:
                await self._send_slack_alert(
                    webhook_url=config.get("slack_webhook"),
                    message=message["slack_body"]
                )
                sent_channels.append(AlertChannel.SLACK)
            except Exception as e:
                logger.error(f"Slack alert failed: {e}")

        if config.get("discord_enabled", False):
            try:
                await self._send_discord_alert(
                    webhook_url=config.get("discord_webhook"),
                    message=message["discord_body"]
                )
                sent_channels.append(AlertChannel.DISCORD)
            except Exception as e:
                logger.error(f"Discord alert failed: {e}")

        # Save to history
        await self._save_alert_history(
            provider=provider,
            severity=severity,
            margin=margin,
            data=data,
            channels=sent_channels,
            tenant_id=tenant_id
        )

        logger.info(f"✅ Alert sent for {provider} via {sent_channels}")

    def _build_alert_message(
        self,
        provider: str,
        severity: AlertSeverity,
        margin: float,
        data: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Build alert message for different channels.

        Args:
            provider: Provider name
            severity: Alert severity
            margin: Profit margin percentage
            data: Full provider data

        Returns:
            Dict with messages for each channel
        """
        revenue = data.get("total_revenue", 0)
        costs = data.get("total_costs", 0)
        profit = data.get("total_profit", 0)
        transactions = data.get("transaction_count", 0)

        # Determine urgency
        urgency = "CRITICAL" if severity == AlertSeverity.CRITICAL else "HIGH PRIORITY"

        # Subject line
        subject = f"🚨 {urgency}: {provider} Profit Margin Alert"

        # Email body (HTML)
        email_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .alert {{ background-color: #FEE2E2; padding: 20px; border-left: 4px solid #EF4444; }}
                .critical {{ background-color: #FEE2E2; }}
                .high {{ background-color: #FED7AA; }}
                .metrics {{ background-color: #F3F4F6; padding: 15px; margin: 10px 0; }}
                .metric-row {{ display: flex; justify-content: space-between; margin: 5px 0; }}
                .recommendation {{ background-color: #DBEAFE; padding: 15px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="alert {severity}">
                <h2>🚨 {urgency}: Provider Losing Money</h2>
                <h3>Provider: {provider.upper()}</h3>
                <p><strong>Margin: {margin:.2f}%</strong> ({"LOSING MONEY" if margin < 0 else "VERY LOW MARGIN"})</p>
            </div>

            <div class="metrics">
                <h4>Financial Summary</h4>
                <div class="metric-row">
                    <span>Revenue:</span>
                    <span>₵{revenue:.2f}</span>
                </div>
                <div class="metric-row">
                    <span>Costs:</span>
                    <span>₵{costs:.2f}</span>
                </div>
                <div class="metric-row">
                    <span>Profit/Loss:</span>
                    <span style="color: {"#EF4444" if profit < 0 else "#10B981"}">₵{profit:.2f}</span>
                </div>
                <div class="metric-row">
                    <span>Transactions:</span>
                    <span>{transactions}</span>
                </div>
            </div>

            <div class="recommendation">
                <h4>💡 Recommended Actions</h4>
                <ul>
                    <li>Review pricing for {provider} services</li>
                    <li>Consider switching to a more cost-effective provider</li>
                    <li>Negotiate better rates with {provider}</li>
                    <li>Temporarily disable {provider} until pricing is fixed</li>
                </ul>
            </div>

            <p>View details: <a href="https://kasaai.ailabsafrica.com/admin/cost-analytics">Cost Analytics Dashboard</a></p>

            <hr>
            <p style="color: #6B7280; font-size: 12px;">
                This is an automated alert from KasaAI Cost Analytics System.<br>
                Generated at: {datetime.utcnow().isoformat()}Z
            </p>
        </body>
        </html>
        """

        # Slack body (Markdown with blocks)
        slack_body = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🚨 {urgency}: {provider} Alert"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Provider:*\n{provider.upper()}"},
                        {"type": "mrkdwn", "text": f"*Margin:*\n{margin:.2f}%"},
                        {"type": "mrkdwn", "text": f"*Revenue:*\n₵{revenue:.2f}"},
                        {"type": "mrkdwn", "text": f"*Costs:*\n₵{costs:.2f}"},
                        {"type": "mrkdwn", "text": f"*Profit:*\n₵{profit:.2f}"},
                        {"type": "mrkdwn", "text": f"*Transactions:*\n{transactions}"}
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*💡 Recommended Actions:*\n• Review pricing\n• Consider alternative provider\n• Negotiate better rates"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "View Dashboard"},
                            "url": "https://kasaai.ailabsafrica.com/admin/cost-analytics",
                            "style": "primary"
                        }
                    ]
                }
            ]
        }

        # Discord body (Rich embed)
        discord_body = {
            "embeds": [{
                "title": f"🚨 {urgency}: {provider} Alert",
                "color": 15158332 if severity == AlertSeverity.CRITICAL else 16744192,  # Red or Orange
                "fields": [
                    {"name": "Provider", "value": provider.upper(), "inline": True},
                    {"name": "Margin", "value": f"{margin:.2f}%", "inline": True},
                    {"name": "Revenue", "value": f"₵{revenue:.2f}", "inline": True},
                    {"name": "Costs", "value": f"₵{costs:.2f}", "inline": True},
                    {"name": "Profit/Loss", "value": f"₵{profit:.2f}", "inline": True},
                    {"name": "Transactions", "value": str(transactions), "inline": True},
                    {"name": "💡 Recommendation", "value": "Review pricing or switch provider", "inline": False}
                ],
                "footer": {
                    "text": "KasaAI Cost Analytics"
                },
                "timestamp": datetime.utcnow().isoformat()
            }]
        }

        return {
            "subject": subject,
            "email_body": email_body,
            "slack_body": slack_body,
            "discord_body": discord_body
        }

    async def _send_email_alert(
        self,
        config: Dict[str, Any],
        subject: str,
        body: str
    ):
        """
        Send email alert using SMTP.

        Args:
            config: Alert configuration with email settings
            subject: Email subject
            body: Email body (HTML)
        """
        # Get email configuration
        smtp_host = config.get("smtp_host", "smtp.gmail.com")
        smtp_port = config.get("smtp_port", 587)
        smtp_user = config.get("smtp_user")
        smtp_password = config.get("smtp_password")
        from_email = config.get("from_email", smtp_user)
        to_emails = config.get("alert_emails", [])

        if not to_emails or not smtp_user:
            logger.warning("Email alerts not configured properly")
            return

        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = from_email
        msg["To"] = ", ".join(to_emails)

        # Attach HTML body
        html_part = MIMEText(body, "html")
        msg.attach(html_part)

        # Send email
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)

        logger.info(f"✅ Email alert sent to {len(to_emails)} recipients")

    async def _send_slack_alert(
        self,
        webhook_url: str,
        message: Dict[str, Any]
    ):
        """
        Send Slack alert via webhook.

        Args:
            webhook_url: Slack webhook URL
            message: Slack message with blocks
        """
        if not webhook_url:
            logger.warning("Slack webhook not configured")
            return

        async with httpx.AsyncClient() as client:
            response = await client.post(webhook_url, json=message)
            response.raise_for_status()

        logger.info("✅ Slack alert sent")

    async def _send_discord_alert(
        self,
        webhook_url: str,
        message: Dict[str, Any]
    ):
        """
        Send Discord alert via webhook.

        Args:
            webhook_url: Discord webhook URL
            message: Discord message with embeds
        """
        if not webhook_url:
            logger.warning("Discord webhook not configured")
            return

        async with httpx.AsyncClient() as client:
            response = await client.post(webhook_url, json=message)
            response.raise_for_status()

        logger.info("✅ Discord alert sent")

    async def _save_alert_history(
        self,
        provider: str,
        severity: AlertSeverity,
        margin: float,
        data: Dict[str, Any],
        channels: List[AlertChannel],
        tenant_id: Optional[str] = None
    ):
        """
        Save alert to history for tracking.

        Args:
            provider: Provider name
            severity: Alert severity
            margin: Profit margin percentage
            data: Full provider data
            channels: Channels alert was sent to
            tenant_id: Optional organization ID
        """
        alert_record = {
            "provider": provider,
            "severity": severity,
            "margin": margin,
            "data": data,
            "channels": channels,
            "tenant_id": tenant_id,
            "sent_at": datetime.utcnow(),
            "acknowledged": False
        }

        await self.collection.insert_one(alert_record)
        logger.debug(f"Alert saved to history for {provider}")

    async def _get_alert_config(
        self,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get alert configuration for organization.

        Args:
            tenant_id: Optional organization ID

        Returns:
            Alert configuration dict
        """
        query = {"tenant_id": tenant_id} if tenant_id else {"tenant_id": None}
        config = await self.config_collection.find_one(query)

        if not config:
            # Return default configuration
            return {
                "email_enabled": True,
                "slack_enabled": False,
                "discord_enabled": False,
                "alert_emails": [],
                "cooldown_hours": 24
            }

        return config

    async def configure_alerts(
        self,
        tenant_id: Optional[str],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Configure alert settings for organization.

        Args:
            tenant_id: Optional organization ID
            config: Configuration to save

        Returns:
            Saved configuration
        """
        config["tenant_id"] = tenant_id
        config["updated_at"] = datetime.utcnow()

        await self.config_collection.update_one(
            {"tenant_id": tenant_id},
            {"$set": config},
            upsert=True
        )

        logger.info(f"Alert configuration updated for tenant {tenant_id}")
        return config

    async def get_alert_history(
        self,
        tenant_id: Optional[str] = None,
        provider: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get alert history.

        Args:
            tenant_id: Optional organization filter
            provider: Optional provider filter
            limit: Maximum number of records

        Returns:
            List of alert records
        """
        query = {}
        if tenant_id:
            query["tenant_id"] = tenant_id
        if provider:
            query["provider"] = provider

        cursor = self.collection.find(query).sort("sent_at", -1).limit(limit)
        alerts = await cursor.to_list(length=limit)

        # Convert ObjectId to string
        for alert in alerts:
            alert["_id"] = str(alert["_id"])

        return alerts
