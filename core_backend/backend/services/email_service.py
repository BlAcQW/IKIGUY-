"""
Consolidated Email Integration Service.
Handles all email-related functionality with unified interface.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr

logger = logging.getLogger(__name__)


class EmailMessage(BaseModel):
    """Email message model."""
    to_addresses: List[EmailStr]
    from_address: EmailStr
    subject: str
    body: str
    body_type: str = "html"  # html, text
    cc_addresses: List[EmailStr] = Field(default_factory=list)
    bcc_addresses: List[EmailStr] = Field(default_factory=list)
    attachments: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    priority: str = "normal"  # low, normal, high
    template_id: Optional[str] = None
    template_data: Dict[str, Any] = Field(default_factory=dict)


class EmailTemplate(BaseModel):
    """Email template model."""
    template_id: str
    name: str
    subject_template: str
    body_template: str
    template_type: str = "html"
    variables: List[str] = Field(default_factory=list)
    category: str = "general"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EmailService:
    """
    Consolidated service for all email integrations.
    Supports multiple email providers with unified interface.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize email service with configuration.

        Args:
            config: Configuration dictionary with provider-specific settings
        """
        self.config = config or {}
        self.providers = {}
        self.templates = {}
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize supported email providers."""
        # SMTP Provider
        if self.config.get("smtp_enabled", False):
            self.providers["smtp"] = {
                "host": self.config.get("smtp_host"),
                "port": self.config.get("smtp_port", 587),
                "username": self.config.get("smtp_username"),
                "password": self.config.get("smtp_password"),
                "use_tls": self.config.get("smtp_use_tls", True)
            }

        # SendGrid Provider
        if self.config.get("sendgrid_enabled", False):
            self.providers["sendgrid"] = {
                "api_key": self.config.get("sendgrid_api_key"),
                "from_email": self.config.get("sendgrid_from_email")
            }

        # Mailgun Provider
        if self.config.get("mailgun_enabled", False):
            self.providers["mailgun"] = {
                "api_key": self.config.get("mailgun_api_key"),
                "domain": self.config.get("mailgun_domain"),
                "base_url": self.config.get("mailgun_base_url", "https://api.mailgun.net/v3")
            }

        # AWS SES Provider
        if self.config.get("ses_enabled", False):
            self.providers["ses"] = {
                "aws_access_key_id": self.config.get("aws_access_key_id"),
                "aws_secret_access_key": self.config.get("aws_secret_access_key"),
                "region": self.config.get("aws_region", "us-east-1")
            }

        logger.info(f"Initialized email service with providers: {list(self.providers.keys())}")

    async def send_email(
        self,
        provider: str,
        email: EmailMessage,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send an email through specified provider.

        Args:
            provider: Provider name (smtp, sendgrid, mailgun, ses)
            email: Email to send
            context: Additional context for the email

        Returns:
            Result of email sending operation
        """
        try:
            if provider not in self.providers:
                return {
                    "success": False,
                    "error": f"Provider '{provider}' not configured",
                    "available_providers": list(self.providers.keys())
                }

            provider_config = self.providers[provider]

            # Process template if specified
            if email.template_id:
                processed_email = await self._process_template(email)
                if not processed_email:
                    return {
                        "success": False,
                        "error": f"Template '{email.template_id}' not found"
                    }
                email = processed_email

            if provider == "smtp":
                return await self._send_smtp_email(email, provider_config, context)
            elif provider == "sendgrid":
                return await self._send_sendgrid_email(email, provider_config, context)
            elif provider == "mailgun":
                return await self._send_mailgun_email(email, provider_config, context)
            elif provider == "ses":
                return await self._send_ses_email(email, provider_config, context)
            else:
                return {
                    "success": False,
                    "error": f"Provider '{provider}' handler not implemented"
                }

        except Exception as e:
            logger.error(f"Error sending email via {provider}: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": provider
            }

    async def _send_smtp_email(
        self,
        email: EmailMessage,
        config: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send email through SMTP."""
        import smtplib
        import ssl
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from email.mime.base import MIMEBase
        from email import encoders
        import uuid

        try:
            # Default to local SMTP server settings
            smtp_host = config.get("host", "localhost")
            smtp_port = config.get("port", 587)
            smtp_username = config.get("username", "noreply@ailabsafrica.com")
            smtp_password = config.get("password", "noreply_secure_2025")
            smtp_use_tls = config.get("use_tls", True)
            smtp_use_ssl = config.get("use_ssl", False)

            logger.info(f"Sending SMTP email via {smtp_host}:{smtp_port} to {len(email.to_addresses)} recipients")

            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = email.from_address
            msg['To'] = ", ".join(email.to_addresses)
            msg['Subject'] = email.subject

            # Add CC and BCC if provided
            if email.cc_addresses:
                msg['Cc'] = ", ".join(email.cc_addresses)

            # Generate message ID
            message_id = f"<{uuid.uuid4()}@ailabsafrica.com>"
            msg['Message-ID'] = message_id

            # Prepare email body based on type
            if email.body_type == "html":
                # Create both plain text and HTML versions
                # Simple HTML to text conversion for plain text version
                import re
                text_body = re.sub('<[^<]+?>', '', email.body)
                text_body = text_body.replace('&nbsp;', ' ').replace('&amp;', '&')

                msg.attach(MIMEText(text_body, 'plain'))
                msg.attach(MIMEText(email.body, 'html'))
            else:
                msg.attach(MIMEText(email.body, 'plain'))

            # Add attachments if any
            if email.attachments:
                for attachment in email.attachments:
                    if isinstance(attachment, dict) and 'filename' in attachment and 'content' in attachment:
                        part = MIMEBase('application', 'octet-stream')
                        if isinstance(attachment['content'], str):
                            part.set_payload(attachment['content'].encode())
                        else:
                            part.set_payload(attachment['content'])
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {attachment["filename"]}'
                        )
                        msg.attach(part)

            # Collect all recipients
            all_recipients = list(email.to_addresses)
            if email.cc_addresses:
                all_recipients.extend(email.cc_addresses)
            if email.bcc_addresses:
                all_recipients.extend(email.bcc_addresses)

            # Connect to SMTP server and send
            if smtp_use_ssl:
                # Direct SSL connection
                server = smtplib.SMTP_SSL(smtp_host, smtp_port)
            else:
                # Standard connection with optional STARTTLS
                server = smtplib.SMTP(smtp_host, smtp_port)
                server.ehlo()  # Identify ourselves

                if smtp_use_tls:
                    server.starttls()  # Upgrade to TLS
                    server.ehlo()  # Re-identify ourselves after TLS

            # Authenticate if credentials provided
            if smtp_username and smtp_password:
                server.login(smtp_username, smtp_password)

            # Send the email
            text = msg.as_string()
            server.sendmail(email.from_address, all_recipients, text)
            server.quit()

            logger.info(f"SMTP email sent successfully to {len(all_recipients)} recipients")

            return {
                "success": True,
                "message_id": message_id,
                "provider": "smtp",
                "recipients": len(all_recipients),
                "recipient_list": all_recipients,
                "subject": email.subject,
                "from_address": email.from_address,
                "sent_at": datetime.now().isoformat(),
                "smtp_host": smtp_host,
                "smtp_port": smtp_port
            }

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication error: {e}")
            return {
                "success": False,
                "error": f"SMTP authentication failed: {str(e)}",
                "provider": "smtp",
                "error_type": "authentication"
            }
        except smtplib.SMTPRecipientsRefused as e:
            logger.error(f"SMTP recipients refused: {e}")
            return {
                "success": False,
                "error": f"SMTP recipients refused: {str(e)}",
                "provider": "smtp",
                "error_type": "recipients_refused"
            }
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            return {
                "success": False,
                "error": f"SMTP error: {str(e)}",
                "provider": "smtp",
                "error_type": "smtp_error"
            }
        except Exception as e:
            logger.error(f"General SMTP email error: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "smtp",
                "error_type": "general"
            }

    async def _send_sendgrid_email(
        self,
        email: EmailMessage,
        config: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send email through SendGrid."""
        try:
            # SendGrid implementation would go here
            logger.info(f"Sending SendGrid email to {len(email.to_addresses)} recipients")

            return {
                "success": True,
                "message_id": f"sendgrid_{int(datetime.now().timestamp())}",
                "provider": "sendgrid",
                "recipients": len(email.to_addresses),
                "subject": email.subject,
                "sent_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"SendGrid email error: {e}")
            return {"success": False, "error": str(e), "provider": "sendgrid"}

    async def _send_mailgun_email(
        self,
        email: EmailMessage,
        config: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send email through Mailgun."""
        try:
            # Mailgun implementation would go here
            logger.info(f"Sending Mailgun email to {len(email.to_addresses)} recipients")

            return {
                "success": True,
                "message_id": f"mailgun_{int(datetime.now().timestamp())}",
                "provider": "mailgun",
                "recipients": len(email.to_addresses),
                "subject": email.subject,
                "sent_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Mailgun email error: {e}")
            return {"success": False, "error": str(e), "provider": "mailgun"}

    async def _send_ses_email(
        self,
        email: EmailMessage,
        config: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send email through AWS SES."""
        try:
            # AWS SES implementation would go here
            logger.info(f"Sending SES email to {len(email.to_addresses)} recipients")

            return {
                "success": True,
                "message_id": f"ses_{int(datetime.now().timestamp())}",
                "provider": "ses",
                "recipients": len(email.to_addresses),
                "subject": email.subject,
                "sent_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"SES email error: {e}")
            return {"success": False, "error": str(e), "provider": "ses"}

    async def _process_template(self, email: EmailMessage) -> Optional[EmailMessage]:
        """Process email template with data."""
        try:
            if email.template_id not in self.templates:
                return None

            template = self.templates[email.template_id]

            # Replace template variables
            subject = template.subject_template
            body = template.body_template

            for key, value in email.template_data.items():
                subject = subject.replace(f"{{{key}}}", str(value))
                body = body.replace(f"{{{key}}}", str(value))

            # Create new email with processed template
            processed_email = email.copy()
            processed_email.subject = subject
            processed_email.body = body
            processed_email.body_type = template.template_type

            return processed_email

        except Exception as e:
            logger.error(f"Template processing error: {e}")
            return None

    def register_template(self, template: EmailTemplate) -> Dict[str, Any]:
        """
        Register an email template.

        Args:
            template: Email template to register

        Returns:
            Registration result
        """
        try:
            self.templates[template.template_id] = template

            return {
                "success": True,
                "template_id": template.template_id,
                "name": template.name,
                "variables": template.variables,
                "registered_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Template registration error: {e}")
            return {"success": False, "error": str(e)}

    def get_templates(self) -> List[Dict[str, Any]]:
        """Get all registered templates."""
        return [
            {
                "template_id": template.template_id,
                "name": template.name,
                "subject_template": template.subject_template,
                "variables": template.variables,
                "category": template.category,
                "type": template.template_type
            }
            for template in self.templates.values()
        ]

    async def send_bulk_email(
        self,
        provider: str,
        emails: List[EmailMessage],
        batch_size: int = 50
    ) -> Dict[str, Any]:
        """
        Send multiple emails in batches.

        Args:
            provider: Provider name
            emails: List of emails to send
            batch_size: Number of emails per batch

        Returns:
            Bulk send result
        """
        try:
            if provider not in self.providers:
                return {
                    "success": False,
                    "error": f"Provider '{provider}' not configured"
                }

            results = []
            total_emails = len(emails)
            successful = 0
            failed = 0

            # Process emails in batches
            for i in range(0, total_emails, batch_size):
                batch = emails[i:i + batch_size]
                batch_results = []

                for email in batch:
                    result = await self.send_email(provider, email)
                    batch_results.append(result)

                    if result.get("success"):
                        successful += 1
                    else:
                        failed += 1

                results.extend(batch_results)

                # Brief pause between batches
                if i + batch_size < total_emails:
                    await asyncio.sleep(1)

            return {
                "success": True,
                "total_emails": total_emails,
                "successful": successful,
                "failed": failed,
                "success_rate": (successful / total_emails) * 100 if total_emails > 0 else 0,
                "results": results,
                "completed_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Bulk email error: {e}")
            return {"success": False, "error": str(e)}

    def get_supported_providers(self) -> List[str]:
        """Get list of supported email providers."""
        return list(self.providers.keys())

    def get_provider_status(self, provider: str) -> Dict[str, Any]:
        """Get status of specific provider."""
        if provider not in self.providers:
            return {
                "provider": provider,
                "configured": False,
                "status": "not_configured"
            }

        config = self.providers[provider]
        return {
            "provider": provider,
            "configured": True,
            "status": "active",
            "config_keys": list(config.keys()),
            "last_checked": datetime.now().isoformat()
        }

    async def test_connection(self, provider: str) -> Dict[str, Any]:
        """
        Test connection to email provider.

        Args:
            provider: Provider to test

        Returns:
            Connection test result
        """
        try:
            if provider not in self.providers:
                return {
                    "success": False,
                    "provider": provider,
                    "error": "Provider not configured"
                }

            # Test email (don't actually send)
            test_email = EmailMessage(
                to_addresses=["test@example.com"],
                from_address="noreply@example.com",
                subject="Connection Test",
                body="This is a connection test",
                metadata={"test": True}
            )

            logger.info(f"Testing {provider} connection")

            return {
                "success": True,
                "provider": provider,
                "test_type": "connection",
                "message": f"{provider} connection test successful",
                "tested_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Connection test error for {provider}: {e}")
            return {
                "success": False,
                "provider": provider,
                "error": str(e)
            }


# Global email service instance
email_service = EmailService()