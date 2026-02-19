"""
Low Credit Notifier Service

Monitors VAPI phone number credit balances and sends email notifications
when credit falls below configured thresholds.

Follows the same pattern as TTSHealthNotifier for consistency.

Usage:
    from apps.shared.services.low_credit_notifier import LowCreditNotifier

    notifier = LowCreditNotifier()
    await notifier.send_low_credit_alert(phone_data, recipient_email)
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

logger = logging.getLogger(__name__)


class LowCreditNotifier:
    """
    Service for sending email notifications about low VAPI phone credit.
    Uses the same email infrastructure as TTSHealthNotifier.
    """

    def __init__(
        self,
        default_recipient: str = "alfred.anyan@gmail.com",
        from_email: str = "noreply@ailabsafrica.com",
        smtp_host: str = "localhost",
        smtp_port: int = 25,
        smtp_username: Optional[str] = None,
        smtp_password: Optional[str] = None,
        use_tls: bool = False,
        enable_notifications: bool = True,
        cooldown_minutes: int = 60,
    ):
        """
        Initialize low credit notifier.

        Args:
            default_recipient: Default email address to receive notifications
            from_email: From email address
            smtp_host: SMTP server host
            smtp_port: SMTP server port
            smtp_username: SMTP username (optional)
            smtp_password: SMTP password (optional)
            use_tls: Use TLS for SMTP
            enable_notifications: Enable/disable email notifications
            cooldown_minutes: Minutes to wait before sending another alert for same phone
        """
        self.default_recipient = default_recipient
        self.from_email = from_email
        self.smtp_host = os.getenv("SMTP_SERVER", smtp_host)
        self.smtp_port = int(os.getenv("SMTP_PORT", str(smtp_port)))
        self.smtp_username = os.getenv("SMTP_USERNAME", smtp_username)
        self.smtp_password = os.getenv("SMTP_PASSWORD", smtp_password)
        self.use_tls = use_tls
        self.enable_notifications = enable_notifications
        self.cooldown_minutes = cooldown_minutes

        # Track last notification times to prevent spam
        self._last_notifications: Dict[str, datetime] = {}

        logger.info(
            f"LowCreditNotifier initialized (recipient: {default_recipient}, "
            f"notifications: {enable_notifications})"
        )

    def _should_send_notification(self, phone_id: str) -> bool:
        """
        Check if enough time has passed since last notification.

        Args:
            phone_id: Phone identifier

        Returns:
            True if notification should be sent
        """
        if phone_id not in self._last_notifications:
            return True

        last_time = self._last_notifications[phone_id]
        cooldown_delta = timedelta(minutes=self.cooldown_minutes)

        return datetime.now() - last_time >= cooldown_delta

    async def send_low_credit_alert(
        self,
        phone_number: str,
        phone_id: str,
        provider: str,
        current_balance: float,
        threshold: float,
        currency: str,
        cost_per_minute: float,
        recipient_email: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Send email alert when a phone's credit balance falls below threshold.

        Args:
            phone_number: Phone number string (e.g., +233240000000)
            phone_id: Phone ID in system
            provider: Provider name (e.g., vapi, twilio)
            current_balance: Current credit balance
            threshold: Low balance threshold
            currency: Currency code (e.g., GHC, USD)
            cost_per_minute: Cost per minute for calls
            recipient_email: Email to send alert to (uses default if not specified)
            metadata: Additional metadata to include

        Returns:
            True if email was sent successfully
        """
        if not self.enable_notifications:
            logger.debug("Notifications disabled, skipping low credit alert")
            return False

        # Check cooldown period
        if not self._should_send_notification(phone_id):
            logger.debug(f"Skipping notification for {phone_id} (in cooldown)")
            return False

        recipient = recipient_email or self.default_recipient
        remaining_minutes = current_balance / cost_per_minute if cost_per_minute > 0 else 0

        subject = f"🚨 Low Credit Alert: {phone_number}"

        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; }}
                .alert-box {{
                    background-color: #fee2e2;
                    border: 2px solid #dc2626;
                    border-radius: 8px;
                    padding: 20px;
                    margin-bottom: 20px;
                }}
                .alert-header {{
                    color: #dc2626;
                    margin-top: 0;
                    display: flex;
                    align-items: center;
                }}
                .info-box {{
                    background-color: #f9fafb;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 15px 0;
                }}
                .info-table {{
                    width: 100%;
                    border-collapse: collapse;
                }}
                .info-table td {{
                    padding: 12px 0;
                    border-bottom: 1px solid #e5e7eb;
                }}
                .info-table tr:last-child td {{
                    border-bottom: none;
                }}
                .balance-critical {{
                    color: #dc2626;
                    font-weight: bold;
                    font-size: 18px;
                }}
                .action-box {{
                    background-color: #fef3c7;
                    border-left: 4px solid #f59e0b;
                    padding: 15px;
                    border-radius: 4px;
                    margin: 20px 0;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #e5e7eb;
                    color: #6b7280;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="alert-box">
                <h2 class="alert-header">⚠️ Low Credit Balance Alert</h2>
                <p style="font-size: 16px; color: #374151;">
                    The VAPI phone number <strong>{phone_number}</strong> has fallen
                    below the low balance threshold and requires immediate attention.
                </p>
            </div>

            <div class="info-box">
                <h3 style="margin-top: 0; color: #374151;">📊 Current Status</h3>
                <table class="info-table">
                    <tr>
                        <td><strong>Phone Number:</strong></td>
                        <td>{phone_number}</td>
                    </tr>
                    <tr>
                        <td><strong>Provider:</strong></td>
                        <td>{provider.upper()}</td>
                    </tr>
                    <tr>
                        <td><strong>Current Balance:</strong></td>
                        <td class="balance-critical">{currency} {current_balance:.2f}</td>
                    </tr>
                    <tr>
                        <td><strong>Alert Threshold:</strong></td>
                        <td>{currency} {threshold:.2f}</td>
                    </tr>
                    <tr>
                        <td><strong>Remaining Minutes:</strong></td>
                        <td>{remaining_minutes:.1f} minutes</td>
                    </tr>
                    <tr>
                        <td><strong>Rate:</strong></td>
                        <td>{currency} {cost_per_minute:.2f}/min</td>
                    </tr>
                </table>
            </div>

            <div class="action-box">
                <p style="margin: 0; color: #92400e;">
                    <strong>⚡ Action Required:</strong> Please add credit to this phone number
                    to avoid service interruption. You can add credit via the
                    <strong>Cost Monitoring</strong> tab in the Phone Numbers page.
                </p>
            </div>

            <h3 style="color: #374151;">🔧 Impact if Not Addressed</h3>
            <ul style="color: #4b5563;">
                <li>Outbound calls from this number may fail</li>
                <li>Automated campaigns using this number will be paused</li>
                <li>Voice agents assigned to this number may become unavailable</li>
            </ul>

            <div class="footer">
                <p>This is an automated alert from the KasaAI VAPI Cost Monitoring System.</p>
                <p><strong>Timestamp:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                <p>Next alert for this number: After {self.cooldown_minutes} minutes if balance remains low</p>
            </div>
        </body>
        </html>
        """

        plain_body = f"""
Low Credit Balance Alert - VAPI Phone Number

Phone Number: {phone_number}
Provider: {provider.upper()}
Current Balance: {currency} {current_balance:.2f}
Alert Threshold: {currency} {threshold:.2f}
Remaining Minutes: {remaining_minutes:.1f} minutes
Rate: {currency} {cost_per_minute:.2f}/min

ACTION REQUIRED: Please add credit to this phone number to avoid service interruption.
You can add credit via the Cost Monitoring tab in the Phone Numbers page.

Impact if not addressed:
- Outbound calls from this number may fail
- Automated campaigns using this number will be paused
- Voice agents assigned to this number may become unavailable

Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
        """

        try:
            success = await self._send_email(
                to=recipient,
                subject=subject,
                plain_body=plain_body,
                html_body=html_body
            )

            if success:
                self._last_notifications[phone_id] = datetime.now()
                logger.info(
                    f"Low credit alert sent for {phone_number} to {recipient}: "
                    f"Balance {current_balance:.2f} {currency}"
                )
            return success

        except Exception as e:
            logger.error(f"Failed to send low credit alert for {phone_number}: {e}")
            return False

    async def send_credit_restored_alert(
        self,
        phone_number: str,
        phone_id: str,
        new_balance: float,
        added_amount: float,
        currency: str,
        recipient_email: Optional[str] = None,
    ) -> bool:
        """
        Send notification when credit is added and balance is restored above threshold.

        Args:
            phone_number: Phone number string
            phone_id: Phone ID in system
            new_balance: New credit balance after addition
            added_amount: Amount that was added
            currency: Currency code
            recipient_email: Email to send alert to

        Returns:
            True if email was sent successfully
        """
        if not self.enable_notifications:
            return False

        recipient = recipient_email or self.default_recipient

        subject = f"✅ Credit Restored: {phone_number}"

        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; }}
                .success-box {{
                    background-color: #dcfce7;
                    border: 2px solid #16a34a;
                    border-radius: 8px;
                    padding: 20px;
                    margin-bottom: 20px;
                }}
                .success-header {{
                    color: #16a34a;
                    margin-top: 0;
                }}
                .info-box {{
                    background-color: #f9fafb;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 15px 0;
                }}
                .balance-healthy {{
                    color: #16a34a;
                    font-weight: bold;
                    font-size: 18px;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #e5e7eb;
                    color: #6b7280;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="success-box">
                <h2 class="success-header">✅ Credit Balance Restored</h2>
                <p style="font-size: 16px; color: #374151;">
                    Credit has been added to <strong>{phone_number}</strong>.
                    The phone is now fully operational.
                </p>
            </div>

            <div class="info-box">
                <h3 style="margin-top: 0; color: #374151;">📊 Transaction Details</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 12px 0; border-bottom: 1px solid #e5e7eb;">
                            <strong>Phone Number:</strong>
                        </td>
                        <td style="padding: 12px 0; border-bottom: 1px solid #e5e7eb;">
                            {phone_number}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 12px 0; border-bottom: 1px solid #e5e7eb;">
                            <strong>Credit Added:</strong>
                        </td>
                        <td style="padding: 12px 0; border-bottom: 1px solid #e5e7eb; color: #16a34a; font-weight: bold;">
                            +{currency} {added_amount:.2f}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 12px 0;">
                            <strong>New Balance:</strong>
                        </td>
                        <td style="padding: 12px 0;" class="balance-healthy">
                            {currency} {new_balance:.2f}
                        </td>
                    </tr>
                </table>
            </div>

            <h3 style="color: #374151;">✅ Service Status</h3>
            <ul style="color: #4b5563;">
                <li>Phone number is fully operational</li>
                <li>Outbound calls are enabled</li>
                <li>Campaigns using this number can continue</li>
            </ul>

            <div class="footer">
                <p>This is an automated notification from the KasaAI VAPI Cost Monitoring System.</p>
                <p><strong>Timestamp:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            </div>
        </body>
        </html>
        """

        plain_body = f"""
Credit Balance Restored - VAPI Phone Number

Phone Number: {phone_number}
Credit Added: +{currency} {added_amount:.2f}
New Balance: {currency} {new_balance:.2f}

Service Status:
- Phone number is fully operational
- Outbound calls are enabled
- Campaigns using this number can continue

Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
        """

        try:
            success = await self._send_email(
                to=recipient,
                subject=subject,
                plain_body=plain_body,
                html_body=html_body
            )

            if success:
                # Clear the cooldown when credit is restored
                if phone_id in self._last_notifications:
                    del self._last_notifications[phone_id]
                logger.info(f"Credit restored alert sent for {phone_number} to {recipient}")

            return success

        except Exception as e:
            logger.error(f"Failed to send credit restored alert for {phone_number}: {e}")
            return False

    async def _send_email(
        self,
        to: str,
        subject: str,
        plain_body: str,
        html_body: str
    ) -> bool:
        """
        Send an email using unified email service with fallback mechanisms.

        Args:
            to: Recipient email address
            subject: Email subject
            plain_body: Plain text body
            html_body: HTML body

        Returns:
            True if email was sent successfully
        """
        # Try Method 1: Unified Email Service (Primary - Most Reliable)
        try:
            from .unified_email_service import get_email_service

            email_service = get_email_service()
            result = await email_service.send_email(
                to=to,
                subject=subject,
                body=plain_body,
                html_body=html_body,
                from_email=self.from_email
            )

            if result.get("success"):
                logger.info(f"✅ Low credit alert sent via unified service to {to}")
                return True
            else:
                logger.warning(f"⚠️ Unified email service failed: {result.get('error')}, trying fallback...")

        except Exception as e:
            logger.warning(f"⚠️ Unified email service error: {e}, trying fallback...")

        # Try Method 2: Direct SMTP (Fallback)
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to

            msg.attach(MIMEText(plain_body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))

            await asyncio.get_event_loop().run_in_executor(
                None,
                self._send_smtp_email,
                to,
                msg.as_string()
            )
            logger.info(f"✅ Low credit alert sent via direct SMTP to {to}")
            return True

        except Exception as e:
            logger.error(f"❌ Direct SMTP failed: {e}")
            return False

    def _send_smtp_email(self, to: str, message: str) -> None:
        """
        Send email via SMTP (synchronous).

        Args:
            to: Recipient email address
            message: Email message as string
        """
        try:
            is_localhost = self.smtp_host in ["localhost", "127.0.0.1"]
            smtp_host = "127.0.0.1" if is_localhost else self.smtp_host
            smtp_port = 25 if is_localhost else self.smtp_port

            with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
                if self.use_tls and not is_localhost:
                    server.starttls()
                if self.smtp_username and self.smtp_password and not is_localhost:
                    server.login(self.smtp_username, self.smtp_password)
                server.sendmail(self.from_email, [to], message)

        except Exception as e:
            logger.error(f"SMTP send failed: {e}")
            raise

    async def send_test_notification(self, recipient_email: Optional[str] = None) -> bool:
        """
        Send a test notification to verify email configuration.

        Args:
            recipient_email: Email to send test to (uses default if not specified)

        Returns:
            True if email was sent successfully
        """
        recipient = recipient_email or self.default_recipient

        subject = "🧪 Low Credit Alert Test Notification"

        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; }}
                .test-box {{
                    background-color: #dbeafe;
                    border: 2px solid #3b82f6;
                    border-radius: 8px;
                    padding: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="test-box">
                <h2 style="color: #1d4ed8; margin-top: 0;">🧪 Low Credit Alert Test</h2>
                <p>This is a test notification to confirm that the low credit alert
                email system is configured correctly.</p>

                <h3>Configuration:</h3>
                <ul>
                    <li><strong>Recipient:</strong> {recipient}</li>
                    <li><strong>From:</strong> {self.from_email}</li>
                    <li><strong>SMTP Host:</strong> {self.smtp_host}:{self.smtp_port}</li>
                    <li><strong>Notifications Enabled:</strong> {self.enable_notifications}</li>
                    <li><strong>Cooldown Period:</strong> {self.cooldown_minutes} minutes</li>
                </ul>

                <p><strong>Test Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                <p>If you received this email, the notification system is working correctly!</p>
            </div>
        </body>
        </html>
        """

        plain_body = f"""
Low Credit Alert Test Notification

This is a test notification to confirm that the low credit alert
email system is configured correctly.

Configuration:
- Recipient: {recipient}
- From: {self.from_email}
- SMTP Host: {self.smtp_host}:{self.smtp_port}
- Notifications Enabled: {self.enable_notifications}
- Cooldown Period: {self.cooldown_minutes} minutes

Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

If you received this email, the notification system is working correctly!
        """

        try:
            success = await self._send_email(
                to=recipient,
                subject=subject,
                plain_body=plain_body,
                html_body=html_body
            )

            if success:
                logger.info(f"Test notification sent to {recipient}")
            return success

        except Exception as e:
            logger.error(f"Failed to send test notification: {e}")
            return False


# Singleton instance
_low_credit_notifier_instance: Optional[LowCreditNotifier] = None


def get_low_credit_notifier() -> LowCreditNotifier:
    """
    Get the global low credit notifier instance.

    Returns:
        LowCreditNotifier: Configured notifier instance

    Example:
        from shared.services.low_credit_notifier import get_low_credit_notifier

        notifier = get_low_credit_notifier()
        await notifier.send_low_credit_alert(
            phone_number="+233240000000",
            phone_id="vapi_123",
            provider="vapi",
            current_balance=50.0,
            threshold=100.0,
            currency="GHC",
            cost_per_minute=0.15,
            recipient_email="admin@example.com"
        )
    """
    global _low_credit_notifier_instance

    if _low_credit_notifier_instance is None:
        _low_credit_notifier_instance = LowCreditNotifier()

    return _low_credit_notifier_instance


def reset_low_credit_notifier():
    """Reset the notifier instance (useful for testing)."""
    global _low_credit_notifier_instance
    _low_credit_notifier_instance = None


# Example usage
if __name__ == "__main__":
    async def test_notifier():
        """Test the low credit notifier."""
        notifier = LowCreditNotifier(
            default_recipient="admin@ailabsafrica.com",
            enable_notifications=True
        )

        # Send test notification
        await notifier.send_test_notification()
        print(f"Test notification sent to {notifier.default_recipient}")

    asyncio.run(test_notifier())
