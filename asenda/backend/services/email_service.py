"""
Email service for sending auto-response emails.
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape
import os

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails."""

    def __init__(
        self,
        smtp_host: str = "localhost",
        smtp_port: int = 25,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        from_email: str = "hello@asenda.ai",
        from_name: str = "Asenda AI",
        use_tls: bool = False,
    ):
        """
        Initialize the email service.

        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            smtp_user: SMTP username for authentication
            smtp_password: SMTP password for authentication
            from_email: Sender email address
            from_name: Sender display name
            use_tls: Whether to use TLS encryption
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.from_email = from_email
        self.from_name = from_name
        self.use_tls = use_tls

        # Set up Jinja2 template environment
        template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """
        Send an email.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML content of the email
            text_content: Plain text fallback content

        Returns:
            bool: True if email was sent successfully
        """
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email

            # Add plain text version
            if text_content:
                part1 = MIMEText(text_content, "plain")
                msg.attach(part1)

            # Add HTML version
            part2 = MIMEText(html_content, "html")
            msg.attach(part2)

            # Connect and send
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_email, to_email, msg.as_string())

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    def send_contact_confirmation(
        self,
        to_email: str,
        name: str,
        message: Optional[str] = None,
    ) -> bool:
        """
        Send contact form confirmation email.

        Args:
            to_email: Recipient email address
            name: Recipient name
            message: Original message from contact form

        Returns:
            bool: True if email was sent successfully
        """
        try:
            template = self.jinja_env.get_template("contact_confirmation.html")
            html_content = template.render(
                name=name,
                message=message,
            )
            text_content = f"""
Hi {name},

Thank you for reaching out to Asenda AI!

We've received your message and our team will get back to you within 24 hours.

In the meantime, feel free to explore our website to learn more about how our voice AI solutions can transform your business.

Best regards,
The Asenda AI Team

---
Asenda AI
hello@asenda.ai
https://asenda.ai
            """
            return self.send_email(
                to_email=to_email,
                subject="Thanks for contacting Asenda AI!",
                html_content=html_content,
                text_content=text_content.strip(),
            )
        except Exception as e:
            logger.error(f"Failed to send contact confirmation: {str(e)}")
            return False

    def send_demo_confirmation(
        self,
        to_email: str,
        name: str,
        company: str,
        preferred_date: Optional[str] = None,
        preferred_time: Optional[str] = None,
    ) -> bool:
        """
        Send demo request confirmation email.

        Args:
            to_email: Recipient email address
            name: Recipient name
            company: Company name
            preferred_date: Preferred demo date
            preferred_time: Preferred demo time

        Returns:
            bool: True if email was sent successfully
        """
        try:
            template = self.jinja_env.get_template("demo_confirmation.html")
            html_content = template.render(
                name=name,
                company=company,
                preferred_date=preferred_date,
                preferred_time=preferred_time,
            )
            text_content = f"""
Hi {name},

Thank you for requesting a demo of Asenda AI!

We're excited to show you how our intelligent voice AI can transform {company}'s customer interactions.

What happens next:
1. Our team will review your request
2. We'll reach out within 24 hours to confirm your demo time
3. You'll receive a calendar invite with meeting details

If you have any questions before the demo, feel free to reply to this email.

Best regards,
The Asenda AI Team

---
Asenda AI
hello@asenda.ai
https://asenda.ai
            """
            return self.send_email(
                to_email=to_email,
                subject=f"Demo Request Received - Asenda AI",
                html_content=html_content,
                text_content=text_content.strip(),
            )
        except Exception as e:
            logger.error(f"Failed to send demo confirmation: {str(e)}")
            return False

    def send_meeting_confirmation(
        self,
        to_email: str,
        name: str,
        meeting_type: str,
        preferred_datetime: Optional[str] = None,
    ) -> bool:
        """
        Send meeting schedule confirmation email.

        Args:
            to_email: Recipient email address
            name: Recipient name
            meeting_type: Type of meeting
            preferred_datetime: Preferred meeting datetime

        Returns:
            bool: True if email was sent successfully
        """
        try:
            template = self.jinja_env.get_template("meeting_confirmation.html")
            html_content = template.render(
                name=name,
                meeting_type=meeting_type,
                preferred_datetime=preferred_datetime,
            )
            text_content = f"""
Hi {name},

Your meeting request has been received!

Meeting Type: {meeting_type}
{f"Requested Time: {preferred_datetime}" if preferred_datetime else ""}

We'll confirm your meeting time within 24 hours and send you a calendar invite.

Best regards,
The Asenda AI Team

---
Asenda AI
hello@asenda.ai
https://asenda.ai
            """
            return self.send_email(
                to_email=to_email,
                subject="Meeting Request Confirmed - Asenda AI",
                html_content=html_content,
                text_content=text_content.strip(),
            )
        except Exception as e:
            logger.error(f"Failed to send meeting confirmation: {str(e)}")
            return False

    def send_newsletter_welcome(
        self,
        to_email: str,
        name: Optional[str] = None,
    ) -> bool:
        """
        Send newsletter subscription welcome email.

        Args:
            to_email: Recipient email address
            name: Recipient name (optional)

        Returns:
            bool: True if email was sent successfully
        """
        try:
            template = self.jinja_env.get_template("newsletter_welcome.html")
            html_content = template.render(name=name)
            greeting = f"Hi {name}," if name else "Hi there,"
            text_content = f"""
{greeting}

Welcome to the Asenda AI newsletter!

You'll now receive updates on:
- Latest voice AI trends and insights
- Product updates and new features
- Industry best practices and case studies
- Exclusive offers and early access

To unsubscribe, click the link at the bottom of any email.

Best regards,
The Asenda AI Team

---
Asenda AI
hello@asenda.ai
https://asenda.ai
            """
            return self.send_email(
                to_email=to_email,
                subject="Welcome to Asenda AI Newsletter!",
                html_content=html_content,
                text_content=text_content.strip(),
            )
        except Exception as e:
            logger.error(f"Failed to send newsletter welcome: {str(e)}")
            return False

    def send_internal_notification(
        self,
        lead_type: str,
        lead_data: dict,
    ) -> bool:
        """
        Send internal notification about new lead.

        Args:
            lead_type: Type of lead (contact, demo, meeting, newsletter)
            lead_data: Lead data dictionary

        Returns:
            bool: True if email was sent successfully
        """
        try:
            internal_email = "leads@asenda.ai"  # Internal notification email
            subject = f"[NEW LEAD] {lead_type.upper()} - {lead_data.get('name', 'Unknown')}"

            details = "\n".join([f"- {k}: {v}" for k, v in lead_data.items() if v])
            text_content = f"""
New {lead_type} lead received:

{details}

---
View all leads in the admin dashboard.
            """
            html_content = f"""
<!DOCTYPE html>
<html>
<head><style>body {{ font-family: Arial, sans-serif; }}</style></head>
<body>
<h2>New {lead_type} Lead</h2>
<table style="border-collapse: collapse;">
{"".join([f'<tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>{k}</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{v}</td></tr>' for k, v in lead_data.items() if v])}
</table>
</body>
</html>
            """
            return self.send_email(
                to_email=internal_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content.strip(),
            )
        except Exception as e:
            logger.error(f"Failed to send internal notification: {str(e)}")
            return False
