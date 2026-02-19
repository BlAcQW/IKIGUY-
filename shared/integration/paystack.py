"""
Paystack Integration Module

This module provides comprehensive integration with Paystack for African payment processing.
Supports payment processing, transaction management, and webhook handling.
"""

import asyncio
import json
import logging
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

try:
    import requests
    PAYSTACK_AVAILABLE = True
except ImportError:
    PAYSTACK_AVAILABLE = False
    logging.warning("Paystack APIs not available. Install requests")

logger = logging.getLogger(__name__)


class PaystackTransactionStatus(Enum):
    """Paystack transaction statuses."""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    ABANDONED = "abandoned"
    CANCELLED = "cancelled"


class PaystackChannel(Enum):
    """Paystack payment channels."""
    CARD = "card"
    BANK = "bank"
    USSD = "ussd"
    QR = "qr"
    MOBILE_MONEY = "mobile_money"
    BANK_TRANSFER = "bank_transfer"


@dataclass
class PaystackConfig:
    """Configuration for Paystack integration."""
    secret_key: str
    public_key: str
    base_url: str = "https://api.paystack.co"
    webhook_secret: Optional[str] = None


@dataclass
class PaystackTransaction:
    """Paystack transaction data structure."""
    id: Optional[str] = None
    reference: str = ""
    amount: int = 0  # Amount in kobo (smallest currency unit)
    currency: str = "NGN"
    status: PaystackTransactionStatus = PaystackTransactionStatus.PENDING
    channel: PaystackChannel = PaystackChannel.CARD
    customer_email: str = ""
    customer_code: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None


@dataclass
class PaystackCustomer:
    """Paystack customer data structure."""
    id: Optional[int] = None
    customer_code: str = ""
    email: str = ""
    first_name: str = ""
    last_name: str = ""
    phone: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class PaystackPlan:
    """Paystack plan data structure."""
    id: Optional[int] = None
    name: str = ""
    amount: int = 0  # Amount in kobo
    interval: str = "monthly"  # daily, weekly, monthly, yearly
    currency: str = "NGN"
    description: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class PaystackWebhookEvent:
    """Paystack webhook event data structure."""
    event: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[datetime] = None


class PaystackIntegration:
    """Paystack integration for African payment processing."""
    
    def __init__(self, config: PaystackConfig):
        """
        Initialize Paystack integration.
        
        Args:
            config: Paystack configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.headers = {
            "Authorization": f"Bearer {config.secret_key}",
            "Content-Type": "application/json"
        }
    
    async def initialize_transaction(self, transaction: PaystackTransaction) -> Dict[str, Any]:
        """
        Initialize a Paystack transaction.
        
        Args:
            transaction: Transaction data
            
        Returns:
            Transaction initialization result
        """
        try:
            # Prepare transaction data
            transaction_data = {
                "amount": transaction.amount,
                "email": transaction.customer_email,
                "reference": transaction.reference,
                "currency": transaction.currency,
                "callback_url": transaction.metadata.get("callback_url"),
                "metadata": transaction.metadata
            }
            
            url = f"{self.config.base_url}/transaction/initialize"
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, requests.post, url, json=transaction_data, headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "authorization_url": data["data"]["authorization_url"],
                    "access_code": data["data"]["access_code"],
                    "reference": data["data"]["reference"]
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to initialize transaction: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            self.logger.error(f"Failed to initialize Paystack transaction: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def verify_transaction(self, reference: str) -> Dict[str, Any]:
        """
        Verify a Paystack transaction.
        
        Args:
            reference: Transaction reference
            
        Returns:
            Transaction verification result
        """
        try:
            url = f"{self.config.base_url}/transaction/verify/{reference}"
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, requests.get, url, headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "transaction": data["data"],
                    "status": data["data"]["status"],
                    "amount": data["data"]["amount"],
                    "currency": data["data"]["currency"]
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to verify transaction: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            self.logger.error(f"Failed to verify Paystack transaction: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def create_customer(self, customer: PaystackCustomer) -> Dict[str, Any]:
        """
        Create a new Paystack customer.
        
        Args:
            customer: Customer data
            
        Returns:
            Customer creation result
        """
        try:
            customer_data = {
                "email": customer.email,
                "first_name": customer.first_name,
                "last_name": customer.last_name,
                "phone": customer.phone,
                "metadata": customer.metadata
            }
            
            url = f"{self.config.base_url}/customer"
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, requests.post, url, json=customer_data, headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "customer": data["data"],
                    "customer_code": data["data"]["customer_code"]
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to create customer: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            self.logger.error(f"Failed to create Paystack customer: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_customer(self, customer_code: str) -> Dict[str, Any]:
        """
        Get a Paystack customer by customer code.
        
        Args:
            customer_code: Customer code
            
        Returns:
            Customer information
        """
        try:
            url = f"{self.config.base_url}/customer/{customer_code}"
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, requests.get, url, headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "customer": data["data"]
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to get customer: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get Paystack customer: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def create_plan(self, plan: PaystackPlan) -> Dict[str, Any]:
        """
        Create a new Paystack plan.
        
        Args:
            plan: Plan data
            
        Returns:
            Plan creation result
        """
        try:
            plan_data = {
                "name": plan.name,
                "amount": plan.amount,
                "interval": plan.interval,
                "currency": plan.currency,
                "description": plan.description
            }
            
            url = f"{self.config.base_url}/plan"
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, requests.post, url, json=plan_data, headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "plan": data["data"],
                    "plan_code": data["data"]["plan_code"]
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to create plan: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            self.logger.error(f"Failed to create Paystack plan: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def create_subscription(self, customer_code: str, plan_code: str, 
                                 start_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Create a Paystack subscription.
        
        Args:
            customer_code: Customer code
            plan_code: Plan code
            start_date: Subscription start date
            
        Returns:
            Subscription creation result
        """
        try:
            subscription_data = {
                "customer": customer_code,
                "plan": plan_code
            }
            
            if start_date:
                subscription_data["start_date"] = start_date.isoformat()
            
            url = f"{self.config.base_url}/subscription"
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, requests.post, url, json=subscription_data, headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "subscription": data["data"],
                    "subscription_code": data["data"]["subscription_code"]
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to create subscription: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            self.logger.error(f"Failed to create Paystack subscription: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def charge_card(self, customer_code: str, amount: int, 
                         authorization_code: str, reference: str) -> Dict[str, Any]:
        """
        Charge a customer's card.
        
        Args:
            customer_code: Customer code
            amount: Amount in kobo
            authorization_code: Card authorization code
            reference: Transaction reference
            
        Returns:
            Charge result
        """
        try:
            charge_data = {
                "amount": amount,
                "email": "",  # Will be fetched from customer
                "authorization_code": authorization_code,
                "reference": reference
            }
            
            url = f"{self.config.base_url}/transaction/charge_authorization"
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, requests.post, url, json=charge_data, headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "transaction": data["data"],
                    "status": data["data"]["status"]
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to charge card: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            self.logger.error(f"Failed to charge Paystack card: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_transactions(self, page: int = 1, per_page: int = 50) -> Dict[str, Any]:
        """
        Get Paystack transactions.
        
        Args:
            page: Page number
            per_page: Number of transactions per page
            
        Returns:
            List of transactions
        """
        try:
            params = {
                "page": page,
                "perPage": per_page
            }
            
            url = f"{self.config.base_url}/transaction"
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, requests.get, url, params=params, headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "transactions": data["data"],
                    "meta": data["meta"]
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to get transactions: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get Paystack transactions: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def refund_transaction(self, transaction_id: str, amount: Optional[int] = None, 
                                reason: Optional[str] = None) -> Dict[str, Any]:
        """
        Refund a Paystack transaction.
        
        Args:
            transaction_id: Transaction ID
            amount: Amount to refund (if None, refunds full amount)
            reason: Refund reason
            
        Returns:
            Refund result
        """
        try:
            refund_data = {}
            
            if amount:
                refund_data["amount"] = amount
            
            if reason:
                refund_data["reason"] = reason
            
            url = f"{self.config.base_url}/refund"
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, requests.post, url, json=refund_data, headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "refund": data["data"]
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to refund transaction: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            self.logger.error(f"Failed to refund Paystack transaction: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """
        Verify Paystack webhook signature.
        
        Args:
            payload: Raw webhook payload
            signature: Webhook signature
            
        Returns:
            True if signature is valid
        """
        if not self.config.webhook_secret:
            self.logger.warning("Webhook secret not configured, skipping signature verification")
            return True
        
        try:
            # Calculate expected signature
            expected_signature = hmac.new(
                self.config.webhook_secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha512
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, signature)
            
        except Exception as e:
            self.logger.error(f"Failed to verify webhook signature: {e}")
            return False
    
    async def process_webhook(self, payload: str, signature: str) -> Dict[str, Any]:
        """
        Process a Paystack webhook.
        
        Args:
            payload: Raw webhook payload
            signature: Webhook signature
            
        Returns:
            Webhook processing result
        """
        try:
            # Verify signature
            if not self.verify_webhook_signature(payload, signature):
                return {
                    "success": False,
                    "error": "Invalid webhook signature"
                }
            
            # Parse webhook data
            webhook_data = json.loads(payload)
            
            event = PaystackWebhookEvent(
                event=webhook_data.get("event", ""),
                data=webhook_data.get("data", {}),
                timestamp=datetime.now()
            )
            
            # Process different event types
            if event.event == "charge.success":
                return await self._handle_charge_success(event.data)
            elif event.event == "charge.failed":
                return await self._handle_charge_failed(event.data)
            elif event.event == "transfer.success":
                return await self._handle_transfer_success(event.data)
            elif event.event == "transfer.failed":
                return await self._handle_transfer_failed(event.data)
            else:
                return {
                    "success": True,
                    "message": f"Unhandled event: {event.event}",
                    "event": event.event
                }
                
        except Exception as e:
            self.logger.error(f"Failed to process Paystack webhook: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_charge_success(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle charge.success webhook event."""
        return {
            "success": True,
            "event": "charge.success",
            "transaction_id": data.get("id"),
            "reference": data.get("reference"),
            "amount": data.get("amount"),
            "status": data.get("status")
        }
    
    async def _handle_charge_failed(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle charge.failed webhook event."""
        return {
            "success": True,
            "event": "charge.failed",
            "transaction_id": data.get("id"),
            "reference": data.get("reference"),
            "failure_reason": data.get("failure_reason")
        }
    
    async def _handle_transfer_success(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle transfer.success webhook event."""
        return {
            "success": True,
            "event": "transfer.success",
            "transfer_id": data.get("id"),
            "reference": data.get("reference"),
            "amount": data.get("amount")
        }
    
    async def _handle_transfer_failed(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle transfer.failed webhook event."""
        return {
            "success": True,
            "event": "transfer.failed",
            "transfer_id": data.get("id"),
            "reference": data.get("reference"),
            "failure_reason": data.get("failure_reason")
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Paystack integration.
        
        Returns:
            Health status
        """
        try:
            # Try to get transaction list as a health check
            url = f"{self.config.base_url}/transaction?perPage=1"
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, requests.get, url, headers=self.headers
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "status": "healthy",
                    "message": "Paystack API is accessible"
                }
            else:
                return {
                    "success": False,
                    "status": "unhealthy",
                    "error": f"Health check failed: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            self.logger.error(f"Paystack health check failed: {e}")
            return {
                "success": False,
                "status": "unhealthy",
                "error": str(e)
            }

