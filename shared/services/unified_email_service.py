"""
Unified Email Service for KasaAI Platform

This service provides a centralized, easy-to-use interface for sending emails
across all KasaAI applications. It automatically configures itself from environment
variables and provides fallback mechanisms.

Usage:
    from shared.services.unified_email_service import get_email_service

    email_service = get_email_service()
    result = await email_service.send_email(
        to="recipient@example.com",
        subject="Test Email",
        body="Hello World",
        html_body="<h1>Hello World</h1>"
    )
"""

import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class UnifiedEmailService:
    """
    Unified email service that works across all KasaAI applications.

    Automatically configures itself from environment variables and provides
    multiple fallback mechanisms for reliable email delivery.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize unified email service.

        Args:
            config: Optional configuration dict. If not provided, uses environment variables.
        """
        self.config = config or self._load_config_from_env()
        self.logger = logging.getLogger("UnifiedEmailService")
        self._validate_config()

    def _load_config_from_env(self) -> Dict[str, Any]:
        """Load email configuration from environment variables."""
        return {
            # Primary SMTP configuration (iRedMail)
            "smtp_enabled": True,
            "smtp_host": os.getenv("SMTP_HOST", os.getenv("SMTP_SERVER", "mail.ailabsafrica.com")),
            "smtp_port": int(os.getenv("SMTP_PORT", "587")),
            "smtp_username": os.getenv("SMTP_USERNAME"),
            "smtp_password": os.getenv("SMTP_PASSWORD"),
            "smtp_use_tls": os.getenv("SMTP_USE_TLS", "true").lower() == "true",
            "smtp_timeout": int(os.getenv("SMTP_TIMEOUT", "30")),

            # Default sender information
            "from_email": os.getenv("SENDER_EMAIL", os.getenv("SMTP_FROM_EMAIL", "noreply@ailabsafrica.com")),
            "from_name": os.getenv("SENDER_NAME", "KasaAI Platform"),

            # Fallback configuration
            "resend_api_key": os.getenv("RESEND_API"),
            "sendgrid_api_key": os.getenv("SENDGRID_API_KEY"),

            # Email settings
            "default_recipient": os.getenv("DEFAULT_EMAIL_RECIPIENT", "ailabsafrica@gmail.com"),
            "enable_fallback": os.getenv("EMAIL_ENABLE_FALLBACK", "true").lower() == "true",
        }

    def _validate_config(self):
        """Validate email configuration."""
        if not self.config.get("smtp_host"):
            self.logger.warning("SMTP host not configured. Email sending may fail.")

        if not self.config.get("from_email"):
            self.logger.warning("From email not configured. Using default: noreply@ailabsafrica.com")
            self.config["from_email"] = "noreply@ailabsafrica.com"

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        reply_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send an email with automatic fallback mechanisms.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Plain text email body
            html_body: Optional HTML email body
            from_email: Optional sender email (overrides config)
            from_name: Optional sender name
            cc: Optional CC recipients
            bcc: Optional BCC recipients
            attachments: Optional list of attachments
            reply_to: Optional reply-to email address

        Returns:
            Dict with success status, message_id, and other details

        Example:
            result = await email_service.send_email(
                to="user@example.com",
                subject="Welcome!",
                body="Welcome to KasaAI",
                html_body="<h1>Welcome to KasaAI</h1>"
            )
        """
        try:
            # Try primary SMTP method
            if self.config.get("smtp_enabled"):
                result = await self._send_via_smtp(
                    to=to,
                    subject=subject,
                    body=body,
                    html_body=html_body,
                    from_email=from_email,
                    from_name=from_name,
                    cc=cc,
                    bcc=bcc,
                    attachments=attachments,
                    reply_to=reply_to
                )

                if result.get("success"):
                    self.logger.info(f"✅ Email sent successfully via SMTP to {to}")
                    return result
                else:
                    self.logger.warning(f"⚠️ SMTP sending failed: {result.get('error')}")

                    # Try fallback if enabled
                    if self.config.get("enable_fallback"):
                        self.logger.info("🔄 Attempting fallback email service...")
                        return await self._send_via_fallback(to, subject, body, html_body, from_email)

                    return result

            # If SMTP not enabled, try fallback directly
            if self.config.get("enable_fallback"):
                return await self._send_via_fallback(to, subject, body, html_body, from_email)

            return {
                "success": False,
                "error": "No email service configured",
                "provider": "none"
            }

        except Exception as e:
            self.logger.error(f"❌ Email sending error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "provider": "error"
            }

    async def _send_via_smtp(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        reply_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send email via SMTP."""
        try:
            # Get SMTP configuration
            smtp_host = self.config["smtp_host"]
            smtp_port = self.config["smtp_port"]
            smtp_username = self.config.get("smtp_username")
            smtp_password = self.config.get("smtp_password")
            use_tls = self.config.get("smtp_use_tls", True)
            timeout = self.config.get("smtp_timeout", 30)

            # Set sender email
            if not from_email:
                from_email = self.config["from_email"]

            if not from_name:
                from_name = self.config.get("from_name", "")

            # Format sender
            sender = f"{from_name} <{from_email}>" if from_name else from_email

            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = sender
            msg['To'] = to
            msg['Subject'] = subject

            # Add optional headers
            if cc:
                msg['Cc'] = ", ".join(cc)
            if reply_to:
                msg['Reply-To'] = reply_to

            # Generate message ID
            message_id = f"<{uuid.uuid4()}@{smtp_host}>"
            msg['Message-ID'] = message_id
            msg['Date'] = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000')

            # Add body content
            if body:
                msg.attach(MIMEText(body, 'plain', 'utf-8'))

            if html_body:
                msg.attach(MIMEText(html_body, 'html', 'utf-8'))
            elif not body:
                # If no body and no HTML, use a placeholder
                msg.attach(MIMEText("Email content not provided", 'plain', 'utf-8'))

            # Add attachments
            if attachments:
                for attachment in attachments:
                    part = MIMEBase('application', 'octet-stream')

                    content = attachment.get('content', b'')
                    if isinstance(content, str):
                        content = content.encode()

                    part.set_payload(content)
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {attachment.get("filename", "attachment")}'
                    )
                    msg.attach(part)

            # Collect all recipients
            all_recipients = [to]
            if cc:
                all_recipients.extend(cc)
            if bcc:
                all_recipients.extend(bcc)

            # For localhost, force 127.0.0.1 to ensure proper local binding
            is_localhost = smtp_host in ["localhost", "127.0.0.1"]
            actual_host = "127.0.0.1" if is_localhost else smtp_host

            # Connect and send
            self.logger.info(f"📤 Connecting to SMTP server: {actual_host}:{smtp_port}")
            server = smtplib.SMTP(actual_host, smtp_port, timeout=timeout)

            # Use STARTTLS if enabled (skip for localhost relay)
            if use_tls and not is_localhost:
                self.logger.info("🔐 Starting TLS encryption...")
                server.starttls()

            # Authenticate if credentials provided
            # Skip authentication for localhost (postfix relay doesn't support AUTH)
            if smtp_username and smtp_password and not is_localhost:
                self.logger.info(f"🔑 Authenticating as: {smtp_username}")
                server.login(smtp_username, smtp_password)
            else:
                self.logger.info("📧 Sending without authentication (local relay)")

            # Send email
            server.sendmail(from_email, all_recipients, msg.as_string())
            server.quit()

            self.logger.info(f"✅ SMTP email sent successfully - Message ID: {message_id}")

            return {
                "success": True,
                "message_id": message_id,
                "provider": "smtp",
                "smtp_host": smtp_host,
                "smtp_port": smtp_port,
                "recipients": all_recipients,
                "from_address": from_email,
                "subject": subject,
                "sent_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            self.logger.error(f"❌ SMTP sending failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "provider": "smtp"
            }

    async def _send_via_fallback(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        from_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send email via fallback service (Resend or SendGrid)."""
        try:
            # Try Resend first
            if self.config.get("resend_api_key"):
                import httpx

                self.logger.info("📤 Attempting to send via Resend API...")

                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        "https://api.resend.com/emails",
                        headers={
                            "Authorization": f"Bearer {self.config['resend_api_key']}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "from": from_email or self.config["from_email"],
                            "to": [to],
                            "subject": subject,
                            "html": html_body or f"<pre>{body}</pre>"
                        },
                        timeout=30
                    )

                    if response.status_code == 200:
                        result = response.json()
                        self.logger.info(f"✅ Email sent via Resend - ID: {result.get('id')}")
                        return {
                            "success": True,
                            "message_id": result.get('id'),
                            "provider": "resend",
                            "recipients": [to],
                            "sent_at": datetime.utcnow().isoformat()
                        }
                    else:
                        self.logger.error(f"❌ Resend API error: {response.status_code} - {response.text}")

            # SendGrid fallback (if Resend fails or not configured)
            if self.config.get("sendgrid_api_key"):
                self.logger.info("📤 Attempting to send via SendGrid...")
                # SendGrid implementation here if needed
                pass

            return {
                "success": False,
                "error": "All fallback methods failed or not configured",
                "provider": "fallback"
            }

        except Exception as e:
            self.logger.error(f"❌ Fallback sending failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "provider": "fallback"
            }

    async def send_template_email(
        self,
        to: str,
        template_name: str,
        template_variables: Dict[str, Any],
        from_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send an email using a template.

        Args:
            to: Recipient email
            template_name: Name of the template
            template_variables: Variables to inject into template
            from_email: Optional sender email

        Returns:
            Dict with success status and details
        """
        # Template rendering logic here
        # For now, just pass through to send_email
        subject = template_variables.get("subject", "Notification from KasaAI")
        body = template_variables.get("body", "")
        html_body = template_variables.get("html_body")

        return await self.send_email(
            to=to,
            subject=subject,
            body=body,
            html_body=html_body,
            from_email=from_email
        )


# Singleton instance
_email_service_instance: Optional[UnifiedEmailService] = None


def get_email_service() -> UnifiedEmailService:
    """
    Get the global email service instance.

    Returns:
        UnifiedEmailService: Configured email service

    Example:
        from shared.services.unified_email_service import get_email_service

        email_service = get_email_service()
        result = await email_service.send_email(
            to="user@example.com",
            subject="Test",
            body="Hello!"
        )
    """
    global _email_service_instance

    if _email_service_instance is None:
        _email_service_instance = UnifiedEmailService()

    return _email_service_instance


def reset_email_service():
    """Reset the email service instance (useful for testing)."""
    global _email_service_instance
    _email_service_instance = None


# Convenience function for quick email sending
async def send_email(
    to: str,
    subject: str,
    body: str,
    html_body: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Convenience function for sending emails without explicitly getting the service.

    Example:
        from shared.services.unified_email_service import send_email

        result = await send_email(
            to="user@example.com",
            subject="Test Email",
            body="Hello World"
        )
    """
    service = get_email_service()
    return await service.send_email(to, subject, body, html_body, **kwargs)
