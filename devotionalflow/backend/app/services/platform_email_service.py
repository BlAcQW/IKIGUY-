"""
Platform email service for DevotionalFlow.

Handles invitation emails using the shared UnifiedEmailService.
Provides HTML and plain text templates for professional email delivery.
"""

import logging
import sys
from typing import Dict, Any
from datetime import datetime

# Add shared path for unified email service
sys.path.insert(0, "/opt/kasaai")

from app.config import settings

logger = logging.getLogger(__name__)

# Email constants
INVITE_EMAIL_SUBJECT = "You're Invited to Join FreshManna"
INVITE_RESEND_SUBJECT = "Reminder: Your FreshManna Invitation"


def get_invite_email_html(
    invitee_email: str,
    inviter_name: str,
    invite_token: str,
    role: str,
    custom_message: str = None,
    expires_at: datetime = None,
    is_resend: bool = False
) -> str:
    """
    Generate HTML email body for platform invitation.

    Args:
        invitee_email: Email address of the invitee
        inviter_name: Name of the person sending the invite
        invite_token: Unique invitation token
        role: Role being assigned (user/admin)
        custom_message: Optional custom message from inviter
        expires_at: Invitation expiry datetime
        is_resend: Whether this is a reminder email

    Returns:
        str: HTML email body
    """
    signup_url = f"{settings.FRONTEND_URL}/signup?invite={invite_token}"
    expiry_str = expires_at.strftime("%B %d, %Y") if expires_at else "7 days"
    role_display = "Administrator" if role == "admin" else "Member"

    # Header based on resend status
    header_text = "Reminder: You're Invited!" if is_resend else "You're Invited!"
    intro_text = (
        f"This is a friendly reminder that <strong>{inviter_name}</strong> invited you"
        if is_resend
        else f"<strong>{inviter_name}</strong> has invited you"
    )

    custom_message_html = ""
    if custom_message:
        custom_message_html = f'''
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #4CAF50;">
            <p style="margin: 0; font-style: italic;">"{custom_message}"</p>
            <p style="margin: 10px 0 0 0; font-size: 14px; color: #666;">- {inviter_name}</p>
        </div>
        '''

    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Join FreshManna</title>
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">

        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #4CAF50; margin: 0; font-size: 32px;">FreshManna</h1>
            <p style="color: #666; font-size: 14px; margin: 5px 0 0 0;">Daily Devotional Platform</p>
        </div>

        <div style="background-color: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h2 style="color: #333; margin-top: 0; font-size: 24px;">{header_text}</h2>

            <p style="font-size: 16px;">Hi there,</p>

            <p style="font-size: 16px;">{intro_text} to join <strong>FreshManna</strong> as a <strong>{role_display}</strong>.</p>

            {custom_message_html}

            <p style="font-size: 16px;">FreshManna is a Holy Spirit-inspired devotional platform where you can:</p>
            <ul style="color: #555; font-size: 15px; line-height: 1.8;">
                <li>Read daily devotionals from inspiring authors</li>
                <li>Share your own spiritual insights</li>
                <li>Connect with a community of believers</li>
                <li>Track your spiritual reading journey</li>
            </ul>

            <div style="text-align: center; margin: 30px 0;">
                <a href="{signup_url}"
                   style="display: inline-block; background-color: #4CAF50; color: white; padding: 15px 40px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 16px; box-shadow: 0 2px 5px rgba(76,175,80,0.3);">
                    Accept Invitation & Sign Up
                </a>
            </div>

            <p style="font-size: 14px; color: #666; text-align: center;">
                This invitation will expire on <strong>{expiry_str}</strong>.
            </p>

            <hr style="border: none; border-top: 1px solid #eee; margin: 25px 0;">

            <p style="font-size: 12px; color: #999;">
                If you can't click the button, copy and paste this link into your browser:<br>
                <a href="{signup_url}" style="color: #4CAF50; word-break: break-all;">{signup_url}</a>
            </p>
        </div>

        <div style="text-align: center; margin-top: 30px; padding-top: 20px;">
            <p style="font-size: 12px; color: #999;">
                This email was sent by FreshManna (DevotionalFlow).<br>
                If you didn't expect this invitation, you can safely ignore this email.
            </p>
            <p style="font-size: 11px; color: #bbb; margin-top: 10px;">
                &copy; {datetime.utcnow().year} AI Labs Africa. All rights reserved.
            </p>
        </div>

    </body>
    </html>
    '''


def get_invite_email_text(
    invitee_email: str,
    inviter_name: str,
    invite_token: str,
    role: str,
    custom_message: str = None,
    expires_at: datetime = None,
    is_resend: bool = False
) -> str:
    """
    Generate plain text email body for platform invitation.

    Args:
        invitee_email: Email address of the invitee
        inviter_name: Name of the person sending the invite
        invite_token: Unique invitation token
        role: Role being assigned
        custom_message: Optional custom message
        expires_at: Invitation expiry datetime
        is_resend: Whether this is a reminder email

    Returns:
        str: Plain text email body
    """
    signup_url = f"{settings.FRONTEND_URL}/signup?invite={invite_token}"
    expiry_str = expires_at.strftime("%B %d, %Y") if expires_at else "7 days"
    role_display = "Administrator" if role == "admin" else "Member"

    header = "Reminder: You're Invited to Join FreshManna!" if is_resend else "You're Invited to Join FreshManna!"
    intro = (
        f"This is a friendly reminder that {inviter_name} invited you"
        if is_resend
        else f"{inviter_name} has invited you"
    )

    message_section = ""
    if custom_message:
        message_section = f'''

Message from {inviter_name}:
"{custom_message}"
'''

    return f'''
{header}

Hi there,

{intro} to join FreshManna as a {role_display}.
{message_section}
FreshManna is a Holy Spirit-inspired devotional platform where you can:
- Read daily devotionals from inspiring authors
- Share your own spiritual insights
- Connect with a community of believers
- Track your spiritual reading journey

Accept your invitation and sign up here:
{signup_url}

This invitation will expire on {expiry_str}.

---
If you didn't expect this invitation, you can safely ignore this email.

FreshManna (DevotionalFlow)
AI Labs Africa
'''


async def send_invite_email(
    to_email: str,
    inviter_name: str,
    invite_token: str,
    role: str = "user",
    custom_message: str = None,
    expires_at: datetime = None,
    is_resend: bool = False
) -> Dict[str, Any]:
    """
    Send platform invitation email using UnifiedEmailService.

    Args:
        to_email: Recipient email address
        inviter_name: Name of the person sending the invite
        invite_token: Unique invitation token
        role: Role being assigned (user/admin)
        custom_message: Optional custom message
        expires_at: Invitation expiry datetime
        is_resend: Whether this is a reminder/resend

    Returns:
        Dict with success status and details:
        - success: bool
        - message_id: str (if successful)
        - provider: str (smtp, resend, etc.)
        - error: str (if failed)
    """
    try:
        # Import shared email service
        from apps.shared.services.unified_email_service import get_email_service

        email_service = get_email_service()

        html_body = get_invite_email_html(
            invitee_email=to_email,
            inviter_name=inviter_name,
            invite_token=invite_token,
            role=role,
            custom_message=custom_message,
            expires_at=expires_at,
            is_resend=is_resend
        )

        text_body = get_invite_email_text(
            invitee_email=to_email,
            inviter_name=inviter_name,
            invite_token=invite_token,
            role=role,
            custom_message=custom_message,
            expires_at=expires_at,
            is_resend=is_resend
        )

        subject = INVITE_RESEND_SUBJECT if is_resend else INVITE_EMAIL_SUBJECT

        result = await email_service.send_email(
            to=to_email,
            subject=subject,
            body=text_body,
            html_body=html_body,
            from_email="noreply@ailabsafrica.com",
            from_name="FreshManna"
        )

        if result.get("success"):
            logger.info(f"Invitation email sent successfully to {to_email}")
        else:
            logger.error(f"Failed to send invitation email to {to_email}: {result.get('error')}")

        return result

    except ImportError as e:
        logger.error(f"Failed to import email service: {e}")
        return {
            "success": False,
            "error": f"Email service not available: {str(e)}",
            "provider": "error"
        }
    except Exception as e:
        logger.error(f"Error sending invitation email to {to_email}: {e}")
        return {
            "success": False,
            "error": str(e),
            "provider": "error"
        }


async def send_welcome_email(
    to_email: str,
    user_name: str,
    role: str = "user"
) -> Dict[str, Any]:
    """
    Send welcome email after successful signup.

    Args:
        to_email: User's email address
        user_name: User's display name
        role: User's role

    Returns:
        Dict with success status
    """
    try:
        from apps.shared.services.unified_email_service import get_email_service

        email_service = get_email_service()
        role_display = "Administrator" if role == "admin" else "member"

        html_body = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Welcome to FreshManna</title>
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #4CAF50;">Welcome to FreshManna!</h1>
            </div>

            <p>Hi {user_name},</p>

            <p>Welcome to FreshManna! Your account has been created successfully as a {role_display}.</p>

            <p>You can now:</p>
            <ul>
                <li>Read daily devotionals</li>
                <li>Like and comment on devotionals</li>
                <li>Track your reading streaks</li>
                <li>Join Bible study groups</li>
            </ul>

            <div style="text-align: center; margin: 30px 0;">
                <a href="{settings.FRONTEND_URL}/login"
                   style="display: inline-block; background-color: #4CAF50; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                    Start Reading
                </a>
            </div>

            <p>Blessings,<br>The FreshManna Team</p>
        </body>
        </html>
        '''

        text_body = f'''
Welcome to FreshManna!

Hi {user_name},

Welcome to FreshManna! Your account has been created successfully as a {role_display}.

You can now:
- Read daily devotionals
- Like and comment on devotionals
- Track your reading streaks
- Join Bible study groups

Start reading: {settings.FRONTEND_URL}/login

Blessings,
The FreshManna Team
'''

        result = await email_service.send_email(
            to=to_email,
            subject="Welcome to FreshManna!",
            body=text_body,
            html_body=html_body,
            from_email="noreply@ailabsafrica.com",
            from_name="FreshManna"
        )

        if result.get("success"):
            logger.info(f"Welcome email sent to {to_email}")
        else:
            logger.warning(f"Failed to send welcome email to {to_email}: {result.get('error')}")

        return result

    except Exception as e:
        logger.error(f"Error sending welcome email to {to_email}: {e}")
        return {"success": False, "error": str(e)}
