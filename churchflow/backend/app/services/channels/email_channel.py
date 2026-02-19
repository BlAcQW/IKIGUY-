"""
Email notification channel using SMTP.

Sends emails via iRedMail SMTP server.
"""

import logging
from typing import Dict, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiosmtplib

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailChannel:
    """
    Email notification channel using SMTP.

    Handles sending emails with HTML and plain text content.
    """

    def __init__(self):
        """Initialize email configuration."""
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password
        self.from_email = settings.smtp_from_email
        self.from_name = settings.smtp_from_name
        self.use_tls = settings.smtp_use_tls
        self.logger = logger

    async def send(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        user_name: Optional[str] = None
    ) -> Dict:
        """
        Send email via SMTP.

        Args:
            to_email: Recipient email address
            subject: Email subject line
            body_text: Plain text email body
            body_html: Optional HTML email body
            user_name: Optional user name for logging

        Returns:
            Dict with delivery status

        Raises:
            aiosmtplib.SMTPException: If email sending fails
        """
        try:
            self.logger.info(
                f"Sending email to {user_name or to_email}: {subject}"
            )

            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email

            # Add plain text part
            text_part = MIMEText(body_text, "plain")
            message.attach(text_part)

            # Add HTML part if provided
            if body_html:
                html_part = MIMEText(body_html, "html")
                message.attach(html_part)

            # Send email
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_username,
                password=self.smtp_password,
                use_tls=self.use_tls
            )

            self.logger.info(
                f"Email sent successfully to {user_name or to_email}"
            )

            return {
                "success": True,
                "channel": "email",
                "to": to_email,
                "subject": subject,
                "provider": "smtp"
            }

        except aiosmtplib.SMTPException as e:
            self.logger.error(
                f"Failed to send email to {user_name or to_email}: {e}"
            )
            return {
                "success": False,
                "channel": "email",
                "to": to_email,
                "error": str(e),
                "provider": "smtp"
            }

        except Exception as e:
            self.logger.error(
                f"Unexpected error sending email to {user_name or to_email}: {e}"
            )
            return {
                "success": False,
                "channel": "email",
                "to": to_email,
                "error": str(e),
                "provider": "smtp"
            }

    def format_bus_delay_email(
        self,
        user_name: str,
        bus_name: str,
        delay_minutes: int,
        new_eta: str,
        pickup_location: str
    ) -> tuple[str, str]:
        """
        Format bus delay email (subject and body).

        Args:
            user_name: Recipient name
            bus_name: Bus route name
            delay_minutes: Delay in minutes
            new_eta: New estimated arrival time
            pickup_location: Pickup location

        Returns:
            Tuple of (subject, html_body)
        """
        subject = f"🚌 Bus Delay Alert: {bus_name} - {delay_minutes} min delay"

        html_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #d32f2f;">Bus Delay Alert</h2>
            <p>Hello {user_name},</p>
            <p>We wanted to inform you that <strong>{bus_name}</strong> is experiencing a delay.</p>

            <div style="background-color: #fff3e0; padding: 15px; border-left: 4px solid #ff9800; margin: 20px 0;">
              <p style="margin: 5px 0;"><strong>Delay:</strong> {delay_minutes} minutes</p>
              <p style="margin: 5px 0;"><strong>New ETA:</strong> {new_eta}</p>
              <p style="margin: 5px 0;"><strong>Pickup:</strong> {pickup_location}</p>
            </div>

            <p>We apologize for any inconvenience and appreciate your patience.</p>

            <p style="color: #757575; font-size: 12px; margin-top: 30px;">
              ChurchFlow Notifications<br>
              This is an automated message. Please do not reply to this email.
            </p>
          </body>
        </html>
        """

        return subject, html_body

    def format_conference_reminder_email(
        self,
        user_name: str,
        conference_name: str,
        start_date: str,
        venue: str,
        hours_before: int
    ) -> tuple[str, str]:
        """
        Format conference reminder email (subject and body).

        Args:
            user_name: Recipient name
            conference_name: Conference name
            start_date: Conference start date
            venue: Conference venue
            hours_before: Hours before conference

        Returns:
            Tuple of (subject, html_body)
        """
        timing = f"{hours_before} hours" if hours_before >= 24 else f"{hours_before} hours"
        if hours_before >= 24:
            days = hours_before // 24
            timing = f"{days} {'day' if days == 1 else 'days'}"

        subject = f"📅 Reminder: {conference_name} starts in {timing}"

        html_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #1976d2;">Conference Reminder</h2>
            <p>Hello {user_name},</p>
            <p>This is a friendly reminder that <strong>{conference_name}</strong> is starting soon!</p>

            <div style="background-color: #e3f2fd; padding: 15px; border-left: 4px solid #2196f3; margin: 20px 0;">
              <p style="margin: 5px 0;"><strong>Event:</strong> {conference_name}</p>
              <p style="margin: 5px 0;"><strong>Date:</strong> {start_date}</p>
              <p style="margin: 5px 0;"><strong>Venue:</strong> {venue}</p>
              <p style="margin: 5px 0;"><strong>Time Until Start:</strong> {timing}</p>
            </div>

            <p>We look forward to seeing you there!</p>

            <p style="color: #757575; font-size: 12px; margin-top: 30px;">
              ChurchFlow Notifications<br>
              This is an automated message. Please do not reply to this email.
            </p>
          </body>
        </html>
        """

        return subject, html_body
