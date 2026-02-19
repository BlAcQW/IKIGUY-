"""
MTN Mobile Money Integration Module

This module provides integration with MTN Mobile Money for mobile payment processing,
money transfers, and financial services in African markets.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

try:
    import requests
    MTN_MOBILE_MONEY_AVAILABLE = True
except ImportError:
    MTN_MOBILE_MONEY_AVAILABLE = False
    logging.warning("MTN Mobile Money APIs not available. Install requests")

logger = logging.getLogger(__name__)


class MTNTransactionType(Enum):
    """MTN Mobile Money transaction types."""
    COLLECTION = "collection"
    DISBURSEMENT = "disbursement"
    REMITTANCE = "remittance"
    REFUND = "refund"
    BALANCE = "balance"


class MTNTransactionStatus(Enum):
    """MTN Mobile Money transaction status."""
    PENDING = "pending"
    SUCCESSFUL = "successful"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class MTNCurrency(Enum):
    """MTN Mobile Money supported currencies."""
    GHS = "GHS"  # Ghana Cedi
    UGX = "UGX"  # Uganda Shilling
    ZMW = "ZMW"  # Zambia Kwacha
    XAF = "XAF"  # Central African CFA Franc
    XOF = "XOF"  # West African CFA Franc
    RWF = "RWF"  # Rwanda Franc
    MWK = "MWK"  # Malawi Kwacha
    ZAR = "ZAR"  # South African Rand


@dataclass
class MTNConfig:
    """Configuration for MTN Mobile Money integration."""
    
    api_key: str
    """API key for authentication."""
    
    api_secret: str
    """API secret for authentication."""
    
    subscription_key: str
    """Subscription key for API access."""
    
    environment: str = "sandbox"
    """Environment (sandbox or production)."""
    
    country_code: str = "GH"
    """Country code for the MTN Mobile Money service."""
    
    currency: MTNCurrency = MTNCurrency.GHS
    """Currency for transactions."""
    
    timeout: int = 30
    """Request timeout in seconds."""
    
    verify_ssl: bool = True
    """Verify SSL certificates."""


@dataclass
class MTNTransaction:
    """MTN Mobile Money transaction data structure."""
    
    id: str
    """Transaction ID."""
    
    reference: str
    """External reference ID."""
    
    amount: float
    """Transaction amount."""
    
    currency: MTNCurrency
    """Transaction currency."""
    
    phone_number: str
    """Customer phone number."""
    
    transaction_type: MTNTransactionType
    """Transaction type."""
    
    status: MTNTransactionStatus
    """Transaction status."""
    
    description: Optional[str] = None
    """Transaction description."""
    
    payer_message: Optional[str] = None
    """Message to payer."""
    
    payee_note: Optional[str] = None
    """Note for payee."""
    
    created_at: Optional[datetime] = None
    """Creation timestamp."""
    
    updated_at: Optional[datetime] = None
    """Last update timestamp."""
    
    completed_at: Optional[datetime] = None
    """Completion timestamp."""


@dataclass
class MTNBalance:
    """MTN Mobile Money balance data structure."""
    
    available_balance: float
    """Available balance."""
    
    currency: MTNCurrency
    """Balance currency."""
    
    account_status: str
    """Account status."""
    
    last_updated: Optional[datetime] = None
    """Last update timestamp."""


@dataclass
class MTNUser:
    """MTN Mobile Money user data structure."""
    
    phone_number: str
    """User phone number."""
    
    account_status: str
    """Account status."""
    
    kyc_status: str
    """KYC status."""
    
    name: Optional[str] = None
    """User name."""
    
    email: Optional[str] = None
    """User email."""
    
    created_at: Optional[datetime] = None
    """Account creation timestamp."""


class MTNMobileMoneyIntegration:
    """MTN Mobile Money integration for mobile payment processing."""
    
    def __init__(self, config: MTNConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        if config.environment == "sandbox":
            self.base_url = "https://sandbox.momodeveloper.mtn.com"
        else:
            self.base_url = "https://proxy.momoapi.mtn.com"
        
        self.session = requests.Session()
        self.session.timeout = config.timeout
        self.session.verify = config.verify_ssl
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Reference-Id": "",
            "X-Target-Environment": config.environment,
            "Ocp-Apim-Subscription-Key": config.subscription_key
        })
        
        self.access_token = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with MTN Mobile Money API."""
        try:
            auth_url = f"{self.base_url}/collection/token/"
            
            auth_data = {
                "client_id": self.config.api_key,
                "client_secret": self.config.api_secret,
                "grant_type": "client_credentials"
            }
            
            response = self.session.post(auth_url, json=auth_data)
            response.raise_for_status()
            
            result = response.json()
            if "access_token" in result:
                self.access_token = result["access_token"]
                self.session.headers.update({
                    "Authorization": f"Bearer {self.access_token}"
                })
                self.logger.info("Successfully authenticated with MTN Mobile Money")
            else:
                raise Exception("Authentication failed")
                
        except Exception as e:
            self.logger.error(f"Failed to authenticate with MTN Mobile Money: {e}")
            raise
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a request to the MTN Mobile Money API."""
        try:
            url = f"{self.base_url}/{endpoint}"
            
            if method.upper() == "GET":
                response = self.session.get(url)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            if response.content:
                return response.json()
            return {}
            
        except Exception as e:
            self.logger.error(f"Failed to make {method} request to {endpoint}: {e}")
            raise
    
    async def request_payment(
        self,
        phone_number: str,
        amount: float,
        reference: str,
        description: Optional[str] = None,
        payer_message: Optional[str] = None,
        payee_note: Optional[str] = None
    ) -> MTNTransaction:
        """
        Request payment from a customer.
        
        Args:
            phone_number: Customer phone number
            amount: Payment amount
            reference: External reference ID
            description: Transaction description
            payer_message: Message to payer
            payee_note: Note for payee
            
        Returns:
            Transaction data
        """
        try:
            data = {
                "amount": str(amount),
                "currency": self.config.currency.value,
                "externalId": reference,
                "payer": {
                    "partyIdType": "MSISDN",
                    "partyId": phone_number
                },
                "payerMessage": payer_message or "Payment request",
                "payeeNote": payee_note or "Payment for services"
            }
            
            if description:
                data["payerMessage"] = description
            
            result = self._make_request("POST", "collection/v1_0/requesttopay", data)
            
            return MTNTransaction(
                id=result.get("transactionId", reference),
                reference=reference,
                amount=amount,
                currency=self.config.currency,
                phone_number=phone_number,
                transaction_type=MTNTransactionType.COLLECTION,
                status=MTNTransactionStatus.PENDING,
                description=description,
                payer_message=payer_message,
                payee_note=payee_note,
                created_at=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Failed to request payment: {e}")
            raise
    
    async def send_money(
        self,
        phone_number: str,
        amount: float,
        reference: str,
        description: Optional[str] = None,
        payer_message: Optional[str] = None,
        payee_note: Optional[str] = None
    ) -> MTNTransaction:
        """
        Send money to a customer.
        
        Args:
            phone_number: Customer phone number
            amount: Payment amount
            reference: External reference ID
            description: Transaction description
            payer_message: Message to payer
            payee_note: Note for payee
            
        Returns:
            Transaction data
        """
        try:
            data = {
                "amount": str(amount),
                "currency": self.config.currency.value,
                "externalId": reference,
                "payee": {
                    "partyIdType": "MSISDN",
                    "partyId": phone_number
                },
                "payerMessage": payer_message or "Money sent",
                "payeeNote": payee_note or "Payment received"
            }
            
            if description:
                data["payerMessage"] = description
            
            result = self._make_request("POST", "disbursement/v1_0/transfer", data)
            
            return MTNTransaction(
                id=result.get("transactionId", reference),
                reference=reference,
                amount=amount,
                currency=self.config.currency,
                phone_number=phone_number,
                transaction_type=MTNTransactionType.DISBURSEMENT,
                status=MTNTransactionStatus.PENDING,
                description=description,
                payer_message=payer_message,
                payee_note=payee_note,
                created_at=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Failed to send money: {e}")
            raise
    
    async def get_transaction_status(self, reference: str) -> MTNTransaction:
        """
        Get transaction status.
        
        Args:
            reference: External reference ID
            
        Returns:
            Transaction data
        """
        try:
            result = self._make_request("GET", f"collection/v1_0/requesttopay/{reference}")
            
            status_mapping = {
                "PENDING": MTNTransactionStatus.PENDING,
                "SUCCESSFUL": MTNTransactionStatus.SUCCESSFUL,
                "FAILED": MTNTransactionStatus.FAILED,
                "CANCELLED": MTNTransactionStatus.CANCELLED,
                "TIMEOUT": MTNTransactionStatus.TIMEOUT
            }
            
            return MTNTransaction(
                id=result.get("transactionId", reference),
                reference=reference,
                amount=float(result.get("amount", 0)),
                currency=MTNCurrency(result.get("currency", self.config.currency.value)),
                phone_number=result.get("payer", {}).get("partyId", ""),
                transaction_type=MTNTransactionType.COLLECTION,
                status=status_mapping.get(result.get("status", "PENDING"), MTNTransactionStatus.PENDING),
                description=result.get("payerMessage"),
                payer_message=result.get("payerMessage"),
                payee_note=result.get("payeeNote"),
                created_at=datetime.fromisoformat(result["date"].replace("Z", "+00:00")) if result.get("date") else None,
                updated_at=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get transaction status: {e}")
            raise
    
    async def get_account_balance(self) -> MTNBalance:
        """
        Get account balance.
        
        Returns:
            Balance data
        """
        try:
            result = self._make_request("GET", "collection/v1_0/account/balance")
            
            return MTNBalance(
                available_balance=float(result.get("availableBalance", 0)),
                currency=MTNCurrency(result.get("currency", self.config.currency.value)),
                account_status=result.get("accountStatus", "ACTIVE"),
                last_updated=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get account balance: {e}")
            raise
    
    async def get_user_info(self, phone_number: str) -> MTNUser:
        """
        Get user information.
        
        Args:
            phone_number: User phone number
            
        Returns:
            User data
        """
        try:
            data = {
                "partyIdType": "MSISDN",
                "partyId": phone_number
            }
            
            result = self._make_request("POST", "collection/v1_0/accountholder/msisdn/1/account/active", data)
            
            return MTNUser(
                phone_number=phone_number,
                name=result.get("name"),
                email=result.get("email"),
                account_status=result.get("accountStatus", "ACTIVE"),
                kyc_status=result.get("kycStatus", "VERIFIED"),
                created_at=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get user info: {e}")
            raise
    
    async def refund_transaction(
        self,
        original_reference: str,
        amount: float,
        reference: str,
        description: Optional[str] = None
    ) -> MTNTransaction:
        """
        Refund a transaction.
        
        Args:
            original_reference: Original transaction reference
            amount: Refund amount
            reference: New reference ID for refund
            description: Refund description
            
        Returns:
            Refund transaction data
        """
        try:
            data = {
                "amount": str(amount),
                "currency": self.config.currency.value,
                "externalId": reference,
                "payerMessage": description or "Refund for transaction",
                "payeeNote": f"Refund for {original_reference}"
            }
            
            result = self._make_request("POST", f"collection/v1_0/requesttopay/{original_reference}/refund", data)
            
            return MTNTransaction(
                id=result.get("transactionId", reference),
                reference=reference,
                amount=amount,
                currency=self.config.currency,
                phone_number="",  # Will be filled from original transaction
                transaction_type=MTNTransactionType.REFUND,
                status=MTNTransactionStatus.PENDING,
                description=description,
                created_at=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Failed to refund transaction: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the MTN Mobile Money integration.
        
        Returns:
            Health check results
        """
        try:
            # Test API connectivity by getting account balance
            balance = await self.get_account_balance()
            
            return {
                "status": "healthy",
                "base_url": self.base_url,
                "environment": self.config.environment,
                "country_code": self.config.country_code,
                "currency": self.config.currency.value,
                "available_balance": balance.available_balance,
                "api_connectivity": "successful",
                "last_checked": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_checked": datetime.now().isoformat()
            }

