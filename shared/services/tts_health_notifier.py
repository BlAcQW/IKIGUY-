"""
TTS Health Notifier Service

Monitors TTS provider health and sends email notifications when services go down or recover.
Integrates with HealthMonitorService to receive real-time alerts.
Automatically restarts Docker containers for down providers.

Usage:
    from apps.shared.services.tts_health_notifier import TTSHealthNotifier

    notifier = TTSHealthNotifier()
    await notifier.initialize(health_monitor)
"""

import logging
import asyncio
import subprocess
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

# Mapping of provider IDs to Docker container names
PROVIDER_DOCKER_MAPPING = {
    "coqui_xtts": "coqui",
    "melotts": "68d4522d4834_melotts",  # or use docker-compose service name
    "openvoice": "openvoice",
    "kokoro": "kokoro",
    "chatterbox": "chatterbox",
    "moshi": "moshi",
    # Add more mappings as needed
}


class TTSHealthNotifier:
    """
    Service for sending email notifications about TTS provider health issues.
    """

    def __init__(
        self,
        admin_email: str = "admin@ailabsafrica.com",
        from_email: str = "noreply@ailabsafrica.com",
        smtp_host: str = "localhost",
        smtp_port: int = 587,
        smtp_username: Optional[str] = None,
        smtp_password: Optional[str] = None,
        use_tls: bool = True,
        enable_notifications: bool = True,
        cooldown_minutes: int = 30,  # Prevent spam by limiting notifications
    ):
        """
        Initialize TTS health notifier.

        Args:
            admin_email: Admin email address to receive notifications
            from_email: From email address
            smtp_host: SMTP server host
            smtp_port: SMTP server port
            smtp_username: SMTP username (optional)
            smtp_password: SMTP password (optional)
            use_tls: Use TLS for SMTP
            enable_notifications: Enable/disable email notifications
            cooldown_minutes: Minutes to wait before sending another alert for same provider
        """
        self.admin_email = admin_email
        self.from_email = from_email
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.use_tls = use_tls
        self.enable_notifications = enable_notifications
        self.cooldown_minutes = cooldown_minutes

        # Track last notification times to prevent spam
        self._last_notifications: Dict[str, datetime] = {}

        logger.info(
            f"TTSHealthNotifier initialized (admin: {admin_email}, "
            f"notifications: {enable_notifications})"
        )

    async def initialize(self, health_monitor) -> None:
        """
        Initialize notifier with health monitor.

        Args:
            health_monitor: HealthMonitorService instance
        """
        # Register callback with health monitor
        health_monitor.register_alert_callback(self.on_health_alert)
        logger.info("Registered health alert callback with monitor")

    async def on_health_alert(self, provider: Any, result: Any) -> None:
        """
        Callback for health monitor alerts.

        Args:
            provider: AIProvider instance
            result: HealthCheckResult instance
        """
        if not self.enable_notifications:
            return

        try:
            # Check cooldown period
            if not self._should_send_notification(provider.id):
                logger.debug(f"Skipping notification for {provider.id} (in cooldown)")
                return

            # Determine alert type
            is_down = not result.healthy

            if is_down:
                # Try to restart Docker container first
                restart_result = await self.restart_docker_container(provider.id)

                # Send alert with restart status
                await self.send_provider_down_alert(provider, result, restart_result)
            else:
                # Check if this is a recovery (was previously down)
                if provider.id in self._last_notifications:
                    await self.send_provider_recovered_alert(provider, result)

        except Exception as e:
            logger.error(f"Failed to send health notification: {e}")

    def _should_send_notification(self, provider_id: str) -> bool:
        """
        Check if enough time has passed since last notification.

        Args:
            provider_id: Provider identifier

        Returns:
            True if notification should be sent
        """
        if provider_id not in self._last_notifications:
            return True

        last_time = self._last_notifications[provider_id]
        cooldown_delta = timedelta(minutes=self.cooldown_minutes)

        return datetime.now() - last_time >= cooldown_delta

    def _format_restart_result_html(self, restart_result: Optional[Dict[str, Any]]) -> str:
        """Format restart result as HTML for email."""
        if not restart_result:
            return '<div style="color: #666;">No restart attempted</div>'

        if not restart_result.get("attempted"):
            return f'''
            <div style="background: #f5f5f5; padding: 10px; border-radius: 5px;">
                <strong>⏭️ Skipped:</strong> {restart_result.get("reason", "Unknown reason")}
            </div>
            '''

        if restart_result.get("success"):
            return f'''
            <div style="background: #e8f5e9; padding: 10px; border-radius: 5px; border-left: 4px solid #4caf50;">
                <strong>✅ Container Restarted Successfully</strong><br>
                Container: <code>{restart_result.get("container")}</code><br>
                The service should be back online shortly.
            </div>
            '''
        else:
            return f'''
            <div style="background: #ffebee; padding: 10px; border-radius: 5px; border-left: 4px solid #f44336;">
                <strong>❌ Restart Failed</strong><br>
                Container: <code>{restart_result.get("container", "unknown")}</code><br>
                Error: {restart_result.get("error", "Unknown error")}<br>
                <em>Manual intervention required.</em>
            </div>
            '''

    async def restart_docker_container(self, provider_id: str) -> Dict[str, Any]:
        """
        Attempt to restart Docker container for a provider.

        Args:
            provider_id: Provider identifier

        Returns:
            Dict with restart status and details
        """
        container_name = PROVIDER_DOCKER_MAPPING.get(provider_id)

        if not container_name:
            logger.info(f"No Docker mapping for provider {provider_id}, skipping restart")
            return {
                "attempted": False,
                "reason": "No Docker container mapping found",
                "provider_id": provider_id
            }

        try:
            logger.info(f"Attempting to restart Docker container '{container_name}' for provider {provider_id}")

            # Run docker restart command
            process = await asyncio.create_subprocess_exec(
                "docker", "restart", container_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=120)

            if process.returncode == 0:
                logger.info(f"Successfully restarted Docker container '{container_name}'")
                return {
                    "attempted": True,
                    "success": True,
                    "container": container_name,
                    "message": f"Container '{container_name}' restarted successfully"
                }
            else:
                error_msg = stderr.decode().strip() if stderr else "Unknown error"
                logger.error(f"Failed to restart container '{container_name}': {error_msg}")
                return {
                    "attempted": True,
                    "success": False,
                    "container": container_name,
                    "error": error_msg
                }

        except asyncio.TimeoutError:
            logger.error(f"Timeout restarting container '{container_name}'")
            return {
                "attempted": True,
                "success": False,
                "container": container_name,
                "error": "Restart timed out after 120 seconds"
            }
        except Exception as e:
            logger.error(f"Error restarting container '{container_name}': {e}")
            return {
                "attempted": True,
                "success": False,
                "container": container_name,
                "error": str(e)
            }

    async def send_provider_down_alert(
        self,
        provider: Any,
        result: Any,
        restart_result: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Send email alert when a provider goes down.

        Args:
            provider: Provider that went down
            result: Health check result
            restart_result: Result of Docker restart attempt
        """
        # Determine subject based on restart result
        if restart_result and restart_result.get("success"):
            subject = f"🟡 TTS Alert: {provider.name} was DOWN - Container Restarted"
        else:
            subject = f"🔴 TTS Alert: {provider.name} is DOWN"

        body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .alert-box {{
                    background-color: #ffebee;
                    border: 2px solid #f44336;
                    padding: 20px;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .provider-info {{
                    background-color: #f5f5f5;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 10px 0;
                }}
                .timestamp {{ color: #666; font-size: 14px; }}
                h2 {{ color: #d32f2f; }}
                .error-msg {{
                    background-color: #fff3cd;
                    padding: 10px;
                    border-left: 4px solid #ffc107;
                    margin: 10px 0;
                }}
            </style>
        </head>
        <body>
            <div class="alert-box">
                <h2>⚠️ TTS Provider Health Alert</h2>

                <div class="provider-info">
                    <strong>Provider:</strong> {provider.name} ({provider.id})<br>
                    <strong>Endpoint:</strong> {provider.endpoint}<br>
                    <strong>Status:</strong> <span style="color: red;">OFFLINE/DEGRADED</span><br>
                    <strong>Time:</strong> {result.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}<br>
                </div>

                {f'<div class="error-msg"><strong>Error:</strong> {result.error}</div>' if result.error else ''}

                <h3>Service Impact:</h3>
                <ul>
                    <li>Text-to-Speech synthesis using {provider.name} will fail</li>
                    <li>Users will be automatically redirected to alternative providers</li>
                    <li>Voice cloning features may be affected if this was a primary provider</li>
                </ul>

                <h3>🔄 Auto-Restart Status:</h3>
                {self._format_restart_result_html(restart_result)}

                <h3>Recommended Actions:</h3>
                <ol>
                    <li>Check the service logs for {provider.id}</li>
                    <li>Verify the endpoint is accessible: {provider.endpoint}/health</li>
                    <li>Check GPU memory and resources if this is a GPU-based service</li>
                    <li>Restart the service manually if auto-restart failed</li>
                </ol>

                <p class="timestamp">
                    <em>This notification was sent because the health check for {provider.name} failed.
                    Health checks run every 2 hours. You'll receive a recovery notification when the service comes back online.</em>
                </p>
            </div>

            <p style="color: #999; font-size: 12px;">
                KasaAI TTS Health Monitor |
                Next check: 2 hours
            </p>
        </body>
        </html>
        """

        await self._send_email(subject, body, is_html=True)
        self._last_notifications[provider.id] = datetime.now()
        logger.warning(f"Sent provider down alert for {provider.name} to {self.admin_email}")

    async def send_provider_recovered_alert(self, provider: Any, result: Any) -> None:
        """
        Send email alert when a provider recovers.

        Args:
            provider: Provider that recovered
            result: Health check result
        """
        subject = f"✅ TTS Recovery: {provider.name} is ONLINE"

        # Calculate downtime
        if provider.id in self._last_notifications:
            downtime = datetime.now() - self._last_notifications[provider.id]
            downtime_str = f"{downtime.total_seconds() / 60:.1f} minutes"
        else:
            downtime_str = "Unknown"

        body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .success-box {{
                    background-color: #e8f5e9;
                    border: 2px solid #4caf50;
                    padding: 20px;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .provider-info {{
                    background-color: #f5f5f5;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 10px 0;
                }}
                .timestamp {{ color: #666; font-size: 14px; }}
                h2 {{ color: #2e7d32; }}
                .metrics {{
                    background-color: #e3f2fd;
                    padding: 10px;
                    border-left: 4px solid #2196f3;
                    margin: 10px 0;
                }}
            </style>
        </head>
        <body>
            <div class="success-box">
                <h2>✅ TTS Provider Recovered</h2>

                <div class="provider-info">
                    <strong>Provider:</strong> {provider.name} ({provider.id})<br>
                    <strong>Endpoint:</strong> {provider.endpoint}<br>
                    <strong>Status:</strong> <span style="color: green;">ONLINE</span><br>
                    <strong>Recovery Time:</strong> {result.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}<br>
                    <strong>Downtime:</strong> {downtime_str}<br>
                </div>

                <div class="metrics">
                    <strong>Response Time:</strong> {result.response_time_ms:.2f}ms<br>
                    <strong>Health Check:</strong> Passed ✓
                </div>

                <h3>Service Status:</h3>
                <ul>
                    <li>✅ Service is now fully operational</li>
                    <li>✅ All TTS features using {provider.name} are available</li>
                    <li>✅ Normal performance metrics observed</li>
                </ul>

                <p class="timestamp">
                    <em>This recovery notification confirms that {provider.name} has passed health checks
                    and is ready to process requests.</em>
                </p>
            </div>

            <p style="color: #999; font-size: 12px;">
                KasaAI TTS Health Monitor |
                Service monitoring continues every 60 seconds
            </p>
        </body>
        </html>
        """

        await self._send_email(subject, body, is_html=True)
        # Remove from last notifications on recovery
        if provider.id in self._last_notifications:
            del self._last_notifications[provider.id]
        logger.info(f"Sent provider recovery alert for {provider.name} to {self.admin_email}")

    async def _send_email(self, subject: str, body: str, is_html: bool = True) -> None:
        """
        Send an email using unified email service with fallback mechanisms.

        Args:
            subject: Email subject
            body: Email body
            is_html: Whether body is HTML
        """
        # Try Method 1: Unified Email Service (Primary - Most Reliable)
        try:
            from .unified_email_service import get_email_service

            email_service = get_email_service()
            result = await email_service.send_email(
                to=self.admin_email,
                subject=subject,
                body=body if not is_html else "",
                html_body=body if is_html else None,
                from_email=self.from_email
            )

            if result.get("success"):
                logger.info(f"✅ TTS alert email sent via unified service to {self.admin_email}")
                return  # Success - exit early
            else:
                logger.warning(f"⚠️ Unified email service failed: {result.get('error')}, trying fallback...")

        except Exception as e:
            logger.warning(f"⚠️ Unified email service error: {e}, trying fallback...")

        # Try Method 2: Direct SMTP (Fallback - Known Working)
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = self.admin_email

            # Add body
            if is_html:
                part = MIMEText(body, 'html')
            else:
                part = MIMEText(body, 'plain')
            msg.attach(part)

            # Send via SMTP
            await asyncio.get_event_loop().run_in_executor(
                None,
                self._send_smtp_email,
                msg.as_string()
            )
            logger.info(f"✅ TTS alert email sent via direct SMTP to {self.admin_email}")
            return  # Success - exit early

        except Exception as e:
            logger.error(f"❌ Direct SMTP failed: {e}, trying final fallback...")
            # Try using the existing email service as final fallback
            await self._send_via_email_service(subject, body, is_html)

    def _send_smtp_email(self, message: str) -> None:
        """
        Send email via SMTP (synchronous).

        Args:
            message: Email message as string
        """
        try:
            # For localhost, force 127.0.0.1 and port 25 (postfix relay)
            is_localhost = self.smtp_host in ["localhost", "127.0.0.1"]
            smtp_host = "127.0.0.1" if is_localhost else self.smtp_host
            smtp_port = 25 if is_localhost else self.smtp_port

            with smtplib.SMTP(smtp_host, smtp_port) as server:
                # Skip TLS and auth for localhost (postfix relay)
                if self.use_tls and not is_localhost:
                    server.starttls()
                if self.smtp_username and self.smtp_password and not is_localhost:
                    server.login(self.smtp_username, self.smtp_password)
                server.sendmail(self.from_email, [self.admin_email], message)
        except Exception as e:
            logger.error(f"SMTP send failed: {e}")
            raise

    async def _send_via_email_service(self, subject: str, body: str, is_html: bool) -> None:
        """
        Final fallback: Force unified email service to try all its fallback methods.

        This method is called as a last resort when both primary unified service
        and direct SMTP have failed. It forces the unified service to try its
        fallback providers (Resend, SendGrid).

        Args:
            subject: Email subject
            body: Email body
            is_html: Whether body is HTML
        """
        try:
            from .unified_email_service import UnifiedEmailService

            # Create a new instance with fallback enabled
            email_service = UnifiedEmailService(config={
                "smtp_enabled": False,  # Skip SMTP since it already failed
                "enable_fallback": True,
                "resend_api_key": None,  # Will be loaded from env if available
                "from_email": self.from_email
            })

            result = await email_service.send_email(
                to=self.admin_email,
                subject=subject,
                body=body if not is_html else "",
                html_body=body if is_html else None,
                from_email=self.from_email
            )

            if result.get("success"):
                logger.info(f"✅ TTS alert email sent via final fallback to {self.admin_email}")
            else:
                logger.error(f"❌ All email sending methods failed: {result.get('error')}")

        except Exception as e:
            logger.error(f"❌ Final fallback email service failed: {e}")
            logger.error(f"💀 CRITICAL: Unable to send TTS alert email for subject: {subject}")

    async def send_test_notification(self) -> None:
        """
        Send a test notification to verify email configuration.
        """
        subject = "🧪 TTS Health Monitor Test Notification"

        body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .info-box {{
                    background-color: #e1f5fe;
                    border: 2px solid #03a9f4;
                    padding: 20px;
                    border-radius: 5px;
                }}
            </style>
        </head>
        <body>
            <div class="info-box">
                <h2>TTS Health Monitor Test</h2>
                <p>This is a test notification to confirm that the TTS health monitoring
                email system is configured correctly.</p>

                <p><strong>Configuration:</strong></p>
                <ul>
                    <li>Admin Email: {self.admin_email}</li>
                    <li>From Email: {self.from_email}</li>
                    <li>SMTP Host: {self.smtp_host}:{self.smtp_port}</li>
                    <li>Notifications Enabled: {self.enable_notifications}</li>
                    <li>Cooldown Period: {self.cooldown_minutes} minutes</li>
                </ul>

                <p><strong>Test Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>

                <p>If you received this email, the notification system is working correctly!</p>
            </div>
        </body>
        </html>
        """

        await self._send_email(subject, body, is_html=True)
        logger.info(f"Sent test notification to {self.admin_email}")


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    async def test_notifier():
        """Test the TTS health notifier."""

        # Create notifier
        notifier = TTSHealthNotifier(
            admin_email="admin@ailabsafrica.com",
            enable_notifications=True
        )

        # Send test notification
        await notifier.send_test_notification()
        print(f"Test notification sent to {notifier.admin_email}")

    asyncio.run(test_notifier())