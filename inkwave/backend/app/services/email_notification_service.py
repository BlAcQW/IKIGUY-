"""
Email Notification Service for InkWave.

Handles sending email notifications for payments, transactions, and user events.

Author: KasaAI Team
Date: 2025-11-27
"""

import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime
from decimal import Decimal

from apps.shared.integration.resend import (
    ResendIntegration,
    ResendConfig,
    ResendEmail,
)

logger = logging.getLogger(__name__)


class InkWaveEmailService:
    """
    Email notification service for InkWave.

    Sends transactional emails for:
    - Payment confirmations
    - Purchase receipts
    - Low balance alerts
    - Welcome emails
    """

    def __init__(self, resend_api_key: Optional[str] = None):
        """
        Initialize email service.

        Args:
            resend_api_key: Resend API key (defaults to RESEND_API_KEY env var)
        """
        self.api_key = resend_api_key or os.getenv("RESEND_API_KEY")
        self.from_email = os.getenv("EMAIL_FROM", "InkWave <inkwave@ailabsafrica.com>")
        self.support_email = os.getenv("SUPPORT_EMAIL", "support@ailabsafrica.com")
        self.initialized = False
        self.resend: Optional[ResendIntegration] = None

        if self.api_key:
            try:
                config = ResendConfig(api_key=self.api_key)
                self.resend = ResendIntegration(config)
                self.initialized = True
                logger.info("InkWave Email Service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize email service: {e}")
        else:
            logger.warning("RESEND_API_KEY not configured - email notifications disabled")

    async def send_payment_confirmation(
        self,
        to_email: str,
        customer_name: str,
        amount: float,
        currency: str,
        order_id: str,
        transaction_id: str,
        item_description: str,
        payment_method: Optional[str] = None,
        card_last4: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send payment confirmation email.

        Args:
            to_email: Customer email address
            customer_name: Customer name
            amount: Payment amount
            currency: Currency code (e.g., GHS, USD)
            order_id: Order ID
            transaction_id: Transaction ID
            item_description: Description of purchased item
            payment_method: Payment method used
            card_last4: Last 4 digits of card (if applicable)

        Returns:
            Dict with success status and message ID
        """
        if not self.initialized:
            logger.warning("Email service not initialized - skipping payment confirmation email")
            return {"success": False, "error": "Email service not configured"}

        try:
            # Format amount
            formatted_amount = f"{currency} {amount:.2f}"

            # Build email content
            subject = f"Payment Confirmed - {formatted_amount}"

            # Payment method display
            payment_info = payment_method or "Card"
            if card_last4:
                payment_info = f"Card ending in {card_last4}"

            # HTML email content
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Payment Confirmation</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .header h1 {{ margin: 0; font-size: 24px; }}
                    .content {{ background: #fff; padding: 30px; border: 1px solid #e5e7eb; border-top: none; }}
                    .success-badge {{ background: #10b981; color: white; padding: 8px 16px; border-radius: 20px; font-size: 14px; display: inline-block; margin-bottom: 20px; }}
                    .details {{ background: #f9fafb; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                    .details-row {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #e5e7eb; }}
                    .details-row:last-child {{ border-bottom: none; }}
                    .details-label {{ color: #6b7280; }}
                    .details-value {{ font-weight: 600; color: #111827; }}
                    .amount {{ font-size: 28px; font-weight: bold; color: #7c3aed; text-align: center; margin: 20px 0; }}
                    .footer {{ background: #f9fafb; padding: 20px; text-align: center; border-radius: 0 0 10px 10px; font-size: 12px; color: #6b7280; }}
                    .footer a {{ color: #7c3aed; text-decoration: none; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>📚 InkWave</h1>
                        <p>Your AI-Powered Audiobook Companion</p>
                    </div>
                    <div class="content">
                        <span class="success-badge">✓ Payment Successful</span>
                        <h2>Thank you for your purchase, {customer_name}!</h2>
                        <p>Your payment has been processed successfully. Here are your transaction details:</p>

                        <div class="amount">{formatted_amount}</div>

                        <div class="details">
                            <div class="details-row">
                                <span class="details-label">Order ID</span>
                                <span class="details-value">{order_id}</span>
                            </div>
                            <div class="details-row">
                                <span class="details-label">Transaction ID</span>
                                <span class="details-value">{transaction_id}</span>
                            </div>
                            <div class="details-row">
                                <span class="details-label">Item</span>
                                <span class="details-value">{item_description}</span>
                            </div>
                            <div class="details-row">
                                <span class="details-label">Payment Method</span>
                                <span class="details-value">{payment_info}</span>
                            </div>
                            <div class="details-row">
                                <span class="details-label">Date</span>
                                <span class="details-value">{datetime.utcnow().strftime('%B %d, %Y at %H:%M UTC')}</span>
                            </div>
                        </div>

                        <p>You can access your purchase immediately in the InkWave app. Happy reading! 📖</p>

                        <p style="margin-top: 30px;">
                            If you have any questions about this transaction, please contact us at
                            <a href="mailto:{self.support_email}" style="color: #7c3aed;">{self.support_email}</a>
                        </p>
                    </div>
                    <div class="footer">
                        <p>© {datetime.utcnow().year} InkWave by AI Labs Africa. All rights reserved.</p>
                        <p>
                            <a href="https://inkwave.ailabsafrica.com">Visit InkWave</a> |
                            <a href="mailto:{self.support_email}">Contact Support</a>
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """

            # Plain text version
            text_content = f"""
Payment Confirmed - {formatted_amount}

Thank you for your purchase, {customer_name}!

Your payment has been processed successfully.

Transaction Details:
- Order ID: {order_id}
- Transaction ID: {transaction_id}
- Item: {item_description}
- Amount: {formatted_amount}
- Payment Method: {payment_info}
- Date: {datetime.utcnow().strftime('%B %d, %Y at %H:%M UTC')}

You can access your purchase immediately in the InkWave app.

If you have any questions, contact us at {self.support_email}

© {datetime.utcnow().year} InkWave by AI Labs Africa
            """

            # Create and send email
            email = ResendEmail(
                from_=self.from_email,
                to=[to_email],
                subject=subject,
                html=html_content,
                text=text_content,
                tags=[{"name": "type", "value": "payment_confirmation"}],
            )

            result = await self.resend.send_email(email)

            if result.success:
                logger.info(f"Payment confirmation email sent to {to_email}, order {order_id}")
                return {
                    "success": True,
                    "email_id": result.email_id,
                    "message": "Payment confirmation email sent"
                }
            else:
                logger.error(f"Failed to send payment email: {result.error}")
                return {
                    "success": False,
                    "error": result.error
                }

        except Exception as e:
            logger.error(f"Error sending payment confirmation email: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def send_wallet_topup_confirmation(
        self,
        to_email: str,
        customer_name: str,
        amount: float,
        currency: str,
        credits_added: int,
        new_balance: int,
        transaction_id: str,
    ) -> Dict[str, Any]:
        """
        Send wallet top-up confirmation email.

        Args:
            to_email: Customer email address
            customer_name: Customer name
            amount: Top-up amount
            currency: Currency code
            credits_added: Number of credits added
            new_balance: New wallet balance in credits
            transaction_id: Transaction ID

        Returns:
            Dict with success status
        """
        if not self.initialized:
            return {"success": False, "error": "Email service not configured"}

        try:
            formatted_amount = f"{currency} {amount:.2f}"
            subject = f"Wallet Top-Up Confirmed - {credits_added} Credits Added"

            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #fff; padding: 30px; border: 1px solid #e5e7eb; }}
                    .credits-box {{ background: linear-gradient(135deg, #10b981 0%, #34d399 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; margin: 20px 0; }}
                    .credits-number {{ font-size: 36px; font-weight: bold; }}
                    .footer {{ background: #f9fafb; padding: 20px; text-align: center; border-radius: 0 0 10px 10px; font-size: 12px; color: #6b7280; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>📚 InkWave</h1>
                        <p>Wallet Top-Up Confirmed</p>
                    </div>
                    <div class="content">
                        <h2>Hi {customer_name}!</h2>
                        <p>Your wallet has been topped up successfully.</p>

                        <div class="credits-box">
                            <div class="credits-number">+{credits_added} Credits</div>
                            <div>New Balance: {new_balance} Credits</div>
                        </div>

                        <p><strong>Amount Paid:</strong> {formatted_amount}</p>
                        <p><strong>Transaction ID:</strong> {transaction_id}</p>
                        <p><strong>Date:</strong> {datetime.utcnow().strftime('%B %d, %Y at %H:%M UTC')}</p>

                        <p>You can now use your credits to listen to audiobooks and interact with AI features!</p>
                    </div>
                    <div class="footer">
                        <p>© {datetime.utcnow().year} InkWave by AI Labs Africa</p>
                    </div>
                </div>
            </body>
            </html>
            """

            text_content = f"""
Wallet Top-Up Confirmed

Hi {customer_name}!

Your wallet has been topped up successfully.

Credits Added: +{credits_added}
New Balance: {new_balance} Credits
Amount Paid: {formatted_amount}
Transaction ID: {transaction_id}
Date: {datetime.utcnow().strftime('%B %d, %Y at %H:%M UTC')}

You can now use your credits in the InkWave app!

© {datetime.utcnow().year} InkWave by AI Labs Africa
            """

            email = ResendEmail(
                from_=self.from_email,
                to=[to_email],
                subject=subject,
                html=html_content,
                text=text_content,
                tags=[{"name": "type", "value": "wallet_topup"}],
            )

            result = await self.resend.send_email(email)

            if result.success:
                logger.info(f"Wallet top-up email sent to {to_email}")
                return {"success": True, "email_id": result.email_id}
            else:
                return {"success": False, "error": result.error}

        except Exception as e:
            logger.error(f"Error sending wallet top-up email: {e}")
            return {"success": False, "error": str(e)}

    async def send_welcome_email(
        self,
        to_email: str,
        customer_name: str,
        free_credits: int = 200,
    ) -> Dict[str, Any]:
        """
        Send welcome email to new users.

        Args:
            to_email: Customer email address
            customer_name: Customer name
            free_credits: Number of free credits given

        Returns:
            Dict with success status
        """
        if not self.initialized:
            return {"success": False, "error": "Email service not configured"}

        try:
            subject = f"Welcome to InkWave! 🎉 {free_credits} Free Credits Waiting"

            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%); color: white; padding: 40px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #fff; padding: 30px; border: 1px solid #e5e7eb; }}
                    .cta-button {{ background: #7c3aed; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; display: inline-block; margin: 20px 0; font-weight: bold; }}
                    .feature {{ display: flex; align-items: center; margin: 15px 0; }}
                    .feature-icon {{ font-size: 24px; margin-right: 15px; }}
                    .footer {{ background: #f9fafb; padding: 20px; text-align: center; border-radius: 0 0 10px 10px; font-size: 12px; color: #6b7280; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>📚 Welcome to InkWave!</h1>
                        <p>Your AI-Powered Audiobook Journey Begins</p>
                    </div>
                    <div class="content">
                        <h2>Hi {customer_name}! 👋</h2>
                        <p>Thank you for joining InkWave! We're excited to have you on board.</p>

                        <div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); padding: 20px; border-radius: 10px; text-align: center; margin: 20px 0;">
                            <div style="font-size: 14px; color: #92400e;">🎁 YOUR WELCOME GIFT</div>
                            <div style="font-size: 36px; font-weight: bold; color: #7c3aed;">{free_credits} Credits</div>
                            <div style="color: #92400e;">Ready to use right away!</div>
                        </div>

                        <h3>What can you do with InkWave?</h3>

                        <div class="feature">
                            <span class="feature-icon">🎧</span>
                            <div><strong>Listen to Audiobooks</strong> - AI-narrated books with natural voices</div>
                        </div>
                        <div class="feature">
                            <span class="feature-icon">💬</span>
                            <div><strong>Ask Questions</strong> - Chat with AI about what you're reading</div>
                        </div>
                        <div class="feature">
                            <span class="feature-icon">📖</span>
                            <div><strong>Upload Your Books</strong> - Convert PDFs to audiobooks</div>
                        </div>
                        <div class="feature">
                            <span class="feature-icon">🎯</span>
                            <div><strong>Track Progress</strong> - Pick up where you left off</div>
                        </div>

                        <center>
                            <a href="https://inkwave.ailabsafrica.com" class="cta-button">Start Listening Now →</a>
                        </center>

                        <p>If you have any questions, just reply to this email or contact us at {self.support_email}</p>
                    </div>
                    <div class="footer">
                        <p>© {datetime.utcnow().year} InkWave by AI Labs Africa</p>
                    </div>
                </div>
            </body>
            </html>
            """

            text_content = f"""
Welcome to InkWave! 🎉

Hi {customer_name}!

Thank you for joining InkWave! We're excited to have you on board.

YOUR WELCOME GIFT: {free_credits} Credits - Ready to use right away!

What can you do with InkWave?
- Listen to Audiobooks - AI-narrated books with natural voices
- Ask Questions - Chat with AI about what you're reading
- Upload Your Books - Convert PDFs to audiobooks
- Track Progress - Pick up where you left off

Start listening now: https://inkwave.ailabsafrica.com

Questions? Contact us at {self.support_email}

© {datetime.utcnow().year} InkWave by AI Labs Africa
            """

            email = ResendEmail(
                from_=self.from_email,
                to=[to_email],
                subject=subject,
                html=html_content,
                text=text_content,
                tags=[{"name": "type", "value": "welcome"}],
            )

            result = await self.resend.send_email(email)

            if result.success:
                logger.info(f"Welcome email sent to {to_email}")
                return {"success": True, "email_id": result.email_id}
            else:
                return {"success": False, "error": result.error}

        except Exception as e:
            logger.error(f"Error sending welcome email: {e}")
            return {"success": False, "error": str(e)}

    async def send_club_invitation(
        self,
        to_email: str,
        recipient_name: Optional[str],
        inviter_name: str,
        club_name: str,
        book_title: str,
        club_description: Optional[str],
        invitation_token: str,
        invitation_message: Optional[str],
        frontend_url: str = "https://inkwave.ailabsafrica.com",
    ) -> Dict[str, Any]:
        """
        Send book club invitation email.

        Args:
            to_email: Recipient email address
            recipient_name: Recipient name (if known) or None
            inviter_name: Name of person who sent invitation
            club_name: Name of the book club
            book_title: Title of the book
            club_description: Club description
            invitation_token: Secure token for invitation link
            invitation_message: Personal message from inviter
            frontend_url: Frontend URL base

        Returns:
            Dict with success status
        """
        if not self.initialized:
            return {"success": False, "error": "Email service not configured"}

        try:
            greeting = f"Hi {recipient_name}" if recipient_name else "Hi there"
            invitation_link = f"{frontend_url}/club-invitation/{invitation_token}"

            # Build subject
            subject = f"{inviter_name} invited you to join '{club_name}' on InkWave"

            # Personal message section
            personal_message_html = ""
            personal_message_text = ""
            if invitation_message:
                personal_message_html = f"""
                <div style="background: #f3f4f6; padding: 15px; border-left: 4px solid #7c3aed; border-radius: 4px; margin: 20px 0;">
                    <p style="margin: 0; color: #374151; font-style: italic;">"{invitation_message}"</p>
                    <p style="margin: 10px 0 0 0; color: #6b7280; font-size: 14px;">— {inviter_name}</p>
                </div>
                """
                personal_message_text = f'\n\nPersonal Message from {inviter_name}:\n"{invitation_message}"\n'

            # Club description section
            club_desc_html = ""
            club_desc_text = ""
            if club_description:
                club_desc_html = f'<p style="color: #6b7280;">{club_description}</p>'
                club_desc_text = f'\n{club_description}\n'

            # HTML email content
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Book Club Invitation</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .header h1 {{ margin: 0; font-size: 24px; }}
                    .content {{ background: #fff; padding: 30px; border: 1px solid #e5e7eb; border-top: none; }}
                    .club-card {{ background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); padding: 20px; border-radius: 10px; margin: 20px 0; }}
                    .club-name {{ font-size: 22px; font-weight: bold; color: #7c3aed; margin-bottom: 5px; }}
                    .book-title {{ font-size: 16px; color: #92400e; margin-bottom: 10px; }}
                    .cta-button {{ background: #7c3aed; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; display: inline-block; margin: 20px 0; font-weight: bold; font-size: 16px; }}
                    .cta-button:hover {{ background: #6d28d9; }}
                    .features {{ background: #f9fafb; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                    .feature {{ display: flex; align-items: center; margin: 10px 0; }}
                    .feature-icon {{ font-size: 20px; margin-right: 10px; }}
                    .footer {{ background: #f9fafb; padding: 20px; text-align: center; border-radius: 0 0 10px 10px; font-size: 12px; color: #6b7280; }}
                    .footer a {{ color: #7c3aed; text-decoration: none; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>📚 Book Club Invitation</h1>
                        <p>Join Your Reading Community</p>
                    </div>
                    <div class="content">
                        <h2>{greeting}! 👋</h2>
                        <p><strong>{inviter_name}</strong> has invited you to join a book club on InkWave!</p>

                        {personal_message_html}

                        <div class="club-card">
                            <div class="club-name">📖 {club_name}</div>
                            <div class="book-title">Reading: {book_title}</div>
                            {club_desc_html}
                        </div>

                        <div class="features">
                            <h3 style="margin-top: 0; color: #374151;">What You'll Get:</h3>
                            <div class="feature">
                                <span class="feature-icon">💬</span>
                                <div>Discuss the book with other readers</div>
                            </div>
                            <div class="feature">
                                <span class="feature-icon">🎯</span>
                                <div>Track your reading progress together</div>
                            </div>
                            <div class="feature">
                                <span class="feature-icon">✨</span>
                                <div>Share insights and reactions</div>
                            </div>
                            <div class="feature">
                                <span class="feature-icon">👥</span>
                                <div>Connect with fellow book lovers</div>
                            </div>
                        </div>

                        <center>
                            <a href="{invitation_link}" class="cta-button">Join the Club →</a>
                        </center>

                        <p style="text-align: center; color: #6b7280; font-size: 14px; margin-top: 20px;">
                            This invitation expires in 7 days.<br>
                            If you don't have an InkWave account yet, you'll be prompted to create one.
                        </p>

                        <p style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; font-size: 14px; color: #6b7280;">
                            Questions? Contact us at <a href="mailto:{self.support_email}" style="color: #7c3aed;">{self.support_email}</a>
                        </p>
                    </div>
                    <div class="footer">
                        <p>© {datetime.utcnow().year} InkWave by AI Labs Africa. All rights reserved.</p>
                        <p>
                            <a href="https://inkwave.ailabsafrica.com">Visit InkWave</a> |
                            <a href="mailto:{self.support_email}">Contact Support</a>
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """

            # Plain text version
            text_content = f"""
Book Club Invitation

{greeting}!

{inviter_name} has invited you to join a book club on InkWave!
{personal_message_text}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📖 {club_name}
Reading: {book_title}
{club_desc_text}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

What You'll Get:
💬 Discuss the book with other readers
🎯 Track your reading progress together
✨ Share insights and reactions
👥 Connect with fellow book lovers

Join the Club:
{invitation_link}

This invitation expires in 7 days.
If you don't have an InkWave account yet, you'll be prompted to create one.

Questions? Contact us at {self.support_email}

© {datetime.utcnow().year} InkWave by AI Labs Africa
            """

            # Create and send email
            email = ResendEmail(
                from_=self.from_email,
                to=[to_email],
                subject=subject,
                html=html_content,
                text=text_content,
                tags=[
                    {"name": "type", "value": "club_invitation"},
                    {"name": "club_name", "value": club_name[:50]},  # Limit tag length
                ],
            )

            result = await self.resend.send_email(email)

            if result.success:
                logger.info(f"Club invitation email sent to {to_email} for club '{club_name}'")
                return {
                    "success": True,
                    "email_id": result.email_id,
                    "message": "Club invitation email sent"
                }
            else:
                logger.error(f"Failed to send club invitation email: {result.error}")
                return {
                    "success": False,
                    "error": result.error
                }

        except Exception as e:
            logger.error(f"Error sending club invitation email: {e}", exc_info=True)
            return {"success": False, "error": str(e)}


    async def send_wallet_topup_success(
        self,
        to_email: str,
        customer_name: str,
        amount: float,
        currency: str,
        new_balance: float,
        reference: str,
        payment_method: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send wallet top-up success email (for direct wallet balance, not credits).

        Args:
            to_email: Customer email address
            customer_name: Customer name
            amount: Top-up amount
            currency: Currency code (e.g., GHS, USD)
            new_balance: New wallet balance
            reference: Payment reference
            payment_method: Payment method used (e.g., Paystack, ExpressPay)

        Returns:
            Dict with success status
        """
        if not self.initialized:
            logger.warning("Email service not initialized - skipping top-up email")
            return {"success": False, "error": "Email service not configured"}

        try:
            formatted_amount = f"{currency} {amount:.2f}"
            formatted_balance = f"{currency} {new_balance:.2f}"
            payment_info = payment_method or "Payment Gateway"

            subject = f"Wallet Topped Up - {formatted_amount} Added to Your InkWave Account"

            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #fff; padding: 30px; border: 1px solid #e5e7eb; }}
                    .success-badge {{ background: #10b981; color: white; padding: 8px 16px; border-radius: 20px; font-size: 14px; display: inline-block; margin-bottom: 20px; }}
                    .amount-box {{ background: linear-gradient(135deg, #10b981 0%, #34d399 100%); color: white; padding: 25px; border-radius: 10px; text-align: center; margin: 20px 0; }}
                    .amount-number {{ font-size: 32px; font-weight: bold; }}
                    .balance-info {{ margin-top: 10px; font-size: 16px; opacity: 0.9; }}
                    .details {{ background: #f9fafb; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                    .details-row {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #e5e7eb; }}
                    .details-row:last-child {{ border-bottom: none; }}
                    .details-label {{ color: #6b7280; }}
                    .details-value {{ font-weight: 600; color: #111827; }}
                    .footer {{ background: #f9fafb; padding: 20px; text-align: center; border-radius: 0 0 10px 10px; font-size: 12px; color: #6b7280; }}
                    .footer a {{ color: #7c3aed; text-decoration: none; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>📚 InkWave</h1>
                        <p>Wallet Top-Up Successful</p>
                    </div>
                    <div class="content">
                        <span class="success-badge">✓ Payment Successful</span>
                        <h2>Hi {customer_name}!</h2>
                        <p>Great news! Your wallet has been topped up successfully.</p>

                        <div class="amount-box">
                            <div class="amount-number">+{formatted_amount}</div>
                            <div class="balance-info">New Balance: {formatted_balance}</div>
                        </div>

                        <div class="details">
                            <div class="details-row">
                                <span class="details-label">Reference</span>
                                <span class="details-value">{reference[:30]}...</span>
                            </div>
                            <div class="details-row">
                                <span class="details-label">Payment Method</span>
                                <span class="details-value">{payment_info}</span>
                            </div>
                            <div class="details-row">
                                <span class="details-label">Date</span>
                                <span class="details-value">{datetime.utcnow().strftime('%B %d, %Y at %H:%M UTC')}</span>
                            </div>
                        </div>

                        <p>Your wallet is ready to use! Start listening to audiobooks and exploring AI features.</p>

                        <p style="margin-top: 30px; color: #6b7280; font-size: 14px;">
                            Questions? Contact us at <a href="mailto:{self.support_email}" style="color: #7c3aed;">{self.support_email}</a>
                        </p>
                    </div>
                    <div class="footer">
                        <p>© {datetime.utcnow().year} InkWave by AI Labs Africa. All rights reserved.</p>
                        <p><a href="https://inkwave.ailabsafrica.com">Visit InkWave</a></p>
                    </div>
                </div>
            </body>
            </html>
            """

            text_content = f"""
Wallet Top-Up Successful

Hi {customer_name}!

Great news! Your wallet has been topped up successfully.

Amount Added: +{formatted_amount}
New Balance: {formatted_balance}
Reference: {reference}
Payment Method: {payment_info}
Date: {datetime.utcnow().strftime('%B %d, %Y at %H:%M UTC')}

Your wallet is ready to use!

Questions? Contact us at {self.support_email}

© {datetime.utcnow().year} InkWave by AI Labs Africa
            """

            email = ResendEmail(
                from_=self.from_email,
                to=[to_email],
                subject=subject,
                html=html_content,
                text=text_content,
                tags=[{"name": "type", "value": "wallet_topup_success"}],
            )

            result = await self.resend.send_email(email)

            if result.success:
                logger.info(f"Wallet top-up success email sent to {to_email}")
                return {"success": True, "email_id": result.email_id}
            else:
                logger.error(f"Failed to send wallet top-up email: {result.error}")
                return {"success": False, "error": result.error}

        except Exception as e:
            logger.error(f"Error sending wallet top-up email: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def send_payment_failed(
        self,
        to_email: str,
        customer_name: str,
        amount: float,
        currency: str,
        reason: str,
        reference: Optional[str] = None,
        payment_method: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send payment failed notification email.

        Args:
            to_email: Customer email address
            customer_name: Customer name
            amount: Attempted amount
            currency: Currency code
            reason: Failure reason
            reference: Payment reference (if available)
            payment_method: Payment method attempted

        Returns:
            Dict with success status
        """
        if not self.initialized:
            logger.warning("Email service not initialized - skipping payment failed email")
            return {"success": False, "error": "Email service not configured"}

        try:
            formatted_amount = f"{currency} {amount:.2f}"
            payment_info = payment_method or "Payment Gateway"

            subject = f"Payment Failed - {formatted_amount} Transaction Unsuccessful"

            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #fff; padding: 30px; border: 1px solid #e5e7eb; }}
                    .failed-badge {{ background: #ef4444; color: white; padding: 8px 16px; border-radius: 20px; font-size: 14px; display: inline-block; margin-bottom: 20px; }}
                    .error-box {{ background: #fef2f2; border: 1px solid #fecaca; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                    .error-title {{ color: #dc2626; font-weight: bold; margin-bottom: 10px; }}
                    .details {{ background: #f9fafb; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                    .details-row {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #e5e7eb; }}
                    .details-row:last-child {{ border-bottom: none; }}
                    .details-label {{ color: #6b7280; }}
                    .details-value {{ font-weight: 600; color: #111827; }}
                    .cta-button {{ background: #7c3aed; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; display: inline-block; margin: 20px 0; font-weight: bold; }}
                    .footer {{ background: #f9fafb; padding: 20px; text-align: center; border-radius: 0 0 10px 10px; font-size: 12px; color: #6b7280; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>📚 InkWave</h1>
                        <p>Payment Notification</p>
                    </div>
                    <div class="content">
                        <span class="failed-badge">✗ Payment Failed</span>
                        <h2>Hi {customer_name},</h2>
                        <p>Unfortunately, your recent payment attempt was unsuccessful.</p>

                        <div class="error-box">
                            <div class="error-title">Reason for Failure:</div>
                            <p style="margin: 0; color: #374151;">{reason}</p>
                        </div>

                        <div class="details">
                            <div class="details-row">
                                <span class="details-label">Amount</span>
                                <span class="details-value">{formatted_amount}</span>
                            </div>
                            <div class="details-row">
                                <span class="details-label">Payment Method</span>
                                <span class="details-value">{payment_info}</span>
                            </div>
                            {f'<div class="details-row"><span class="details-label">Reference</span><span class="details-value">{reference[:30]}...</span></div>' if reference else ''}
                            <div class="details-row">
                                <span class="details-label">Date</span>
                                <span class="details-value">{datetime.utcnow().strftime('%B %d, %Y at %H:%M UTC')}</span>
                            </div>
                        </div>

                        <h3>What You Can Do:</h3>
                        <ul>
                            <li>Check that your card/mobile money account has sufficient funds</li>
                            <li>Verify your payment details are correct</li>
                            <li>Try a different payment method</li>
                            <li>Contact your bank if the issue persists</li>
                        </ul>

                        <center>
                            <a href="https://inkwave.ailabsafrica.com/wallet" class="cta-button">Try Again →</a>
                        </center>

                        <p style="margin-top: 30px; color: #6b7280; font-size: 14px;">
                            Need help? Contact us at <a href="mailto:{self.support_email}" style="color: #7c3aed;">{self.support_email}</a>
                        </p>
                    </div>
                    <div class="footer">
                        <p>© {datetime.utcnow().year} InkWave by AI Labs Africa</p>
                    </div>
                </div>
            </body>
            </html>
            """

            text_content = f"""
Payment Failed

Hi {customer_name},

Unfortunately, your recent payment attempt was unsuccessful.

Reason: {reason}

Transaction Details:
- Amount: {formatted_amount}
- Payment Method: {payment_info}
{f'- Reference: {reference}' if reference else ''}
- Date: {datetime.utcnow().strftime('%B %d, %Y at %H:%M UTC')}

What You Can Do:
- Check that your card/mobile money account has sufficient funds
- Verify your payment details are correct
- Try a different payment method
- Contact your bank if the issue persists

Try again: https://inkwave.ailabsafrica.com/wallet

Need help? Contact us at {self.support_email}

© {datetime.utcnow().year} InkWave by AI Labs Africa
            """

            email = ResendEmail(
                from_=self.from_email,
                to=[to_email],
                subject=subject,
                html=html_content,
                text=text_content,
                tags=[{"name": "type", "value": "payment_failed"}],
            )

            result = await self.resend.send_email(email)

            if result.success:
                logger.info(f"Payment failed email sent to {to_email}")
                return {"success": True, "email_id": result.email_id}
            else:
                logger.error(f"Failed to send payment failed email: {result.error}")
                return {"success": False, "error": result.error}

        except Exception as e:
            logger.error(f"Error sending payment failed email: {e}", exc_info=True)
            return {"success": False, "error": str(e)}


    async def send_admin_payment_notification(
        self,
        user_email: str,
        user_name: str,
        amount: float,
        currency: str,
        reference: str,
        payment_method: str,
        status: str = "Successful",
        admin_email: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send payment notification to admin.

        Args:
            user_email: Customer email address
            user_name: Customer name
            amount: Payment amount
            currency: Currency code
            reference: Transaction reference
            payment_method: Payment method used
            status: Payment status (default: Successful)
            admin_email: Admin email (defaults to ADMIN_EMAIL env var)

        Returns:
            Dict with success status
        """
        if not self.initialized:
            logger.warning("Email service not initialized - skipping admin notification")
            return {"success": False, "error": "Email service not configured"}

        try:
            # Get admin email from parameter or environment
            to_email = admin_email or os.getenv("ADMIN_EMAIL", "admin@ailabsafrica.com")
            formatted_amount = f"{currency} {amount:.2f}"

            subject = f"[InkWave] Payment Received - {formatted_amount} from {user_name}"

            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 25px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .header h1 {{ margin: 0; font-size: 20px; }}
                    .content {{ background: #fff; padding: 25px; border: 1px solid #e5e7eb; }}
                    .amount-highlight {{ background: #ecfdf5; border: 2px solid #10b981; padding: 20px; border-radius: 10px; text-align: center; margin: 20px 0; }}
                    .amount-number {{ font-size: 32px; font-weight: bold; color: #059669; }}
                    .details {{ background: #f9fafb; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                    .details-row {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #e5e7eb; }}
                    .details-row:last-child {{ border-bottom: none; }}
                    .details-label {{ color: #6b7280; }}
                    .details-value {{ font-weight: 600; color: #111827; }}
                    .status-success {{ color: #059669; }}
                    .cta-button {{ background: #7c3aed; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; margin-top: 15px; }}
                    .footer {{ background: #f9fafb; padding: 15px; text-align: center; border-radius: 0 0 10px 10px; font-size: 12px; color: #6b7280; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>💰 Payment Received</h1>
                    </div>
                    <div class="content">
                        <p>Hello,</p>
                        <p>A new payment has been successfully completed on InkWave.</p>

                        <div class="amount-highlight">
                            <div class="amount-number">{formatted_amount}</div>
                            <div style="color: #059669; margin-top: 5px;">Payment Received</div>
                        </div>

                        <div class="details">
                            <div class="details-row">
                                <span class="details-label">User</span>
                                <span class="details-value">{user_name}</span>
                            </div>
                            <div class="details-row">
                                <span class="details-label">Email</span>
                                <span class="details-value">{user_email}</span>
                            </div>
                            <div class="details-row">
                                <span class="details-label">Amount</span>
                                <span class="details-value">{formatted_amount}</span>
                            </div>
                            <div class="details-row">
                                <span class="details-label">Reference</span>
                                <span class="details-value">{reference[:40]}...</span>
                            </div>
                            <div class="details-row">
                                <span class="details-label">Payment Method</span>
                                <span class="details-value">{payment_method}</span>
                            </div>
                            <div class="details-row">
                                <span class="details-label">Date</span>
                                <span class="details-value">{datetime.utcnow().strftime('%B %d, %Y at %H:%M UTC')}</span>
                            </div>
                            <div class="details-row">
                                <span class="details-label">Status</span>
                                <span class="details-value status-success">{status}</span>
                            </div>
                        </div>

                        <p>Please log in to the admin dashboard if further action is required.</p>

                        <center>
                            <a href="https://inkwave.ailabsafrica.com/admin" class="cta-button">View Dashboard</a>
                        </center>
                    </div>
                    <div class="footer">
                        <p>InkWave System Notification</p>
                        <p>© {datetime.utcnow().year} AI Labs Africa</p>
                    </div>
                </div>
            </body>
            </html>
            """

            text_content = f"""
[InkWave] Payment Received

Hello,

A new payment has been successfully completed on InkWave.

Payment Details:
- User: {user_name} ({user_email})
- Amount: {formatted_amount}
- Reference: {reference}
- Payment Method: {payment_method}
- Date: {datetime.utcnow().strftime('%B %d, %Y at %H:%M UTC')}
- Status: {status}

Please log in to the admin dashboard if further action is required.

Dashboard: https://inkwave.ailabsafrica.com/admin

---
InkWave System Notification
© {datetime.utcnow().year} AI Labs Africa
            """

            email = ResendEmail(
                from_=self.from_email,
                to=[to_email],
                subject=subject,
                html=html_content,
                text=text_content,
                tags=[{"name": "type", "value": "admin_payment_notification"}],
            )

            result = await self.resend.send_email(email)

            if result.success:
                logger.info(f"Admin payment notification sent for {user_email}, amount: {formatted_amount}")
                return {"success": True, "email_id": result.email_id}
            else:
                logger.error(f"Failed to send admin notification: {result.error}")
                return {"success": False, "error": result.error}

        except Exception as e:
            logger.error(f"Error sending admin payment notification: {e}", exc_info=True)
            return {"success": False, "error": str(e)}


# Singleton instance
_email_service: Optional[InkWaveEmailService] = None


def get_email_service() -> InkWaveEmailService:
    """
    Get email service singleton instance.

    Returns:
        InkWaveEmailService instance
    """
    global _email_service
    if _email_service is None:
        _email_service = InkWaveEmailService()
    return _email_service
