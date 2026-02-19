"""
Flutterwave Integration Module

This module provides integration with Flutterwave for African payment processing,
mobile money, and banking transactions.
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
    FLUTTERWAVE_AVAILABLE = True
except ImportError:
    FLUTTERWAVE_AVAILABLE = False
    logging.warning("Flutterwave APIs not available. Install requests")

logger = logging.getLogger(__name__)


class FlutterwaveTransactionStatus(Enum):
    """Flutterwave transaction status."""
    PENDING = "pending"
    SUCCESSFUL = "successful"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class FlutterwavePaymentType(Enum):
    """Flutterwave payment types."""
    CARD = "card"
    BANK_TRANSFER = "banktransfer"
    USSD = "ussd"
    QR = "qr"
    MOBILE_MONEY = "mobilemoney"
    BANK_ACCOUNT = "bankaccount"
    PAYATTITUDE = "payattitude"
    MPESA = "mpesa"
    GHANA_MOBILE_MONEY = "ghanamobilemoney"
    ZAMBIA_MOBILE_MONEY = "zambiamobilemoney"
    RWANDA_MOBILE_MONEY = "rwandamobilemoney"
    FRANCOPHONE_MOBILE_MONEY = "francophonemobilemoney"
    MPESA_TANZANIA = "mpesatanzania"
    MPESA_UGANDA = "mpesauganda"
    BARRION_MOBILE_MONEY = "barrionmobilemoney"
    VOICE = "voice"


@dataclass
class FlutterwaveConfig:
    """Configuration for Flutterwave integration."""
    
    public_key: str
    """Flutterwave public key."""
    
    secret_key: str
    """Flutterwave secret key."""
    
    base_url: str = "https://api.flutterwave.com/v3"
    """Flutterwave API base URL."""
    
    timeout: int = 30
    """Request timeout in seconds."""
    
    verify_ssl: bool = True
    """Verify SSL certificates."""
    
    webhook_secret: Optional[str] = None
    """Webhook secret for verification."""


@dataclass
class FlutterwaveTransaction:
    """Flutterwave transaction data structure."""
    
    id: int
    """Transaction ID."""
    
    tx_ref: str
    """Transaction reference."""
    
    flw_ref: str
    """Flutterwave reference."""
    
    amount: float
    """Transaction amount."""
    
    currency: str
    """Transaction currency."""
    
    status: FlutterwaveTransactionStatus
    """Transaction status."""
    
    payment_type: FlutterwavePaymentType
    """Payment type."""
    
    customer: Dict[str, Any]
    """Customer information."""
    
    meta: Dict[str, Any]
    """Transaction metadata."""
    
    created_at: Optional[datetime] = None
    """Creation timestamp."""
    
    updated_at: Optional[datetime] = None
    """Last update timestamp."""
    
    charged_amount: Optional[float] = None
    """Charged amount."""
    
    app_fee: Optional[float] = None
    """Application fee."""
    
    merchant_fee: Optional[float] = None
    """Merchant fee."""
    
    processor_response: Optional[str] = None
    """Processor response."""
    
    auth_model: Optional[str] = None
    """Authentication model."""
    
    ip: Optional[str] = None
    """Customer IP address."""
    
    narration: Optional[str] = None
    """Transaction narration."""
    
    device_fingerprint: Optional[str] = None
    """Device fingerprint."""
    
    amount_settled: Optional[float] = None
    """Amount settled."""
    
    payment_page: Optional[str] = None
    """Payment page URL."""


@dataclass
class FlutterwaveCustomer:
    """Flutterwave customer data structure."""
    
    id: int
    """Customer ID."""
    
    email: str
    """Customer email."""
    
    name: str
    """Customer name."""
    
    phone_number: Optional[str] = None
    """Customer phone number."""
    
    created_at: Optional[datetime] = None
    """Creation timestamp."""
    
    updated_at: Optional[datetime] = None
    """Last update timestamp."""


@dataclass
class FlutterwavePlan:
    """Flutterwave plan data structure."""
    
    id: int
    """Plan ID."""
    
    name: str
    """Plan name."""
    
    amount: float
    """Plan amount."""
    
    currency: str
    """Plan currency."""
    
    interval: str
    """Billing interval."""
    
    duration: int
    """Plan duration."""
    
    status: str
    """Plan status."""
    
    created_at: Optional[datetime] = None
    """Creation timestamp."""


@dataclass
class FlutterwaveWebhookEvent:
    """Flutterwave webhook event data structure."""
    
    event: str
    """Event type."""
    
    data: Dict[str, Any]
    """Event data."""
    
    signature: str
    """Webhook signature."""
    
    timestamp: Optional[datetime] = None
    """Event timestamp."""


class FlutterwaveIntegration:
    """Flutterwave integration for African payment processing."""
    
    def __init__(self, config: FlutterwaveConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.timeout = config.timeout
        self.session.verify = config.verify_ssl
        self.session.headers.update({
            "Authorization": f"Bearer {config.secret_key}",
            "Content-Type": "application/json"
        })
    
    def _generate_tx_ref(self, prefix: str = "KASA") -> str:
        """Generate a unique transaction reference."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = hashlib.md5(f"{timestamp}{prefix}".encode()).hexdigest()[:8]
        return f"{prefix}_{timestamp}_{random_suffix}"
    
    def _verify_webhook_signature(self, signature: str, payload: str) -> bool:
        """Verify webhook signature."""
        if not self.config.webhook_secret:
            return False
        
        expected_signature = hmac.new(
            self.config.webhook_secret.encode(),
            payload.encode(),
            hashlib.sha512
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    async def initialize_transaction(
        self,
        amount: float,
        currency: str,
        email: str,
        phone_number: Optional[str] = None,
        name: Optional[str] = None,
        tx_ref: Optional[str] = None,
        payment_type: Optional[FlutterwavePaymentType] = None,
        meta: Optional[Dict[str, Any]] = None,
        redirect_url: Optional[str] = None,
        customizations: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Initialize a transaction.
        
        Args:
            amount: Transaction amount
            currency: Transaction currency
            email: Customer email
            phone_number: Customer phone number
            name: Customer name
            tx_ref: Transaction reference
            payment_type: Payment type
            meta: Transaction metadata
            redirect_url: Redirect URL after payment
            customizations: Payment page customizations
            
        Returns:
            Transaction initialization response
        """
        try:
            if tx_ref is None:
                tx_ref = self._generate_tx_ref()
            
            url = f"{self.config.base_url}/payments"
            
            data = {
                "tx_ref": tx_ref,
                "amount": amount,
                "currency": currency,
                "email": email,
                "public_key": self.config.public_key
            }
            
            if phone_number:
                data["phone_number"] = phone_number
            if name:
                data["name"] = name
            if payment_type:
                data["payment_type"] = payment_type.value
            if meta:
                data["meta"] = meta
            if redirect_url:
                data["redirect_url"] = redirect_url
            if customizations:
                data["customizations"] = customizations
            
            response = self.session.post(url, json=data)
            response.raise_for_status()
            
            result = response.json()
            if result.get("status") == "success":
                self.logger.info(f"Successfully initialized transaction: {tx_ref}")
                return result["data"]
            else:
                self.logger.error(f"Failed to initialize transaction: {result}")
                raise Exception(f"Transaction initialization failed: {result.get('message')}")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize transaction: {e}")
            raise
    
    async def verify_transaction(self, transaction_id: int) -> FlutterwaveTransaction:
        """
        Verify a transaction.
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            Transaction data
        """
        try:
            url = f"{self.config.base_url}/transactions/{transaction_id}/verify"
            response = self.session.get(url)
            response.raise_for_status()
            
            result = response.json()
            if result.get("status") == "success":
                transaction_data = result["data"]
                
                return FlutterwaveTransaction(
                    id=transaction_data["id"],
                    tx_ref=transaction_data["tx_ref"],
                    flw_ref=transaction_data["flw_ref"],
                    amount=transaction_data["amount"],
                    currency=transaction_data["currency"],
                    status=FlutterwaveTransactionStatus(transaction_data["status"]),
                    payment_type=FlutterwavePaymentType(transaction_data["payment_type"]),
                    customer=transaction_data.get("customer", {}),
                    meta=transaction_data.get("meta", {}),
                    created_at=datetime.fromisoformat(transaction_data["created_at"].replace("Z", "+00:00")) if transaction_data.get("created_at") else None,
                    updated_at=datetime.fromisoformat(transaction_data["updated_at"].replace("Z", "+00:00")) if transaction_data.get("updated_at") else None,
                    charged_amount=transaction_data.get("charged_amount"),
                    app_fee=transaction_data.get("app_fee"),
                    merchant_fee=transaction_data.get("merchant_fee"),
                    processor_response=transaction_data.get("processor_response"),
                    auth_model=transaction_data.get("auth_model"),
                    ip=transaction_data.get("ip"),
                    narration=transaction_data.get("narration"),
                    device_fingerprint=transaction_data.get("device_fingerprint"),
                    amount_settled=transaction_data.get("amount_settled"),
                    payment_page=transaction_data.get("payment_page")
                )
            else:
                raise Exception(f"Transaction verification failed: {result.get('message')}")
                
        except Exception as e:
            self.logger.error(f"Failed to verify transaction: {e}")
            raise
    
    async def get_transaction(self, transaction_id: int) -> FlutterwaveTransaction:
        """
        Get transaction details.
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            Transaction data
        """
        try:
            url = f"{self.config.base_url}/transactions/{transaction_id}"
            response = self.session.get(url)
            response.raise_for_status()
            
            result = response.json()
            if result.get("status") == "success":
                transaction_data = result["data"]
                
                return FlutterwaveTransaction(
                    id=transaction_data["id"],
                    tx_ref=transaction_data["tx_ref"],
                    flw_ref=transaction_data["flw_ref"],
                    amount=transaction_data["amount"],
                    currency=transaction_data["currency"],
                    status=FlutterwaveTransactionStatus(transaction_data["status"]),
                    payment_type=FlutterwavePaymentType(transaction_data["payment_type"]),
                    customer=transaction_data.get("customer", {}),
                    meta=transaction_data.get("meta", {}),
                    created_at=datetime.fromisoformat(transaction_data["created_at"].replace("Z", "+00:00")) if transaction_data.get("created_at") else None,
                    updated_at=datetime.fromisoformat(transaction_data["updated_at"].replace("Z", "+00:00")) if transaction_data.get("updated_at") else None,
                    charged_amount=transaction_data.get("charged_amount"),
                    app_fee=transaction_data.get("app_fee"),
                    merchant_fee=transaction_data.get("merchant_fee"),
                    processor_response=transaction_data.get("processor_response"),
                    auth_model=transaction_data.get("auth_model"),
                    ip=transaction_data.get("ip"),
                    narration=transaction_data.get("narration"),
                    device_fingerprint=transaction_data.get("device_fingerprint"),
                    amount_settled=transaction_data.get("amount_settled"),
                    payment_page=transaction_data.get("payment_page")
                )
            else:
                raise Exception(f"Failed to get transaction: {result.get('message')}")
                
        except Exception as e:
            self.logger.error(f"Failed to get transaction: {e}")
            raise
    
    async def get_transactions(
        self,
        page: int = 1,
        per_page: int = 50,
        status: Optional[FlutterwaveTransactionStatus] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> List[FlutterwaveTransaction]:
        """
        Get transactions.
        
        Args:
            page: Page number
            per_page: Items per page
            status: Filter by status
            from_date: Filter from date
            to_date: Filter to date
            
        Returns:
            List of transactions
        """
        try:
            url = f"{self.config.base_url}/transactions"
            
            params = {
                "page": page,
                "per_page": per_page
            }
            
            if status:
                params["status"] = status.value
            if from_date:
                params["from"] = from_date.strftime("%Y-%m-%d")
            if to_date:
                params["to"] = to_date.strftime("%Y-%m-%d")
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            result = response.json()
            if result.get("status") == "success":
                transactions = []
                for transaction_data in result["data"]:
                    transaction = FlutterwaveTransaction(
                        id=transaction_data["id"],
                        tx_ref=transaction_data["tx_ref"],
                        flw_ref=transaction_data["flw_ref"],
                        amount=transaction_data["amount"],
                        currency=transaction_data["currency"],
                        status=FlutterwaveTransactionStatus(transaction_data["status"]),
                        payment_type=FlutterwavePaymentType(transaction_data["payment_type"]),
                        customer=transaction_data.get("customer", {}),
                        meta=transaction_data.get("meta", {}),
                        created_at=datetime.fromisoformat(transaction_data["created_at"].replace("Z", "+00:00")) if transaction_data.get("created_at") else None,
                        updated_at=datetime.fromisoformat(transaction_data["updated_at"].replace("Z", "+00:00")) if transaction_data.get("updated_at") else None,
                        charged_amount=transaction_data.get("charged_amount"),
                        app_fee=transaction_data.get("app_fee"),
                        merchant_fee=transaction_data.get("merchant_fee"),
                        processor_response=transaction_data.get("processor_response"),
                        auth_model=transaction_data.get("auth_model"),
                        ip=transaction_data.get("ip"),
                        narration=transaction_data.get("narration"),
                        device_fingerprint=transaction_data.get("device_fingerprint"),
                        amount_settled=transaction_data.get("amount_settled"),
                        payment_page=transaction_data.get("payment_page")
                    )
                    transactions.append(transaction)
                
                return transactions
            else:
                raise Exception(f"Failed to get transactions: {result.get('message')}")
                
        except Exception as e:
            self.logger.error(f"Failed to get transactions: {e}")
            raise
    
    async def refund_transaction(
        self,
        transaction_id: int,
        amount: Optional[float] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Refund a transaction.
        
        Args:
            transaction_id: Transaction ID
            amount: Refund amount (partial refund)
            reason: Refund reason
            
        Returns:
            Refund response
        """
        try:
            url = f"{self.config.base_url}/transactions/{transaction_id}/refund"
            
            data = {}
            if amount:
                data["amount"] = amount
            if reason:
                data["reason"] = reason
            
            response = self.session.post(url, json=data)
            response.raise_for_status()
            
            result = response.json()
            if result.get("status") == "success":
                self.logger.info(f"Successfully refunded transaction: {transaction_id}")
                return result["data"]
            else:
                raise Exception(f"Refund failed: {result.get('message')}")
                
        except Exception as e:
            self.logger.error(f"Failed to refund transaction: {e}")
            raise
    
    async def create_customer(
        self,
        email: str,
        name: str,
        phone_number: Optional[str] = None
    ) -> FlutterwaveCustomer:
        """
        Create a customer.
        
        Args:
            email: Customer email
            name: Customer name
            phone_number: Customer phone number
            
        Returns:
            Customer data
        """
        try:
            url = f"{self.config.base_url}/customers"
            
            data = {
                "email": email,
                "name": name
            }
            
            if phone_number:
                data["phone_number"] = phone_number
            
            response = self.session.post(url, json=data)
            response.raise_for_status()
            
            result = response.json()
            if result.get("status") == "success":
                customer_data = result["data"]
                
                return FlutterwaveCustomer(
                    id=customer_data["id"],
                    email=customer_data["email"],
                    phone_number=customer_data.get("phone_number"),
                    name=customer_data["name"],
                    created_at=datetime.fromisoformat(customer_data["created_at"].replace("Z", "+00:00")) if customer_data.get("created_at") else None,
                    updated_at=datetime.fromisoformat(customer_data["updated_at"].replace("Z", "+00:00")) if customer_data.get("updated_at") else None
                )
            else:
                raise Exception(f"Failed to create customer: {result.get('message')}")
                
        except Exception as e:
            self.logger.error(f"Failed to create customer: {e}")
            raise
    
    async def get_customer(self, customer_id: int) -> FlutterwaveCustomer:
        """
        Get customer details.
        
        Args:
            customer_id: Customer ID
            
        Returns:
            Customer data
        """
        try:
            url = f"{self.config.base_url}/customers/{customer_id}"
            response = self.session.get(url)
            response.raise_for_status()
            
            result = response.json()
            if result.get("status") == "success":
                customer_data = result["data"]
                
                return FlutterwaveCustomer(
                    id=customer_data["id"],
                    email=customer_data["email"],
                    phone_number=customer_data.get("phone_number"),
                    name=customer_data["name"],
                    created_at=datetime.fromisoformat(customer_data["created_at"].replace("Z", "+00:00")) if customer_data.get("created_at") else None,
                    updated_at=datetime.fromisoformat(customer_data["updated_at"].replace("Z", "+00:00")) if customer_data.get("updated_at") else None
                )
            else:
                raise Exception(f"Failed to get customer: {result.get('message')}")
                
        except Exception as e:
            self.logger.error(f"Failed to get customer: {e}")
            raise
    
    async def create_plan(
        self,
        name: str,
        amount: float,
        currency: str,
        interval: str,
        duration: int
    ) -> FlutterwavePlan:
        """
        Create a subscription plan.
        
        Args:
            name: Plan name
            amount: Plan amount
            currency: Plan currency
            interval: Billing interval
            duration: Plan duration
            
        Returns:
            Plan data
        """
        try:
            url = f"{self.config.base_url}/payment-plans"
            
            data = {
                "name": name,
                "amount": amount,
                "currency": currency,
                "interval": interval,
                "duration": duration
            }
            
            response = self.session.post(url, json=data)
            response.raise_for_status()
            
            result = response.json()
            if result.get("status") == "success":
                plan_data = result["data"]
                
                return FlutterwavePlan(
                    id=plan_data["id"],
                    name=plan_data["name"],
                    amount=plan_data["amount"],
                    currency=plan_data["currency"],
                    interval=plan_data["interval"],
                    duration=plan_data["duration"],
                    status=plan_data["status"],
                    created_at=datetime.fromisoformat(plan_data["created_at"].replace("Z", "+00:00")) if plan_data.get("created_at") else None
                )
            else:
                raise Exception(f"Failed to create plan: {result.get('message')}")
                
        except Exception as e:
            self.logger.error(f"Failed to create plan: {e}")
            raise
    
    async def get_plans(self) -> List[FlutterwavePlan]:
        """
        Get all plans.
        
        Returns:
            List of plans
        """
        try:
            url = f"{self.config.base_url}/payment-plans"
            response = self.session.get(url)
            response.raise_for_status()
            
            result = response.json()
            if result.get("status") == "success":
                plans = []
                for plan_data in result["data"]:
                    plan = FlutterwavePlan(
                        id=plan_data["id"],
                        name=plan_data["name"],
                        amount=plan_data["amount"],
                        currency=plan_data["currency"],
                        interval=plan_data["interval"],
                        duration=plan_data["duration"],
                        status=plan_data["status"],
                        created_at=datetime.fromisoformat(plan_data["created_at"].replace("Z", "+00:00")) if plan_data.get("created_at") else None
                    )
                    plans.append(plan)
                
                return plans
            else:
                raise Exception(f"Failed to get plans: {result.get('message')}")
                
        except Exception as e:
            self.logger.error(f"Failed to get plans: {e}")
            raise
    
    async def process_webhook(self, payload: str, signature: str) -> FlutterwaveWebhookEvent:
        """
        Process webhook event.
        
        Args:
            payload: Webhook payload
            signature: Webhook signature
            
        Returns:
            Webhook event data
        """
        try:
            if not self._verify_webhook_signature(signature, payload):
                raise Exception("Invalid webhook signature")
            
            data = json.loads(payload)
            
            return FlutterwaveWebhookEvent(
                event=data.get("event"),
                data=data.get("data", {}),
                signature=signature,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Failed to process webhook: {e}")
            raise
    
    async def get_banks(self, country: str = "NG") -> List[Dict[str, Any]]:
        """
        Get banks for a country.
        
        Args:
            country: Country code
            
        Returns:
            List of banks
        """
        try:
            url = f"{self.config.base_url}/banks/{country}"
            response = self.session.get(url)
            response.raise_for_status()
            
            result = response.json()
            if result.get("status") == "success":
                return result["data"]
            else:
                raise Exception(f"Failed to get banks: {result.get('message')}")
                
        except Exception as e:
            self.logger.error(f"Failed to get banks: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the Flutterwave integration.
        
        Returns:
            Health check results
        """
        try:
            # Test API connectivity by getting plans
            plans = await self.get_plans()
            
            return {
                "status": "healthy",
                "base_url": self.config.base_url,
                "plans_count": len(plans),
                "api_connectivity": "successful",
                "webhook_secret_configured": self.config.webhook_secret is not None,
                "last_checked": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_checked": datetime.now().isoformat()
            }

