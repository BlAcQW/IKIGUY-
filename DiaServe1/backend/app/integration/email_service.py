"""
Email Service (Stub) for EstateFlow.

Provides a local email sending stub. Uses SMTP for actual delivery
when configured, otherwise logs emails to console.
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, Any, Optional, List
import os

logger = logging.getLogger(__name__)


class EmailService:
    """
    Local email service.

    Sends emails via SMTP when configured, otherwise logs to console.
    """

    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "localhost")
        self.smtp_port = int(os.getenv("SMTP_PORT", "25"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.smtp_use_tls = os.getenv("SMTP_USE_TLS", "false").lower() == "true"
        self.default_from = os.getenv("DEFAULT_FROM_EMAIL", "noreply@estateflow.local")

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send an email.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Plain text body
            html_body: Optional HTML body
            from_email: Sender email (defaults to configured default)
            from_name: Sender name
            attachments: List of attachment dicts with filename, content, content_type

        Returns:
            Dict with success status and message
        """
        sender = from_email or self.default_from
        if from_name:
            sender = f"{from_name} <{sender}>"

        try:
            msg = MIMEMultipart("mixed")
            msg["From"] = sender
            msg["To"] = to
            msg["Subject"] = subject

            # Add body
            if html_body:
                alt_part = MIMEMultipart("alternative")
                alt_part.attach(MIMEText(body, "plain"))
                alt_part.attach(MIMEText(html_body, "html"))
                msg.attach(alt_part)
            else:
                msg.attach(MIMEText(body, "plain"))

            # Add attachments
            if attachments:
                for attachment in attachments:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment["content"])
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f'attachment; filename="{attachment["filename"]}"'
                    )
                    msg.attach(part)

            # Send via SMTP
            if self.smtp_host and self.smtp_host != "disabled":
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    if self.smtp_use_tls:
                        server.starttls()
                    if self.smtp_user and self.smtp_password:
                        server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)

                logger.info(f"Email sent to {to}: {subject}")
                return {"success": True, "message": f"Email sent to {to}"}
            else:
                # Log-only mode
                logger.info(f"[EMAIL LOG] To: {to}, Subject: {subject}, Body length: {len(body)}")
                return {"success": True, "message": "Email logged (SMTP not configured)"}

        except Exception as e:
            logger.error(f"Failed to send email to {to}: {e}")
            return {"success": False, "message": str(e)}


def get_email_service() -> EmailService:
    """Factory function to get email service instance."""
    return EmailService()
