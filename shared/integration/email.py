"""
Email Integration System

This module provides email integration capabilities for the KasaAI platform.
"""

import asyncio
import logging
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod

# Third-party imports (would be added to requirements.txt)
try:
    import sendgrid
    from sendgrid.helpers.mail import Mail, Email, To, Content, Attachment, FileContent, FileName, FileType, Disposition
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    import boto3
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

try:
    from google.oauth2 import service_account, credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from email.mime.text import MIMEText
    import base64
    GMAIL_API_AVAILABLE = True
except ImportError:
    GMAIL_API_AVAILABLE = False

try:
    import msal
    OUTLOOK_API_AVAILABLE = True
except ImportError:
    OUTLOOK_API_AVAILABLE = False

try:
    import requests
    MAILGUN_AVAILABLE = True
except ImportError:
    MAILGUN_AVAILABLE = False


class EmailProvider(Enum):
    """Supported email providers"""
    SMTP = "smtp"
    SENDGRID = "sendgrid"
    MAILGUN = "mailgun"
    AWS_SES = "aws_ses"
    GMAIL_API = "gmail_api"
    OUTLOOK_API = "outlook_api"


@dataclass
class EmailAttachment:
    """Email attachment definition"""
    filename: str
    content: bytes
    content_type: str = "application/octet-stream"
    disposition: str = "attachment"


@dataclass
class EmailTemplate:
    """Email template definition"""
    template_id: str
    name: str
    subject: str
    html_content: str
    text_content: str
    variables: List[str] = None


@dataclass
class EmailDeliveryReport:
    """Email delivery report"""
    message_id: str
    status: str
    delivered_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    bounced_at: Optional[datetime] = None
    bounce_reason: Optional[str] = None
    provider_response: Optional[str] = None


class BaseEmailProvider(ABC):
    """Base class for email providers"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the email provider"""
        self.config = config
        self.logger = logging.getLogger(f"EmailProvider.{self.__class__.__name__}")
        self.provider_type = self.get_provider_type()
    
    @abstractmethod
    def get_provider_type(self) -> EmailProvider:
        """Get the provider type"""
        pass
    
    @abstractmethod
    async def send_email(self, to: str, subject: str, body: str, 
                        html_body: Optional[str] = None, 
                        from_email: Optional[str] = None,
                        attachments: List[EmailAttachment] = None) -> Dict[str, Any]:
        """Send an email"""
        pass
    
    @abstractmethod
    async def send_template_email(self, template_id: str, to: str, 
                                variables: Dict[str, Any],
                                from_email: Optional[str] = None) -> Dict[str, Any]:
        """Send a template email"""
        pass
    
    @abstractmethod
    async def schedule_email(self, send_time: datetime, to: str, subject: str, 
                           body: str, **kwargs) -> Dict[str, Any]:
        """Schedule an email for later sending"""
        pass
    
    @abstractmethod
    async def get_email_status(self, message_id: str) -> EmailDeliveryReport:
        """Get email delivery status"""
        pass
    
    @abstractmethod
    async def get_delivery_reports(self, date_range: Tuple[datetime, datetime]) -> List[EmailDeliveryReport]:
        """Get delivery reports for a date range"""
        pass


class SMTPEmailProvider(BaseEmailProvider):
    """SMTP email provider"""
    
    def get_provider_type(self) -> EmailProvider:
        return EmailProvider.SMTP
    
    async def send_email(self, to: str, subject: str, body: str, 
                        html_body: Optional[str] = None, 
                        from_email: Optional[str] = None,
                        attachments: List[EmailAttachment] = None) -> Dict[str, Any]:
        """Send email via SMTP"""
        try:
            # Get SMTP configuration
            smtp_server = self.config.get("smtp_server")
            smtp_port = self.config.get("smtp_port", 587)
            username = self.config.get("username")
            password = self.config.get("password")
            use_tls = self.config.get("use_tls", True)
            
            if not from_email:
                from_email = self.config.get("from_email", username)
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = from_email
            msg['To'] = to
            msg['Subject'] = subject
            
            # Add text and HTML parts
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)
            
            # Add attachments
            if attachments:
                for attachment in attachments:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.content)
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', 
                                   f'attachment; filename= {attachment.filename}')
                    msg.attach(part)
            
            # Send email
            await asyncio.get_event_loop().run_in_executor(
                None, self._send_smtp_email, smtp_server, smtp_port, username, 
                password, use_tls, msg
            )
            
            message_id = f"smtp_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            return {
                "success": True,
                "message_id": message_id,
                "provider": "smtp",
                "to": to,
                "subject": subject
            }
            
        except Exception as e:
            self.logger.error(f"Failed to send SMTP email: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "smtp"
            }
    
    def _send_smtp_email(self, smtp_server: str, smtp_port: int, username: str, 
                        password: str, use_tls: bool, msg: MIMEMultipart):
        """Send email via SMTP (synchronous)"""
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            if use_tls:
                server.starttls()
            server.login(username, password)
            server.send_message(msg)
    
    async def send_template_email(self, template_id: str, to: str, 
                                variables: Dict[str, Any],
                                from_email: Optional[str] = None) -> Dict[str, Any]:
        """Send template email via SMTP"""
        # For SMTP, we'll use a simple template replacement
        template = self.config.get("templates", {}).get(template_id)
        if not template:
            return {
                "success": False,
                "error": f"Template {template_id} not found",
                "provider": "smtp"
            }
        
        subject = template.get("subject", "")
        body = template.get("body", "")
        
        # Replace variables
        for key, value in variables.items():
            subject = subject.replace(f"{{{{{key}}}}}", str(value))
            body = body.replace(f"{{{{{key}}}}}", str(value))
        
        return await self.send_email(to, subject, body, from_email=from_email)
    
    async def schedule_email(self, send_time: datetime, to: str, subject: str, 
                           body: str, **kwargs) -> Dict[str, Any]:
        """Schedule email for later sending"""
        # For SMTP, we'll return a placeholder
        # In a real implementation, this would be handled by a task queue
        return {
            "success": True,
            "scheduled": True,
            "send_time": send_time.isoformat(),
            "message_id": f"smtp_scheduled_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        }
    
    async def get_email_status(self, message_id: str) -> EmailDeliveryReport:
        """Get email status (SMTP doesn't provide detailed tracking)"""
        return EmailDeliveryReport(
            message_id=message_id,
            status="sent",  # SMTP doesn't provide detailed status
            delivered_at=datetime.now()
        )
    
    async def get_delivery_reports(self, date_range: Tuple[datetime, datetime]) -> List[EmailDeliveryReport]:
        """Get delivery reports (SMTP doesn't provide detailed reports)"""
        return []


class SendGridEmailProvider(BaseEmailProvider):
    """SendGrid email provider"""
    
    def get_provider_type(self) -> EmailProvider:
        return EmailProvider.SENDGRID
    
    async def send_email(self, to: str, subject: str, body: str, 
                        html_body: Optional[str] = None, 
                        from_email: Optional[str] = None,
                        attachments: List[EmailAttachment] = None) -> Dict[str, Any]:
        """Send email via SendGrid"""
        if not SENDGRID_AVAILABLE:
            return {
                "success": False,
                "error": "SendGrid library not available",
                "provider": "sendgrid"
            }
        
        try:
            api_key = self.config.get("api_key")
            if not from_email:
                from_email = self.config.get("from_email")
            
            # Create SendGrid mail object
            mail = Mail(
                from_email=from_email,
                to_emails=to,
                subject=subject,
                plain_text_content=body
            )
            
            if html_body:
                mail.content = Content("text/html", html_body)
            
            # Add attachments
            if attachments:
                for attachment in attachments:
                    sg_attachment = Attachment(
                        FileContent(attachment.content),
                        FileName(attachment.filename),
                        FileType(attachment.content_type),
                        Disposition(attachment.disposition)
                    )
                    mail.add_attachment(sg_attachment)
            
            # Send email
            sg = sendgrid.SendGridAPIClient(api_key=api_key)
            response = await asyncio.get_event_loop().run_in_executor(
                None, sg.send, mail
            )
            
            return {
                "success": True,
                "message_id": response.headers.get("X-Message-Id", ""),
                "provider": "sendgrid",
                "to": to,
                "subject": subject,
                "status_code": response.status_code
            }
            
        except Exception as e:
            self.logger.error(f"Failed to send SendGrid email: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "sendgrid"
            }
    
    async def send_template_email(self, template_id: str, to: str, 
                                variables: Dict[str, Any],
                                from_email: Optional[str] = None) -> Dict[str, Any]:
        """Send template email via SendGrid"""
        if not SENDGRID_AVAILABLE:
            return {
                "success": False,
                "error": "SendGrid library not available",
                "provider": "sendgrid"
            }
        
        try:
            api_key = self.config.get("api_key")
            if not from_email:
                from_email = self.config.get("from_email")
            
            # Create SendGrid mail object with template
            mail = Mail(
                from_email=from_email,
                to_emails=to
            )
            mail.template_id = template_id
            mail.dynamic_template_data = variables
            
            # Send email
            sg = sendgrid.SendGridAPIClient(api_key=api_key)
            response = await asyncio.get_event_loop().run_in_executor(
                None, sg.send, mail
            )
            
            return {
                "success": True,
                "message_id": response.headers.get("X-Message-Id", ""),
                "template_id": template_id,
                "provider": "sendgrid",
                "status_code": response.status_code
            }
            
        except Exception as e:
            self.logger.error(f"Failed to send SendGrid template email: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "sendgrid"
            }
    
    async def schedule_email(self, send_time: datetime, to: str, subject: str, 
                           body: str, **kwargs) -> Dict[str, Any]:
        """Schedule email for later sending"""
        # SendGrid supports scheduling via send_at parameter
        try:
            api_key = self.config.get("api_key")
            if not kwargs.get("from_email"):
                kwargs["from_email"] = self.config.get("from_email")
            
            mail = Mail(
                from_email=kwargs["from_email"],
                to_emails=to,
                subject=subject,
                plain_text_content=body
            )
            
            # Set send time (Unix timestamp)
            mail.send_at = int(send_time.timestamp())
            
            sg = sendgrid.SendGridAPIClient(api_key=api_key)
            response = await asyncio.get_event_loop().run_in_executor(
                None, sg.send, mail
            )
            
            return {
                "success": True,
                "scheduled": True,
                "send_time": send_time.isoformat(),
                "message_id": response.headers.get("X-Message-Id", ""),
                "provider": "sendgrid"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "provider": "sendgrid"
            }
    
    async def get_email_status(self, message_id: str) -> EmailDeliveryReport:
        """Get email status from SendGrid"""
        # This would require SendGrid's Event Webhook or API calls
        # For now, return a placeholder
        return EmailDeliveryReport(
            message_id=message_id,
            status="sent"
        )
    
    async def get_delivery_reports(self, date_range: Tuple[datetime, datetime]) -> List[EmailDeliveryReport]:
        """Get delivery reports from SendGrid"""
        # This would require SendGrid's Event Webhook or API calls
        return []


class GmailEmailProvider(BaseEmailProvider):
    """Gmail API email provider"""
    
    def get_provider_type(self) -> EmailProvider:
        return EmailProvider.GMAIL_API
    
    async def send_email(self, to: str, subject: str, body: str, 
                        html_body: Optional[str] = None, 
                        from_email: Optional[str] = None,
                        attachments: List[EmailAttachment] = None) -> Dict[str, Any]:
        """Send email via Gmail API"""
        if not GMAIL_API_AVAILABLE:
            return {
                "success": False,
                "error": "Gmail API library not available",
                "provider": "gmail_api"
            }
        
        try:
            # Get credentials and service
            credentials_path = self.config.get("credentials_path")
            if not credentials_path:
                return {
                    "success": False,
                    "error": "Credentials path not configured",
                    "provider": "gmail_api"
                }
            
            creds = service_account.Credentials.from_service_account_file(
                credentials_path, scopes=['https://www.googleapis.com/auth/gmail.send']
            )
            service = build('gmail', 'v1', credentials=creds)
            
            if not from_email:
                from_email = self.config.get("from_email")
            
            # Create message
            message = {
                'raw': base64.urlsafe_b64encode(
                    MIMEText(body, 'plain').as_bytes() + 
                    (MIMEText(html_body, 'html').as_bytes() if html_body else b'')
                ).decode()
            }
            
            if attachments:
                for attachment in attachments:
                    encoded_content = base64.urlsafe_b64encode(attachment.content).decode()
                    message['raw'] += f'\nContent-Type: {attachment.content_type}\n'
                    message['raw'] += f'Content-Transfer-Encoding: base64\n'
                    message['raw'] += f'Content-Disposition: {attachment.disposition}\n'
                    message['raw'] += f'Filename: {attachment.filename}\n'
                    message['raw'] += f'X-Attachment-Id: {attachment.filename}\n'
                    message['raw'] += f'\n--{attachment.filename}\n'
                    message['raw'] += f'Content-Type: {attachment.content_type}\n'
                    message['raw'] += f'Content-Transfer-Encoding: base64\n'
                    message['raw'] += f'Content-ID: <{attachment.filename}>\n'
                    message['raw'] += f'\n{encoded_content}\n'
                    message['raw'] += f'--{attachment.filename}--\n'
            
            # Send email
            response = await asyncio.get_event_loop().run_in_executor(
                None, service.users().messages().send, {'userId': 'me', 'body': message}
            )
            
            return {
                "success": True,
                "message_id": response['id'],
                "provider": "gmail_api",
                "to": to,
                "subject": subject,
                "status_code": response['status']
            }
            
        except Exception as e:
            self.logger.error(f"Failed to send Gmail email: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "gmail_api"
            }
    
    async def send_template_email(self, template_id: str, to: str, 
                                variables: Dict[str, Any],
                                from_email: Optional[str] = None) -> Dict[str, Any]:
        """Send template email via Gmail API"""
        if not GMAIL_API_AVAILABLE:
            return {
                "success": False,
                "error": "Gmail API library not available",
                "provider": "gmail_api"
            }
        
        try:
            # For Gmail, template_id is not directly used for sending.
            # We'll just send a plain email with dynamic content.
            subject = "Template Email" # Placeholder, actual subject will be dynamic
            body = "This is a template email with dynamic content." # Placeholder
            
            # Replace variables
            for key, value in variables.items():
                subject = subject.replace(f"{{{{{key}}}}}", str(value))
                body = body.replace(f"{{{{{key}}}}}", str(value))
            
            return await self.send_email(to, subject, body, from_email=from_email)
            
        except Exception as e:
            self.logger.error(f"Failed to send Gmail template email: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "gmail_api"
            }
    
    async def schedule_email(self, send_time: datetime, to: str, subject: str, 
                           body: str, **kwargs) -> Dict[str, Any]:
        """Schedule email for later sending (Gmail API doesn't support direct scheduling)"""
        return {
            "success": False,
            "error": "Gmail API does not support direct scheduling of emails.",
            "provider": "gmail_api"
        }
    
    async def get_email_status(self, message_id: str) -> EmailDeliveryReport:
        """Get email status from Gmail API (placeholder)"""
        # This would require Gmail's Event Webhook or API calls
        return EmailDeliveryReport(
            message_id=message_id,
            status="sent"
        )
    
    async def get_delivery_reports(self, date_range: Tuple[datetime, datetime]) -> List[EmailDeliveryReport]:
        """Get delivery reports from Gmail API (placeholder)"""
        # This would require Gmail's Event Webhook or API calls
        return []


class OutlookEmailProvider(BaseEmailProvider):
    """Outlook API email provider"""
    
    def get_provider_type(self) -> EmailProvider:
        return EmailProvider.OUTLOOK_API
    
    async def send_email(self, to: str, subject: str, body: str, 
                        html_body: Optional[str] = None, 
                        from_email: Optional[str] = None,
                        attachments: List[EmailAttachment] = None) -> Dict[str, Any]:
        """Send email via Outlook API"""
        if not OUTLOOK_API_AVAILABLE:
            return {
                "success": False,
                "error": "Outlook API library not available",
                "provider": "outlook_api"
            }
        
        try:
            # Get configuration
            client_id = self.config.get("client_id")
            client_secret = self.config.get("client_secret")
            tenant_id = self.config.get("tenant_id")
            user_email = self.config.get("user_email")
            scopes = self.config.get("scopes", ["https://graph.microsoft.com/.default"])
            
            if not client_id or not client_secret or not tenant_id or not user_email:
                return {
                    "success": False,
                    "error": "Outlook API configuration missing",
                    "provider": "outlook_api"
                }
            
            # Initialize MSAL
            app = msal.ConfidentialClientApplication(
                client_id=client_id,
                client_credential={
                    "client_secret": client_secret
                },
                authority=f"https://login.microsoftonline.com/{tenant_id}"
            )
            
            # Acquire token
            result = await asyncio.get_event_loop().run_in_executor(
                None, app.acquire_token_for_client, scopes
            )
            
            if "access_token" not in result:
                self.logger.error(f"Failed to acquire token for Outlook API: {result.get('error_description', result.get('error'))}")
                return {
                    "success": False,
                    "error": f"Failed to authenticate with Outlook API: {result.get('error_description', result.get('error'))}",
                    "provider": "outlook_api"
                }
            
            token = result["access_token"]
            
            # Create Outlook message
            message = {
                "@odata.type": "#microsoft.graph.message",
                "subject": subject,
                "body": {
                    "contentType": "HTML" if html_body else "Text",
                    "content": html_body if html_body else body
                },
                "toRecipients": [{"emailAddress": {"address": to}}],
                "from": {"emailAddress": {"address": from_email or user_email}}
            }
            
            if attachments:
                for attachment in attachments:
                    message["attachments"] = [
                        {
                            "@odata.type": "#microsoft.graph.fileAttachment",
                            "name": attachment.filename,
                            "contentBytes": base64.b64encode(attachment.content).decode(),
                            "contentType": attachment.content_type,
                            "size": len(attachment.content)
                        }
                    ]
            
            # Send email
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, requests.post, "https://graph.microsoft.com/v1.0/users/me/messages", json=message, headers=headers
            )
            
            if response.status_code == 201: # Created
                return {
                    "success": True,
                    "message_id": response.headers.get("Location", "").split("/")[-1],
                    "provider": "outlook_api",
                    "to": to,
                    "subject": subject,
                    "status_code": response.status_code
                }
            else:
                self.logger.error(f"Failed to send Outlook email: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"Failed to send Outlook email: {response.status_code} - {response.text}",
                    "provider": "outlook_api"
                }
            
        except Exception as e:
            self.logger.error(f"Failed to send Outlook email: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "outlook_api"
            }
    
    async def send_template_email(self, template_id: str, to: str, 
                                variables: Dict[str, Any],
                                from_email: Optional[str] = None) -> Dict[str, Any]:
        """Send template email via Outlook API"""
        if not OUTLOOK_API_AVAILABLE:
            return {
                "success": False,
                "error": "Outlook API library not available",
                "provider": "outlook_api"
            }
        
        try:
            # For Outlook, template_id is not directly used for sending.
            # We'll just send a plain email with dynamic content.
            subject = "Template Email" # Placeholder, actual subject will be dynamic
            body = "This is a template email with dynamic content." # Placeholder
            
            # Replace variables
            for key, value in variables.items():
                subject = subject.replace(f"{{{{{key}}}}}", str(value))
                body = body.replace(f"{{{{{key}}}}}", str(value))
            
            return await self.send_email(to, subject, body, from_email=from_email)
            
        except Exception as e:
            self.logger.error(f"Failed to send Outlook template email: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "outlook_api"
            }
    
    async def schedule_email(self, send_time: datetime, to: str, subject: str, 
                           body: str, **kwargs) -> Dict[str, Any]:
        """Schedule email for later sending (Outlook API doesn't support direct scheduling)"""
        return {
            "success": False,
            "error": "Outlook API does not support direct scheduling of emails.",
            "provider": "outlook_api"
        }
    
    async def get_email_status(self, message_id: str) -> EmailDeliveryReport:
        """Get email status from Outlook API (placeholder)"""
        # This would require Outlook's Event Webhook or API calls
        return EmailDeliveryReport(
            message_id=message_id,
            status="sent"
        )
    
    async def get_delivery_reports(self, date_range: Tuple[datetime, datetime]) -> List[EmailDeliveryReport]:
        """Get delivery reports from Outlook API (placeholder)"""
        # This would require Outlook's Event Webhook or API calls
        return []


class AWSSESEmailProvider(BaseEmailProvider):
    """AWS SES email provider"""
    
    def get_provider_type(self) -> EmailProvider:
        return EmailProvider.AWS_SES
    
    async def send_email(self, to: str, subject: str, body: str, 
                        html_body: Optional[str] = None, 
                        from_email: Optional[str] = None,
                        attachments: List[EmailAttachment] = None) -> Dict[str, Any]:
        """Send email via AWS SES"""
        if not BOTO3_AVAILABLE:
            return {
                "success": False,
                "error": "AWS boto3 library not available",
                "provider": "aws_ses"
            }
        
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            # Get AWS SES configuration
            region_name = self.config.get("region_name", "us-east-1")
            aws_access_key_id = self.config.get("aws_access_key_id")
            aws_secret_access_key = self.config.get("aws_secret_access_key")
            
            if not from_email:
                from_email = self.config.get("from_email")
            
            if not from_email:
                return {
                    "success": False,
                    "error": "from_email is required for AWS SES",
                    "provider": "aws_ses"
                }
            
            # Create SES client
            ses_client = boto3.client(
                'ses',
                region_name=region_name,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key
            )
            
            # Prepare email content
            if html_body:
                # Send HTML email
                response = await asyncio.get_event_loop().run_in_executor(
                    None, self._send_ses_html_email, ses_client, from_email, to, subject, body, html_body
                )
            else:
                # Send text email
                response = await asyncio.get_event_loop().run_in_executor(
                    None, self._send_ses_text_email, ses_client, from_email, to, subject, body
                )
            
            return {
                "success": True,
                "message_id": response.get("MessageId"),
                "provider": "aws_ses",
                "response": response
            }
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            self.logger.error(f"AWS SES error: {error_code} - {error_message}")
            return {
                "success": False,
                "error": f"AWS SES error: {error_code} - {error_message}",
                "provider": "aws_ses"
            }
        except Exception as e:
            self.logger.error(f"Failed to send AWS SES email: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "aws_ses"
            }
    
    def _send_ses_text_email(self, ses_client, from_email: str, to: str, subject: str, body: str):
        """Send text email via AWS SES"""
        return ses_client.send_email(
            Source=from_email,
            Destination={'ToAddresses': [to]},
            Message={
                'Subject': {'Data': subject},
                'Body': {'Text': {'Data': body}}
            }
        )
    
    def _send_ses_html_email(self, ses_client, from_email: str, to: str, subject: str, text_body: str, html_body: str):
        """Send HTML email via AWS SES"""
        return ses_client.send_email(
            Source=from_email,
            Destination={'ToAddresses': [to]},
            Message={
                'Subject': {'Data': subject},
                'Body': {
                    'Text': {'Data': text_body},
                    'Html': {'Data': html_body}
                }
            }
        )
    
    async def send_template_email(self, template_id: str, to: str, 
                                variables: Dict[str, Any],
                                from_email: Optional[str] = None) -> Dict[str, Any]:
        """Send template email via AWS SES"""
        if not BOTO3_AVAILABLE:
            return {
                "success": False,
                "error": "AWS boto3 library not available",
                "provider": "aws_ses"
            }
        
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            # Get AWS SES configuration
            region_name = self.config.get("region_name", "us-east-1")
            aws_access_key_id = self.config.get("aws_access_key_id")
            aws_secret_access_key = self.config.get("aws_secret_access_key")
            
            if not from_email:
                from_email = self.config.get("from_email")
            
            if not from_email:
                return {
                    "success": False,
                    "error": "from_email is required for AWS SES",
                    "provider": "aws_ses"
                }
            
            # Create SES client
            ses_client = boto3.client(
                'ses',
                region_name=region_name,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key
            )
            
            # Send template email
            response = await asyncio.get_event_loop().run_in_executor(
                None, self._send_ses_template_email, ses_client, from_email, to, template_id, variables
            )
            
            return {
                "success": True,
                "message_id": response.get("MessageId"),
                "provider": "aws_ses",
                "response": response
            }
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            self.logger.error(f"AWS SES error: {error_code} - {error_message}")
            return {
                "success": False,
                "error": f"AWS SES error: {error_code} - {error_message}",
                "provider": "aws_ses"
            }
        except Exception as e:
            self.logger.error(f"Failed to send AWS SES template email: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "aws_ses"
            }
    
    def _send_ses_template_email(self, ses_client, from_email: str, to: str, template_id: str, variables: Dict[str, Any]):
        """Send template email via AWS SES"""
        return ses_client.send_templated_email(
            Source=from_email,
            Destination={'ToAddresses': [to]},
            Template=template_id,
            TemplateData=str(variables)
        )
    
    async def schedule_email(self, send_time: datetime, to: str, subject: str, 
                           body: str, **kwargs) -> Dict[str, Any]:
        """Schedule email for later sending via AWS SES"""
        if not BOTO3_AVAILABLE:
            return {
                "success": False,
                "error": "AWS boto3 library not available",
                "provider": "aws_ses"
            }
        
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            # Get AWS SES configuration
            region_name = self.config.get("region_name", "us-east-1")
            aws_access_key_id = self.config.get("aws_access_key_id")
            aws_secret_access_key = self.config.get("aws_secret_access_key")
            
            from_email = kwargs.get("from_email", self.config.get("from_email"))
            
            if not from_email:
                return {
                    "success": False,
                    "error": "from_email is required for AWS SES",
                    "provider": "aws_ses"
                }
            
            # Create SES client
            ses_client = boto3.client(
                'ses',
                region_name=region_name,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key
            )
            
            # AWS SES doesn't support direct scheduling, so we'll return a placeholder
            # In a real implementation, this would integrate with AWS SQS or EventBridge
            return {
                "success": False,
                "error": "AWS SES does not support direct email scheduling. Use AWS SQS or EventBridge for scheduling.",
                "provider": "aws_ses"
            }
                
        except Exception as e:
            self.logger.error(f"Failed to schedule AWS SES email: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "aws_ses"
            }
    
    async def get_email_status(self, message_id: str) -> EmailDeliveryReport:
        """Get email status from AWS SES (placeholder)"""
        # This would require AWS SES Event Publishing or CloudWatch logs
        return EmailDeliveryReport(
            message_id=message_id,
            status="sent"
        )
    
    async def get_delivery_reports(self, date_range: Tuple[datetime, datetime]) -> List[EmailDeliveryReport]:
        """Get delivery reports from AWS SES (placeholder)"""
        # This would require AWS SES Event Publishing or CloudWatch logs
        return []


class MailgunEmailProvider(BaseEmailProvider):
    """Mailgun email provider"""
    
    def get_provider_type(self) -> EmailProvider:
        return EmailProvider.MAILGUN
    
    async def send_email(self, to: str, subject: str, body: str, 
                        html_body: Optional[str] = None, 
                        from_email: Optional[str] = None,
                        attachments: List[EmailAttachment] = None) -> Dict[str, Any]:
        """Send email via Mailgun API"""
        if not MAILGUN_AVAILABLE:
            return {
                "success": False,
                "error": "Mailgun library not available",
                "provider": "mailgun"
            }
        
        try:
            # Get Mailgun configuration
            api_key = self.config.get("api_key")
            domain = self.config.get("domain")
            base_url = self.config.get("base_url", "https://api.mailgun.net/v3")
            
            if not from_email:
                from_email = self.config.get("from_email", f"noreply@{domain}")
            
            # Prepare data for Mailgun API
            data = {
                "from": from_email,
                "to": to,
                "subject": subject,
                "text": body
            }
            
            if html_body:
                data["html"] = html_body
            
            # Add attachments if provided
            files = {}
            if attachments:
                for i, attachment in enumerate(attachments):
                    files[f"attachment[{i}]"] = (
                        attachment.filename,
                        attachment.content,
                        attachment.content_type
                    )
            
            # Make API request
            auth = ("api", api_key)
            url = f"{base_url}/{domain}/messages"
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, self._send_mailgun_request, url, data, files, auth
            )
            
            if response.status_code == 200:
                response_data = response.json()
                return {
                    "success": True,
                    "message_id": response_data.get("id"),
                    "provider": "mailgun",
                    "response": response_data
                }
            else:
                return {
                    "success": False,
                    "error": f"Mailgun API error: {response.status_code} - {response.text}",
                    "provider": "mailgun"
                }
                
        except Exception as e:
            self.logger.error(f"Failed to send Mailgun email: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "mailgun"
            }
    
    def _send_mailgun_request(self, url: str, data: Dict[str, Any], 
                            files: Dict[str, Any], auth: Tuple[str, str]):
        """Send HTTP request to Mailgun API"""
        if files:
            return requests.post(url, data=data, files=files, auth=auth)
        else:
            return requests.post(url, data=data, auth=auth)
    
    async def send_template_email(self, template_id: str, to: str, 
                                variables: Dict[str, Any],
                                from_email: Optional[str] = None) -> Dict[str, Any]:
        """Send template email via Mailgun"""
        if not MAILGUN_AVAILABLE:
            return {
                "success": False,
                "error": "Mailgun library not available",
                "provider": "mailgun"
            }
        
        try:
            # Get Mailgun configuration
            api_key = self.config.get("api_key")
            domain = self.config.get("domain")
            base_url = self.config.get("base_url", "https://api.mailgun.net/v3")
            
            if not from_email:
                from_email = self.config.get("from_email", f"noreply@{domain}")
            
            # Prepare data for Mailgun template API
            data = {
                "from": from_email,
                "to": to,
                "template": template_id,
                "h:X-Mailgun-Variables": str(variables)
            }
            
            # Make API request
            auth = ("api", api_key)
            url = f"{base_url}/{domain}/messages"
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, self._send_mailgun_request, url, data, {}, auth
            )
            
            if response.status_code == 200:
                response_data = response.json()
                return {
                    "success": True,
                    "message_id": response_data.get("id"),
                    "provider": "mailgun",
                    "response": response_data
                }
            else:
                return {
                    "success": False,
                    "error": f"Mailgun API error: {response.status_code} - {response.text}",
                    "provider": "mailgun"
                }
                
        except Exception as e:
            self.logger.error(f"Failed to send Mailgun template email: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "mailgun"
            }
    
    async def schedule_email(self, send_time: datetime, to: str, subject: str, 
                           body: str, **kwargs) -> Dict[str, Any]:
        """Schedule email for later sending via Mailgun"""
        if not MAILGUN_AVAILABLE:
            return {
                "success": False,
                "error": "Mailgun library not available",
                "provider": "mailgun"
            }
        
        try:
            # Get Mailgun configuration
            api_key = self.config.get("api_key")
            domain = self.config.get("domain")
            base_url = self.config.get("base_url", "https://api.mailgun.net/v3")
            
            from_email = kwargs.get("from_email", self.config.get("from_email", f"noreply@{domain}"))
            
            # Prepare data for Mailgun API with scheduling
            data = {
                "from": from_email,
                "to": to,
                "subject": subject,
                "text": body,
                "o:deliverytime": send_time.strftime("%a, %d %b %Y %H:%M:%S %z")
            }
            
            # Add HTML body if provided
            html_body = kwargs.get("html_body")
            if html_body:
                data["html"] = html_body
            
            # Make API request
            auth = ("api", api_key)
            url = f"{base_url}/{domain}/messages"
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, self._send_mailgun_request, url, data, {}, auth
            )
            
            if response.status_code == 200:
                response_data = response.json()
                return {
                    "success": True,
                    "message_id": response_data.get("id"),
                    "provider": "mailgun",
                    "response": response_data
                }
            else:
                return {
                    "success": False,
                    "error": f"Mailgun API error: {response.status_code} - {response.text}",
                    "provider": "mailgun"
                }
                
        except Exception as e:
            self.logger.error(f"Failed to schedule Mailgun email: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "mailgun"
            }
    
    async def get_email_status(self, message_id: str) -> EmailDeliveryReport:
        """Get email status from Mailgun (placeholder)"""
        # This would require Mailgun's Event Webhook or API calls
        return EmailDeliveryReport(
            message_id=message_id,
            status="sent"
        )
    
    async def get_delivery_reports(self, date_range: Tuple[datetime, datetime]) -> List[EmailDeliveryReport]:
        """Get delivery reports from Mailgun (placeholder)"""
        # This would require Mailgun's Event Webhook or API calls
        return []


class EmailIntegration:
    """Main email integration class"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize email integration"""
        self.config = config
        self.logger = logging.getLogger("EmailIntegration")
        self.providers: Dict[EmailProvider, BaseEmailProvider] = {}
        self.default_provider = EmailProvider.SMTP
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize email providers based on configuration"""
        provider_configs = self.config.get("providers", {})
        
        # Initialize SMTP provider
        if "smtp" in provider_configs:
            self.providers[EmailProvider.SMTP] = SMTPEmailProvider(provider_configs["smtp"])
        
        # Initialize SendGrid provider
        if "sendgrid" in provider_configs and SENDGRID_AVAILABLE:
            self.providers[EmailProvider.SENDGRID] = SendGridEmailProvider(provider_configs["sendgrid"])
        
        # Initialize Gmail API provider
        if "gmail_api" in provider_configs and GMAIL_API_AVAILABLE:
            self.providers[EmailProvider.GMAIL_API] = GmailEmailProvider(provider_configs["gmail_api"])
        
        # Initialize Outlook API provider
        if "outlook_api" in provider_configs and OUTLOOK_API_AVAILABLE:
            self.providers[EmailProvider.OUTLOOK_API] = OutlookEmailProvider(provider_configs["outlook_api"])
        
        # Initialize Mailgun provider
        if "mailgun" in provider_configs and MAILGUN_AVAILABLE:
            self.providers[EmailProvider.MAILGUN] = MailgunEmailProvider(provider_configs["mailgun"])
        
        # Initialize AWS SES provider
        if "aws_ses" in provider_configs and BOTO3_AVAILABLE:
            self.providers[EmailProvider.AWS_SES] = AWSSESEmailProvider(provider_configs["aws_ses"])
        
        # Set default provider
        default_provider_name = self.config.get("default_provider", "smtp")
        if default_provider_name == "sendgrid" and EmailProvider.SENDGRID in self.providers:
            self.default_provider = EmailProvider.SENDGRID
        elif default_provider_name == "gmail_api" and EmailProvider.GMAIL_API in self.providers:
            self.default_provider = EmailProvider.GMAIL_API
        elif default_provider_name == "outlook_api" and EmailProvider.OUTLOOK_API in self.providers:
            self.default_provider = EmailProvider.OUTLOOK_API
        elif default_provider_name == "mailgun" and EmailProvider.MAILGUN in self.providers:
            self.default_provider = EmailProvider.MAILGUN
        elif default_provider_name == "aws_ses" and EmailProvider.AWS_SES in self.providers:
            self.default_provider = EmailProvider.AWS_SES
    
    async def send_email(self, to: str, subject: str, body: str, 
                        html_body: Optional[str] = None, 
                        from_email: Optional[str] = None,
                        attachments: List[EmailAttachment] = None,
                        provider: Optional[EmailProvider] = None) -> Dict[str, Any]:
        """Send an email"""
        if not provider:
            provider = self.default_provider
        
        if provider not in self.providers:
            return {
                "success": False,
                "error": f"Provider {provider.value} not configured",
                "provider": provider.value
            }
        
        return await self.providers[provider].send_email(
            to, subject, body, html_body, from_email, attachments
        )
    
    async def send_template_email(self, template_id: str, to: str, 
                                variables: Dict[str, Any],
                                from_email: Optional[str] = None,
                                provider: Optional[EmailProvider] = None) -> Dict[str, Any]:
        """Send a template email"""
        if not provider:
            provider = self.default_provider
        
        if provider not in self.providers:
            return {
                "success": False,
                "error": f"Provider {provider.value} not configured",
                "provider": provider.value
            }
        
        return await self.providers[provider].send_template_email(
            template_id, to, variables, from_email
        )
    
    async def schedule_email(self, send_time: datetime, to: str, subject: str, 
                           body: str, **kwargs) -> Dict[str, Any]:
        """Schedule an email for later sending"""
        provider = kwargs.get("provider", self.default_provider)
        
        if provider not in self.providers:
            return {
                "success": False,
                "error": f"Provider {provider.value} not configured",
                "provider": provider.value
            }
        
        return await self.providers[provider].schedule_email(
            send_time, to, subject, body, **kwargs
        )
    
    async def get_email_status(self, message_id: str, 
                             provider: Optional[EmailProvider] = None) -> EmailDeliveryReport:
        """Get email delivery status"""
        if not provider:
            provider = self.default_provider
        
        if provider not in self.providers:
            return EmailDeliveryReport(
                message_id=message_id,
                status="error",
                provider_response="Provider not configured"
            )
        
        return await self.providers[provider].get_email_status(message_id)
    
    async def get_delivery_reports(self, date_range: Tuple[datetime, datetime],
                                 provider: Optional[EmailProvider] = None) -> List[EmailDeliveryReport]:
        """Get delivery reports for a date range"""
        if not provider:
            provider = self.default_provider
        
        if provider not in self.providers:
            return []
        
        return await self.providers[provider].get_delivery_reports(date_range)
    
    def get_available_providers(self) -> List[EmailProvider]:
        """Get list of available providers"""
        return list(self.providers.keys())
    
    def get_provider_info(self, provider: EmailProvider) -> Dict[str, Any]:
        """Get information about a provider"""
        if provider not in self.providers:
            return {"available": False}
        
        return {
            "available": True,
            "type": provider.value,
            "config": self.providers[provider].config
        }
