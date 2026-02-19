"""
Wallet Email Notification Templates and Service.

Handles sending email notifications for wallet events:
- Successful deposits
- Failed transactions
- Low balance alerts
- Auto-reload notifications
"""

import logging
import os
from typing import Dict, Any, Optional
from decimal import Decimal
from datetime import datetime

from .email_service import email_service, EmailMessage, EmailTemplate
from .sms_service import sms_service, SMSMessage

logger = logging.getLogger(__name__)

# Configuration
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://kasaai.ailabsafrica.com")


# Email Templates
DEPOSIT_SUCCESS_TEMPLATE = EmailTemplate(
    template_id="wallet_deposit_success",
    name="Wallet Deposit Success",
    subject_template="Payment Successful - {amount} {currency} Added to Your Wallet",
    body_template="""
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }
        .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }
        .success-icon { font-size: 48px; margin-bottom: 10px; }
        .amount { font-size: 32px; font-weight: bold; color: #667eea; margin: 20px 0; }
        .details { background: white; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .detail-row { display: flex; justify-between; padding: 10px 0; border-bottom: 1px solid #eee; }
        .detail-label { font-weight: bold; color: #666; }
        .detail-value { color: #333; }
        .footer { text-align: center; margin-top: 20px; padding: 20px; color: #666; font-size: 12px; }
        .button { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; display: inline-block; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="success-icon">✅</div>
            <h1>Payment Successful!</h1>
        </div>
        <div class="content">
            <p>Hi there,</p>
            <p>Your wallet has been successfully topped up!</p>

            <div class="amount">{amount} {currency}</div>

            <div class="details">
                <div class="detail-row">
                    <span class="detail-label">Transaction ID:</span>
                    <span class="detail-value">{transaction_id}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Payment Method:</span>
                    <span class="detail-value">{payment_method}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Processing Fee:</span>
                    <span class="detail-value">{processing_fee} {currency}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Date:</span>
                    <span class="detail-value">{transaction_date}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">New Balance:</span>
                    <span class="detail-value" style="font-size: 18px; color: #667eea; font-weight: bold;">{new_balance} {currency}</span>
                </div>
            </div>

            <p style="margin-top: 20px;">Your funds are now available and ready to use!</p>

            <center>
                <a href="{frontend_url}/billing" class="button">View Transaction History</a>
            </center>
        </div>
        <div class="footer">
            <p>© 2025 KasaAI Flow | AI Labs Africa</p>
            <p>This is an automated email. Please do not reply.</p>
        </div>
    </div>
</body>
</html>
    """,
    template_type="html",
    variables=["amount", "currency", "transaction_id", "payment_method", "processing_fee", "transaction_date", "new_balance"],
    category="wallet"
)

LOW_BALANCE_ALERT_TEMPLATE = EmailTemplate(
    template_id="wallet_low_balance",
    name="Low Balance Alert",
    subject_template="Low Balance Alert - {balance} {currency} Remaining",
    body_template="""
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #f59e0b 0%, #ea580c 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }
        .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }
        .warning-icon { font-size: 48px; margin-bottom: 10px; }
        .balance { font-size: 32px; font-weight: bold; color: #ea580c; margin: 20px 0; }
        .alert-box { background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0; }
        .button { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; display: inline-block; margin: 20px 0; }
        .footer { text-align: center; margin-top: 20px; padding: 20px; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="warning-icon">⚠️</div>
            <h1>Low Balance Alert</h1>
        </div>
        <div class="content">
            <p>Hi there,</p>
            <p>Your KasaAI wallet balance is running low.</p>

            <div class="balance">{balance} {currency}</div>

            <div class="alert-box">
                <strong>⚡ Action Needed:</strong> Your balance has dropped below the alert threshold of {threshold} {currency}.
                To avoid service interruption, please top up your wallet soon.
            </div>

            <p>Top up now to ensure uninterrupted service for your AI voice assistants and automations.</p>

            <center>
                <a href="{frontend_url}/billing" class="button">Top Up Now</a>
            </center>
        </div>
        <div class="footer">
            <p>© 2025 KasaAI Flow | AI Labs Africa</p>
            <p>This is an automated alert. You can manage notification settings in your wallet settings.</p>
        </div>
    </div>
</body>
</html>
    """,
    template_type="html",
    variables=["balance", "currency", "threshold"],
    category="wallet"
)

AUTO_RELOAD_SUCCESS_TEMPLATE = EmailTemplate(
    template_id="wallet_auto_reload",
    name="Auto-Reload Success",
    subject_template="Auto-Reload Successful - {amount} {currency} Added",
    body_template="""
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }
        .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }
        .icon { font-size: 48px; margin-bottom: 10px; }
        .amount { font-size: 32px; font-weight: bold; color: #10b981; margin: 20px 0; }
        .info-box { background: #d1fae5; border-left: 4px solid #10b981; padding: 15px; margin: 20px 0; }
        .details { background: white; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .detail-row { display: flex; justify-between; padding: 10px 0; border-bottom: 1px solid #eee; }
        .footer { text-align: center; margin-top: 20px; padding: 20px; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="icon">⚡</div>
            <h1>Auto-Reload Successful</h1>
        </div>
        <div class="content">
            <p>Hi there,</p>
            <p>Your wallet was automatically reloaded because your balance dropped below the threshold.</p>

            <div class="amount">{amount} {currency}</div>

            <div class="info-box">
                <strong>🤖 Automatic Top-Up:</strong> This payment was processed automatically using your saved payment method
                to ensure uninterrupted service.
            </div>

            <div class="details">
                <div class="detail-row">
                    <span style="font-weight: bold; color: #666;">Previous Balance:</span>
                    <span>{previous_balance} {currency}</span>
                </div>
                <div class="detail-row">
                    <span style="font-weight: bold; color: #666;">Reload Amount:</span>
                    <span>{amount} {currency}</span>
                </div>
                <div class="detail-row">
                    <span style="font-weight: bold; color: #666;">New Balance:</span>
                    <span style="font-size: 18px; color: #10b981; font-weight: bold;">{new_balance} {currency}</span>
                </div>
                <div class="detail-row">
                    <span style="font-weight: bold; color: #666;">Payment Method:</span>
                    <span>{payment_method}</span>
                </div>
            </div>

            <p>Your services will continue running without interruption. You can manage auto-reload settings anytime.</p>
        </div>
        <div class="footer">
            <p>© 2025 KasaAI Flow | AI Labs Africa</p>
            <p>Manage auto-reload settings at <a href="{frontend_url}/billing">your billing page</a></p>
        </div>
    </div>
</body>
</html>
    """,
    template_type="html",
    variables=["amount", "currency", "previous_balance", "new_balance", "payment_method"],
    category="wallet"
)


class WalletNotificationService:
    """Service for sending wallet-related email notifications."""

    def __init__(self):
        """Initialize wallet notification service and register templates."""
        self._register_templates()
        logger.info("Wallet notification service initialized")

    def _register_templates(self):
        """Register all wallet email templates."""
        email_service.register_template(DEPOSIT_SUCCESS_TEMPLATE)
        email_service.register_template(LOW_BALANCE_ALERT_TEMPLATE)
        email_service.register_template(AUTO_RELOAD_SUCCESS_TEMPLATE)
        logger.info("Registered 3 wallet email templates")

    async def send_deposit_success_email(
        self,
        to_email: str,
        amount: Decimal,
        currency: str,
        transaction_id: str,
        payment_method: str,
        processing_fee: Decimal,
        new_balance: Decimal,
        transaction_date: str
    ) -> Dict[str, Any]:
        """
        Send deposit success notification email.

        Args:
            to_email: Recipient email address
            amount: Deposit amount
            currency: Currency code
            transaction_id: Transaction ID
            payment_method: Payment method used
            processing_fee: Processing fee charged
            new_balance: New wallet balance
            transaction_date: Transaction timestamp

        Returns:
            Email send result
        """
        try:
            email = EmailMessage(
                to_addresses=[to_email],
                from_address="noreply@ailabsafrica.com",
                subject="",  # Will be populated by template
                body="",  # Will be populated by template
                template_id="wallet_deposit_success",
                template_data={
                    "amount": f"{float(amount):.2f}",
                    "currency": currency,
                    "transaction_id": transaction_id,
                    "payment_method": payment_method,
                    "processing_fee": f"{float(processing_fee):.2f}",
                    "new_balance": f"{float(new_balance):.2f}",
                    "transaction_date": transaction_date,
                    "frontend_url": FRONTEND_URL
                }
            )

            result = await email_service.send_email("smtp", email)
            logger.info(f"Sent deposit success email to {to_email}: {result.get('success')}")
            return result

        except Exception as e:
            logger.error(f"Failed to send deposit success email: {e}")
            return {"success": False, "error": str(e)}

    async def send_low_balance_alert(
        self,
        to_email: str,
        balance: Decimal,
        threshold: Decimal,
        currency: str
    ) -> Dict[str, Any]:
        """
        Send low balance alert email.

        Args:
            to_email: Recipient email address
            balance: Current balance
            threshold: Alert threshold
            currency: Currency code

        Returns:
            Email send result
        """
        try:
            email = EmailMessage(
                to_addresses=[to_email],
                from_address="noreply@ailabsafrica.com",
                subject="",
                body="",
                template_id="wallet_low_balance",
                template_data={
                    "balance": f"{float(balance):.2f}",
                    "threshold": f"{float(threshold):.2f}",
                    "currency": currency,
                    "frontend_url": FRONTEND_URL
                }
            )

            result = await email_service.send_email("smtp", email)
            logger.info(f"Sent low balance alert to {to_email}: {result.get('success')}")
            return result

        except Exception as e:
            logger.error(f"Failed to send low balance alert: {e}")
            return {"success": False, "error": str(e)}

    async def send_auto_reload_notification(
        self,
        to_email: str,
        amount: Decimal,
        previous_balance: Decimal,
        new_balance: Decimal,
        payment_method: str,
        currency: str
    ) -> Dict[str, Any]:
        """
        Send auto-reload success notification.

        Args:
            to_email: Recipient email address
            amount: Reload amount
            previous_balance: Balance before reload
            new_balance: Balance after reload
            payment_method: Payment method used
            currency: Currency code

        Returns:
            Email send result
        """
        try:
            email = EmailMessage(
                to_addresses=[to_email],
                from_address="noreply@ailabsafrica.com",
                subject="",
                body="",
                template_id="wallet_auto_reload",
                template_data={
                    "amount": f"{float(amount):.2f}",
                    "previous_balance": f"{float(previous_balance):.2f}",
                    "new_balance": f"{float(new_balance):.2f}",
                    "payment_method": payment_method,
                    "currency": currency,
                    "frontend_url": FRONTEND_URL
                }
            )

            result = await email_service.send_email("smtp", email)
            logger.info(f"Sent auto-reload notification to {to_email}: {result.get('success')}")
            return result

        except Exception as e:
            logger.error(f"Failed to send auto-reload notification: {e}")
            return {"success": False, "error": str(e)}

    async def send_deposit_success_sms(
        self,
        to_number: str,
        amount: Decimal,
        currency: str,
        new_balance: Decimal
    ) -> Dict[str, Any]:
        """
        Send deposit success SMS notification (for mobile money transactions).

        Args:
            to_number: Recipient phone number (E.164 format)
            amount: Deposit amount
            currency: Currency code
            new_balance: New wallet balance

        Returns:
            SMS send result
        """
        try:
            # Format message (160 characters max)
            message = (
                f"KasaAI: Payment successful! {currency} {float(amount):.2f} added to your wallet. "
                f"New balance: {currency} {float(new_balance):.2f}. Thank you!"
            )

            sms = SMSMessage(
                to_number=to_number,
                message=message,
                from_number="KasaAI"
            )

            # Try Africa's Talking first (best for Ghana/Kenya/Nigeria)
            if "africastalking" in sms_service.get_supported_providers():
                result = await sms_service.send_sms("africastalking", sms)
            else:
                # Fallback to any available provider
                providers = sms_service.get_supported_providers()
                if providers:
                    result = await sms_service.send_sms(providers[0], sms)
                else:
                    return {
                        "success": False,
                        "error": "No SMS providers configured"
                    }

            logger.info(f"Sent deposit success SMS to {to_number}: {result.get('success')}")
            return result

        except Exception as e:
            logger.error(f"Failed to send deposit success SMS: {e}")
            return {"success": False, "error": str(e)}

    async def send_low_balance_sms(
        self,
        to_number: str,
        balance: Decimal,
        currency: str
    ) -> Dict[str, Any]:
        """
        Send low balance alert SMS.

        Args:
            to_number: Recipient phone number
            balance: Current balance
            currency: Currency code

        Returns:
            SMS send result
        """
        try:
            message = (
                f"KasaAI Alert: Your wallet balance is low ({currency} {float(balance):.2f}). "
                f"Top up now at {FRONTEND_URL.replace('https://', '').replace('http://', '')}/billing"
            )

            sms = SMSMessage(
                to_number=to_number,
                message=message,
                from_number="KasaAI"
            )

            if "africastalking" in sms_service.get_supported_providers():
                result = await sms_service.send_sms("africastalking", sms)
            else:
                providers = sms_service.get_supported_providers()
                if providers:
                    result = await sms_service.send_sms(providers[0], sms)
                else:
                    return {"success": False, "error": "No SMS providers configured"}

            logger.info(f"Sent low balance SMS to {to_number}: {result.get('success')}")
            return result

        except Exception as e:
            logger.error(f"Failed to send low balance SMS: {e}")
            return {"success": False, "error": str(e)}

    async def send_payment_prompt_sms(
        self,
        to_number: str,
        amount: Decimal,
        currency: str
    ) -> Dict[str, Any]:
        """
        Send SMS to prompt user to approve mobile money payment.

        Args:
            to_number: Recipient phone number
            amount: Payment amount
            currency: Currency code

        Returns:
            SMS send result
        """
        try:
            message = (
                f"KasaAI: Please approve the {currency} {float(amount):.2f} payment "
                f"request on your phone to complete your wallet top-up."
            )

            sms = SMSMessage(
                to_number=to_number,
                message=message,
                from_number="KasaAI"
            )

            if "africastalking" in sms_service.get_supported_providers():
                result = await sms_service.send_sms("africastalking", sms)
            else:
                providers = sms_service.get_supported_providers()
                if providers:
                    result = await sms_service.send_sms(providers[0], sms)
                else:
                    return {"success": False, "error": "No SMS providers configured"}

            logger.info(f"Sent payment prompt SMS to {to_number}: {result.get('success')}")
            return result

        except Exception as e:
            logger.error(f"Failed to send payment prompt SMS: {e}")
            return {"success": False, "error": str(e)}


# Global instance
wallet_notification_service = WalletNotificationService()
