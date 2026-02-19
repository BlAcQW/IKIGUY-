"""
Notification Service for Bookings

Handles email and SMS notifications for booking-related events.
"""

import sys
import os
from datetime import datetime
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

from app.models.booking import Booking, BookingStatus
from app.models.agent import Agent

logger = logging.getLogger(__name__)


class EmailIntegration:
    """Mock Email Integration for Standalone Mode."""
    
    def __init__(self, config=None):
        self.config = config
        
    async def send_email(self, to, subject, body, html_body=None):
        """Log email instead of sending."""
        logger.info(f"EMAIL SIMULATION [To: {to}] [Subject: {subject}]")
        return {"success": True, "message": "Email simulated"}


class BookingNotificationService:
    """
    Service for sending booking-related notifications via email and SMS.
    """

    def __init__(self, db: AsyncIOMotorDatabase, email_config: Optional[Dict[str, Any]] = None):
        """
        Initialize notification service.

        Args:
            db: MongoDB database instance
            email_config: Optional email configuration
        """
        self.db = db
        # Use mock email service for standalone mode
        self.email_service = EmailIntegration(email_config)


    async def send_booking_confirmation(
        self,
        booking: Booking,
        property_title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send booking confirmation email to customer.

        Args:
            booking: Booking object
            property_title: Optional property title

        Returns:
            Result of email send operation
        """
        if not booking.contact_email:
            logger.warning(f"No email for booking {booking.id}, skipping confirmation")
            return {"success": False, "error": "No email address"}

        # Fetch property details if not provided
        if not property_title:
            property = await self.db["properties"].find_one({"id": booking.property_id})
            property_title = property.get("title", "Property") if property else "Property"

        # Format date and time
        booking_date = booking.scheduled_at.strftime("%A, %B %d, %Y")
        booking_time = booking.scheduled_at.strftime("%I:%M %p")
        duration_display = f"{booking.duration_minutes} minutes"

        # Create email content
        subject = f"Booking Confirmation - {property_title}"

        # Plain text version
        body = f"""
Dear {booking.contact_name},

Your property tour booking has been confirmed!

Booking Details:
- Property: {property_title}
- Date: {booking_date}
- Time: {booking_time}
- Duration: {duration_display}
- Type: {booking.booking_type.replace('-', ' ').title()}

Booking ID: {booking.id}

{f"Meeting Link: {booking.meeting_link}" if booking.meeting_link else ""}
{f"Notes: {booking.notes}" if booking.notes else ""}

We'll send you reminder notifications before your scheduled tour.

If you need to reschedule or cancel, please contact us as soon as possible.

Thank you for your interest!

Best regards,
The EstateFlow Team
"""

        # HTML version
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 28px;">Booking Confirmed!</h1>
    </div>

    <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
        <p style="font-size: 16px; margin-bottom: 20px;">Dear {booking.contact_name},</p>

        <p style="font-size: 16px; margin-bottom: 20px;">
            Your property tour booking has been confirmed. We look forward to showing you around!
        </p>

        <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #667eea;">
            <h2 style="color: #667eea; margin-top: 0; font-size: 20px;">Booking Details</h2>

            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 10px 0; border-bottom: 1px solid #eee;"><strong>Property:</strong></td>
                    <td style="padding: 10px 0; border-bottom: 1px solid #eee;">{property_title}</td>
                </tr>
                <tr>
                    <td style="padding: 10px 0; border-bottom: 1px solid #eee;"><strong>Date:</strong></td>
                    <td style="padding: 10px 0; border-bottom: 1px solid #eee;">{booking_date}</td>
                </tr>
                <tr>
                    <td style="padding: 10px 0; border-bottom: 1px solid #eee;"><strong>Time:</strong></td>
                    <td style="padding: 10px 0; border-bottom: 1px solid #eee;">{booking_time}</td>
                </tr>
                <tr>
                    <td style="padding: 10px 0; border-bottom: 1px solid #eee;"><strong>Duration:</strong></td>
                    <td style="padding: 10px 0; border-bottom: 1px solid #eee;">{duration_display}</td>
                </tr>
                <tr>
                    <td style="padding: 10px 0; border-bottom: 1px solid #eee;"><strong>Type:</strong></td>
                    <td style="padding: 10px 0; border-bottom: 1px solid #eee;">{booking.booking_type.replace('-', ' ').title()}</td>
                </tr>
                <tr>
                    <td style="padding: 10px 0;"><strong>Booking ID:</strong></td>
                    <td style="padding: 10px 0; font-family: monospace; color: #667eea;">{booking.id}</td>
                </tr>
            </table>
        </div>

        {f'<div style="background: #e3f2fd; padding: 15px; border-radius: 8px; margin: 20px 0;"><strong>🔗 Meeting Link:</strong><br/><a href="{booking.meeting_link}" style="color: #1976d2; word-break: break-all;">{booking.meeting_link}</a></div>' if booking.meeting_link else ''}

        {f'<div style="background: #fff3e0; padding: 15px; border-radius: 8px; margin: 20px 0;"><strong>📝 Notes:</strong><br/>{booking.notes}</div>' if booking.notes else ''}

        <div style="background: #f0f0f0; padding: 15px; border-radius: 8px; margin: 20px 0; text-align: center;">
            <p style="margin: 0; color: #666;">
                We'll send you reminder notifications before your scheduled tour.
            </p>
        </div>

        <p style="font-size: 14px; color: #666; margin-top: 30px;">
            If you need to reschedule or cancel, please contact us as soon as possible.
        </p>

        <p style="font-size: 16px; margin-top: 20px;">
            Thank you for your interest!<br/>
            <strong>The EstateFlow Team</strong>
        </p>
    </div>

    <div style="text-align: center; padding: 20px; font-size: 12px; color: #999;">
        <p>This is an automated message from EstateFlow.</p>
        <p>© 2025 EstateFlow. All rights reserved.</p>
    </div>
</body>
</html>
"""

        # Send email
        result = await self.email_service.send_email(
            to=booking.contact_email,
            subject=subject,
            body=body,
            html_body=html_body
        )

        logger.info(f"Booking confirmation sent for {booking.id}: {result.get('success')}")
        return result

    async def send_agent_notification(
        self,
        booking: Booking,
        agent: Agent,
        property_title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send new booking notification to assigned agent.

        Args:
            booking: Booking object
            agent: Agent object
            property_title: Optional property title

        Returns:
            Result of email send operation
        """
        if not agent.email:
            logger.warning(f"No email for agent {agent.id}, skipping notification")
            return {"success": False, "error": "No email address"}

        # Fetch property details if not provided
        if not property_title:
            property = await self.db["properties"].find_one({"id": booking.property_id})
            property_title = property.get("title", "Property") if property else "Property"

        # Format date and time
        booking_date = booking.scheduled_at.strftime("%A, %B %d, %Y")
        booking_time = booking.scheduled_at.strftime("%I:%M %p")
        duration_display = f"{booking.duration_minutes} minutes"

        # Create email content
        subject = f"New Booking Assignment - {property_title}"

        # Plain text version
        body = f"""
Dear {agent.first_name},

You have been assigned a new property tour booking!

Booking Details:
- Property: {property_title}
- Client: {booking.contact_name}
- Email: {booking.contact_email or 'Not provided'}
- Phone: {booking.contact_phone or 'Not provided'}
- Date: {booking_date}
- Time: {booking_time}
- Duration: {duration_display}
- Type: {booking.booking_type.replace('-', ' ').title()}

Booking ID: {booking.id}

{f"Client Notes: {booking.notes}" if booking.notes else ""}

Please review this booking and reach out to the client if needed.

Best regards,
The EstateFlow Team
"""

        # HTML version
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 28px;">New Booking Assignment</h1>
    </div>

    <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
        <p style="font-size: 16px; margin-bottom: 20px;">Dear {agent.first_name},</p>

        <p style="font-size: 16px; margin-bottom: 20px;">
            You have been assigned a new property tour booking. Please review the details below.
        </p>

        <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #11998e;">
            <h2 style="color: #11998e; margin-top: 0; font-size: 20px;">Booking Details</h2>

            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 10px 0; border-bottom: 1px solid #eee;"><strong>Property:</strong></td>
                    <td style="padding: 10px 0; border-bottom: 1px solid #eee;">{property_title}</td>
                </tr>
                <tr>
                    <td style="padding: 10px 0; border-bottom: 1px solid #eee;"><strong>Client:</strong></td>
                    <td style="padding: 10px 0; border-bottom: 1px solid #eee;">{booking.contact_name}</td>
                </tr>
                <tr>
                    <td style="padding: 10px 0; border-bottom: 1px solid #eee;"><strong>Email:</strong></td>
                    <td style="padding: 10px 0; border-bottom: 1px solid #eee;">{booking.contact_email or 'Not provided'}</td>
                </tr>
                <tr>
                    <td style="padding: 10px 0; border-bottom: 1px solid #eee;"><strong>Phone:</strong></td>
                    <td style="padding: 10px 0; border-bottom: 1px solid #eee;">{booking.contact_phone or 'Not provided'}</td>
                </tr>
                <tr>
                    <td style="padding: 10px 0; border-bottom: 1px solid #eee;"><strong>Date:</strong></td>
                    <td style="padding: 10px 0; border-bottom: 1px solid #eee;">{booking_date}</td>
                </tr>
                <tr>
                    <td style="padding: 10px 0; border-bottom: 1px solid #eee;"><strong>Time:</strong></td>
                    <td style="padding: 10px 0; border-bottom: 1px solid #eee;">{booking_time}</td>
                </tr>
                <tr>
                    <td style="padding: 10px 0; border-bottom: 1px solid #eee;"><strong>Duration:</strong></td>
                    <td style="padding: 10px 0; border-bottom: 1px solid #eee;">{duration_display}</td>
                </tr>
                <tr>
                    <td style="padding: 10px 0; border-bottom: 1px solid #eee;"><strong>Type:</strong></td>
                    <td style="padding: 10px 0; border-bottom: 1px solid #eee;">{booking.booking_type.replace('-', ' ').title()}</td>
                </tr>
                <tr>
                    <td style="padding: 10px 0;"><strong>Booking ID:</strong></td>
                    <td style="padding: 10px 0; font-family: monospace; color: #11998e;">{booking.id}</td>
                </tr>
            </table>
        </div>

        {f'<div style="background: #fff3e0; padding: 15px; border-radius: 8px; margin: 20px 0;"><strong>📝 Client Notes:</strong><br/>{booking.notes}</div>' if booking.notes else ''}

        <div style="background: #e8f5e9; padding: 15px; border-radius: 8px; margin: 20px 0; text-align: center;">
            <p style="margin: 0; color: #2e7d32;">
                <strong>Action Required:</strong> Please confirm this booking and reach out to the client if needed.
            </p>
        </div>

        <p style="font-size: 16px; margin-top: 20px;">
            Best regards,<br/>
            <strong>The EstateFlow Team</strong>
        </p>
    </div>

    <div style="text-align: center; padding: 20px; font-size: 12px; color: #999;">
        <p>This is an automated message from EstateFlow.</p>
        <p>© 2025 EstateFlow. All rights reserved.</p>
    </div>
</body>
</html>
"""

        # Send email
        result = await self.email_service.send_email(
            to=agent.email,
            subject=subject,
            body=body,
            html_body=html_body
        )

        logger.info(f"Agent notification sent for booking {booking.id} to {agent.email}: {result.get('success')}")
        return result

    async def send_reminder(
        self,
        booking: Booking,
        reminder_type: str,
        property_title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send reminder email for an upcoming booking.

        Args:
            booking: Booking object
            reminder_type: Type of reminder ('24h', '1h', or 'post-tour')
            property_title: Optional property title

        Returns:
            Result of email send operation
        """
        if not booking.contact_email:
            logger.warning(f"No email for booking {booking.id}, skipping reminder")
            return {"success": False, "error": "No email address"}

        # Fetch property details if not provided
        if not property_title:
            property = await self.db["properties"].find_one({"id": booking.property_id})
            property_title = property.get("title", "Property") if property else "Property"

        # Format date and time
        booking_date = booking.scheduled_at.strftime("%A, %B %d, %Y")
        booking_time = booking.scheduled_at.strftime("%I:%M %p")

        # Customize content based on reminder type
        if reminder_type == "24h":
            subject = f"Reminder: Property Tour Tomorrow - {property_title}"
            greeting = "This is a reminder that your property tour is scheduled for tomorrow!"
            time_info = "tomorrow"
        elif reminder_type == "1h":
            subject = f"Reminder: Property Tour in 1 Hour - {property_title}"
            greeting = "Your property tour is starting in 1 hour!"
            time_info = "in 1 hour"
        elif reminder_type == "post-tour":
            subject = f"How Was Your Tour? - {property_title}"
            greeting = "Thank you for touring the property!"
            time_info = "earlier today"
        else:
            subject = f"Booking Reminder - {property_title}"
            greeting = "This is a reminder about your property tour."
            time_info = "soon"

        # Plain text version
        body = f"""
Dear {booking.contact_name},

{greeting}

Tour Details:
- Property: {property_title}
- Date: {booking_date}
- Time: {booking_time}
- Type: {booking.booking_type.replace('-', ' ').title()}

{f"Meeting Link: {booking.meeting_link}" if booking.meeting_link else ""}

{"We hope you had a great experience! We'd love to hear your feedback." if reminder_type == "post-tour" else "Please arrive on time. If you need to reschedule, contact us as soon as possible."}

Best regards,
The EstateFlow Team
"""

        # HTML version
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 28px;">{"Tour Feedback" if reminder_type == "post-tour" else "Tour Reminder"}</h1>
    </div>

    <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
        <p style="font-size: 16px; margin-bottom: 20px;">Dear {booking.contact_name},</p>

        <p style="font-size: 18px; font-weight: bold; margin-bottom: 20px; color: #f5576c;">
            {greeting}
        </p>

        <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #f5576c;">
            <h2 style="color: #f5576c; margin-top: 0; font-size: 20px;">Tour Details</h2>

            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 10px 0; border-bottom: 1px solid #eee;"><strong>Property:</strong></td>
                    <td style="padding: 10px 0; border-bottom: 1px solid #eee;">{property_title}</td>
                </tr>
                <tr>
                    <td style="padding: 10px 0; border-bottom: 1px solid #eee;"><strong>Date:</strong></td>
                    <td style="padding: 10px 0; border-bottom: 1px solid #eee;">{booking_date}</td>
                </tr>
                <tr>
                    <td style="padding: 10px 0; border-bottom: 1px solid #eee;"><strong>Time:</strong></td>
                    <td style="padding: 10px 0; border-bottom: 1px solid #eee;">{booking_time}</td>
                </tr>
                <tr>
                    <td style="padding: 10px 0;"><strong>Type:</strong></td>
                    <td style="padding: 10px 0;">{booking.booking_type.replace('-', ' ').title()}</td>
                </tr>
            </table>
        </div>

        {f'<div style="background: #e3f2fd; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center;"><strong style="font-size: 18px;">🔗 Meeting Link</strong><br/><br/><a href="{booking.meeting_link}" style="display: inline-block; background: #1976d2; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;">Join Virtual Tour</a></div>' if booking.meeting_link and reminder_type != "post-tour" else ''}

        <p style="font-size: 16px; margin-top: 20px;">
            {"We hope you had a great experience! We'd love to hear your feedback and answer any questions you may have." if reminder_type == "post-tour" else "Please arrive on time. If you need to reschedule, contact us as soon as possible."}
        </p>

        <p style="font-size: 16px; margin-top: 20px;">
            Best regards,<br/>
            <strong>The EstateFlow Team</strong>
        </p>
    </div>

    <div style="text-align: center; padding: 20px; font-size: 12px; color: #999;">
        <p>This is an automated reminder from EstateFlow.</p>
        <p>© 2025 EstateFlow. All rights reserved.</p>
    </div>
</body>
</html>
"""

        # Send email
        result = await self.email_service.send_email(
            to=booking.contact_email,
            subject=subject,
            body=body,
            html_body=html_body
        )

        logger.info(f"Reminder ({reminder_type}) sent for booking {booking.id}: {result.get('success')}")
        return result

    async def send_booking_status_update(
        self,
        booking: Booking,
        old_status: BookingStatus,
        new_status: BookingStatus,
        property_title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send status update email when booking status changes.

        Args:
            booking: Booking object
            old_status: Previous status
            new_status: New status
            property_title: Optional property title

        Returns:
            Result of email send operation
        """
        if not booking.contact_email:
            logger.warning(f"No email for booking {booking.id}, skipping status update")
            return {"success": False, "error": "No email address"}

        # Fetch property details if not provided
        if not property_title:
            property = await self.db["properties"].find_one({"id": booking.property_id})
            property_title = property.get("title", "Property") if property else "Property"

        status_messages = {
            BookingStatus.CONFIRMED: {
                "title": "Booking Confirmed",
                "message": "Great news! Your booking has been confirmed by our team.",
                "color": "#4caf50"
            },
            BookingStatus.CANCELLED: {
                "title": "Booking Cancelled",
                "message": "Your booking has been cancelled. If this was a mistake, please contact us.",
                "color": "#f44336"
            },
            BookingStatus.RESCHEDULED: {
                "title": "Booking Rescheduled",
                "message": "Your booking has been rescheduled to a new date and time.",
                "color": "#ff9800"
            },
            BookingStatus.COMPLETED: {
                "title": "Tour Completed",
                "message": "Thank you for touring the property! We hope you had a great experience.",
                "color": "#2196f3"
            }
        }

        status_info = status_messages.get(new_status, {
            "title": "Booking Status Update",
            "message": f"Your booking status has been updated to {new_status.value}.",
            "color": "#9c27b0"
        })

        subject = f"{status_info['title']} - {property_title}"

        # Plain text version
        body = f"""
Dear {booking.contact_name},

{status_info['message']}

Booking ID: {booking.id}
Property: {property_title}
Status: {new_status.value.upper()}

If you have any questions, please don't hesitate to contact us.

Best regards,
The EstateFlow Team
"""

        # HTML version
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: {status_info['color']}; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 28px;">{status_info['title']}</h1>
    </div>

    <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
        <p style="font-size: 16px; margin-bottom: 20px;">Dear {booking.contact_name},</p>

        <p style="font-size: 16px; margin-bottom: 20px;">
            {status_info['message']}
        </p>

        <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid {status_info['color']};">
            <p><strong>Booking ID:</strong> <span style="font-family: monospace; color: {status_info['color']};">{booking.id}</span></p>
            <p><strong>Property:</strong> {property_title}</p>
            <p><strong>Status:</strong> <span style="color: {status_info['color']}; font-weight: bold;">{new_status.value.upper()}</span></p>
        </div>

        <p style="font-size: 16px; margin-top: 20px;">
            If you have any questions, please don't hesitate to contact us.
        </p>

        <p style="font-size: 16px; margin-top: 20px;">
            Best regards,<br/>
            <strong>The EstateFlow Team</strong>
        </p>
    </div>

    <div style="text-align: center; padding: 20px; font-size: 12px; color: #999;">
        <p>This is an automated message from EstateFlow.</p>
        <p>© 2025 EstateFlow. All rights reserved.</p>
    </div>
</body>
</html>
"""

        # Send email
        result = await self.email_service.send_email(
            to=booking.contact_email,
            subject=subject,
            body=body,
            html_body=html_body
        )

        logger.info(f"Status update email sent for booking {booking.id}: {result.get('success')}")
        return result
