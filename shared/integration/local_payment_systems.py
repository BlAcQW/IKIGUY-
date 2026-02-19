"""
Local Payment Systems Integration Module

This module provides integration with local payment systems for regional payment methods,
local banking systems, and indigenous payment solutions with comprehensive REST API support.
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
    LOCAL_PAYMENT_AVAILABLE = True
except ImportError:
    LOCAL_PAYMENT_AVAILABLE = False
    logging.warning("Local Payment Systems APIs not available. Install requests")

logger = logging.getLogger(__name__)


class LocalPaymentType(Enum):
    """Local payment system types."""
    BANK_TRANSFER = "bank_transfer"
    MOBILE_MONEY = "mobile_money"
    CASH_PICKUP = "cash_pickup"
    AGENT_PAYMENT = "agent_payment"
    USSD_PAYMENT = "ussd_payment"
    QR_CODE_PAYMENT = "qr_code_payment"
    CARD_PAYMENT = "card_payment"
    DIGITAL_WALLET = "digital_wallet"
    BANK_DEPOSIT = "bank_deposit"
    CHECK_PAYMENT = "check_payment"


class LocalPaymentStatus(Enum):
    """Local payment system status."""
    INITIATED = "initiated"
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    REFUNDED = "refunded"


class LocalPaymentProvider(Enum):
    """Local payment providers."""
    # Ghana
    MTN_MOMO = "mtn_momo"
    VODAFONE_CASH = "vodafone_cash"
    AIRTEL_MONEY = "airtel_money"
    GLO_MONEY = "glo_money"
    TIGO_CASH = "tigo_cash"
    # Nigeria
    PAGA = "paga"
    OPAGO = "opago"
    # Kenya
    MPESA = "mpesa"
    AIRTEL_MONEY_KE = "airtel_money_ke"
    # South Africa
    VODACOM_MPESA = "vodacom_mpesa"
    # Local Banks
    LOCAL_BANK = "local_bank"
    MICROFINANCE = "microfinance"
    COOPERATIVE = "cooperative"


class LocalPaymentCurrency(Enum):
    """Local payment currencies."""
    GHS = "GHS"  # Ghana Cedi
    NGN = "NGN"  # Nigerian Naira
    KES = "KES"  # Kenyan Shilling
    ZAR = "ZAR"  # South African Rand
    USD = "USD"  # US Dollar
    EUR = "EUR"  # Euro
    GBP = "GBP"  # British Pound


@dataclass
class LocalPaymentConfig:
    """Configuration for Local Payment Systems integration."""
    api_key: str
    merchant_id: str
    provider: LocalPaymentProvider
    base_url: str = "https://api.localpayments.com/v1"
    timeout: int = 30
    verify_ssl: bool = True
    api_version: str = "v1"


@dataclass
class LocalPaymentTransaction:
    """Local payment transaction data."""
    transaction_id: str
    reference: str
    amount: float
    currency: LocalPaymentCurrency = LocalPaymentCurrency.GHS
    payment_type: LocalPaymentType = LocalPaymentType.MOBILE_MONEY
    provider: LocalPaymentProvider = LocalPaymentProvider.MTN_MOMO
    status: LocalPaymentStatus = LocalPaymentStatus.INITIATED
    sender_name: str = ""
    sender_phone: str = ""
    sender_email: str = ""
    recipient_name: str = ""
    recipient_phone: str = ""
    recipient_account: str = ""
    recipient_bank: str = ""
    description: str = ""
    fee: float = 0.0
    exchange_rate: float = 1.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LocalPaymentAccount:
    """Local payment account data."""
    account_id: str
    account_name: str
    account_number: str = ""
    phone_number: str = ""
    email: str = ""
    provider: LocalPaymentProvider = LocalPaymentProvider.MTN_MOMO
    account_type: str = "mobile_money"
    balance: float = 0.0
    currency: LocalPaymentCurrency = LocalPaymentCurrency.GHS
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LocalPaymentBalance:
    """Local payment balance data."""
    account_id: str
    available_balance: float
    ledger_balance: float
    currency: LocalPaymentCurrency = LocalPaymentCurrency.GHS
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class LocalPaymentProviderInfo:
    """Local payment provider information."""
    provider: LocalPaymentProvider
    name: str
    country: str
    supported_currencies: List[LocalPaymentCurrency] = field(default_factory=list)
    supported_payment_types: List[LocalPaymentType] = field(default_factory=list)
    transaction_limits: Dict[str, float] = field(default_factory=dict)
    fees: Dict[str, float] = field(default_factory=dict)
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LocalPaymentExchangeRate:
    """Local payment exchange rate data."""
    from_currency: LocalPaymentCurrency
    to_currency: LocalPaymentCurrency
    rate: float
    inverse_rate: float
    last_updated: datetime = field(default_factory=datetime.now)
    source: str = "local_payment_system"


class LocalPaymentSystemsIntegration:
    """Local Payment Systems integration for regional payment methods."""
    
    def __init__(self, config: LocalPaymentConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        self.session = requests.Session()
        self.session.timeout = config.timeout
        self.session.verify = config.verify_ssl
        
        self.session.headers.update({
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
            "X-Merchant-ID": config.merchant_id,
            "X-Provider": config.provider.value
        })
        
        self.base_url = f"{config.base_url}/{config.api_version}"
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request to Local Payment Systems API."""
        url = f"{self.base_url}/{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=params)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data)
            elif method.upper() == "DELETE":
                response = self.session.delete(url)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {e}")
            raise
    
    async def initiate_payment(self, amount: float, currency: LocalPaymentCurrency,
                              payment_type: LocalPaymentType, recipient_phone: str,
                              recipient_name: str, description: str = "",
                              sender_name: str = "", sender_phone: str = "",
                              sender_email: str = "") -> LocalPaymentTransaction:
        """Initiate a local payment."""
        data = {
            "amount": amount,
            "currency": currency.value,
            "payment_type": payment_type.value,
            "provider": self.config.provider.value,
            "recipient_phone": recipient_phone,
            "recipient_name": recipient_name,
            "description": description,
            "sender_name": sender_name,
            "sender_phone": sender_phone,
            "sender_email": sender_email
        }
        
        response = await asyncio.to_thread(
            self._make_request, "POST", "payments/initiate", data
        )
        
        return LocalPaymentTransaction(
            transaction_id=response["transaction_id"],
            reference=response["reference"],
            amount=amount,
            currency=currency,
            payment_type=payment_type,
            provider=self.config.provider,
            status=LocalPaymentStatus(response["status"]),
            sender_name=sender_name,
            sender_phone=sender_phone,
            sender_email=sender_email,
            recipient_name=recipient_name,
            recipient_phone=recipient_phone,
            description=description,
            fee=response.get("fee", 0.0),
            exchange_rate=response.get("exchange_rate", 1.0),
            created_at=datetime.fromisoformat(response["created_at"]),
            expires_at=datetime.fromisoformat(response["expires_at"]) if response.get("expires_at") else None,
            metadata=response
        )
    
    async def bank_transfer(self, amount: float, currency: LocalPaymentCurrency,
                           recipient_account: str, recipient_name: str,
                           recipient_bank: str, description: str = "",
                           sender_name: str = "", sender_account: str = "") -> LocalPaymentTransaction:
        """Initiate a bank transfer."""
        data = {
            "amount": amount,
            "currency": currency.value,
            "payment_type": LocalPaymentType.BANK_TRANSFER.value,
            "provider": self.config.provider.value,
            "recipient_account": recipient_account,
            "recipient_name": recipient_name,
            "recipient_bank": recipient_bank,
            "description": description,
            "sender_name": sender_name,
            "sender_account": sender_account
        }
        
        response = await asyncio.to_thread(
            self._make_request, "POST", "payments/bank-transfer", data
        )
        
        return LocalPaymentTransaction(
            transaction_id=response["transaction_id"],
            reference=response["reference"],
            amount=amount,
            currency=currency,
            payment_type=LocalPaymentType.BANK_TRANSFER,
            provider=self.config.provider,
            status=LocalPaymentStatus(response["status"]),
            sender_name=sender_name,
            sender_account=sender_account,
            recipient_name=recipient_name,
            recipient_account=recipient_account,
            recipient_bank=recipient_bank,
            description=description,
            fee=response.get("fee", 0.0),
            exchange_rate=response.get("exchange_rate", 1.0),
            created_at=datetime.fromisoformat(response["created_at"]),
            metadata=response
        )
    
    async def cash_pickup(self, amount: float, currency: LocalPaymentCurrency,
                         recipient_name: str, recipient_phone: str,
                         pickup_location: str, description: str = "",
                         sender_name: str = "", sender_phone: str = "") -> LocalPaymentTransaction:
        """Initiate a cash pickup payment."""
        data = {
            "amount": amount,
            "currency": currency.value,
            "payment_type": LocalPaymentType.CASH_PICKUP.value,
            "provider": self.config.provider.value,
            "recipient_name": recipient_name,
            "recipient_phone": recipient_phone,
            "pickup_location": pickup_location,
            "description": description,
            "sender_name": sender_name,
            "sender_phone": sender_phone
        }
        
        response = await asyncio.to_thread(
            self._make_request, "POST", "payments/cash-pickup", data
        )
        
        return LocalPaymentTransaction(
            transaction_id=response["transaction_id"],
            reference=response["reference"],
            amount=amount,
            currency=currency,
            payment_type=LocalPaymentType.CASH_PICKUP,
            provider=self.config.provider,
            status=LocalPaymentStatus(response["status"]),
            sender_name=sender_name,
            sender_phone=sender_phone,
            recipient_name=recipient_name,
            recipient_phone=recipient_phone,
            description=description,
            fee=response.get("fee", 0.0),
            exchange_rate=response.get("exchange_rate", 1.0),
            created_at=datetime.fromisoformat(response["created_at"]),
            expires_at=datetime.fromisoformat(response["expires_at"]) if response.get("expires_at") else None,
            metadata=response
        )
    
    async def get_transaction_status(self, transaction_id: str) -> LocalPaymentTransaction:
        """Get transaction status."""
        response = await asyncio.to_thread(
            self._make_request, "GET", f"transactions/{transaction_id}"
        )
        
        return LocalPaymentTransaction(
            transaction_id=response["transaction_id"],
            reference=response["reference"],
            amount=response["amount"],
            currency=LocalPaymentCurrency(response["currency"]),
            payment_type=LocalPaymentType(response["payment_type"]),
            provider=LocalPaymentProvider(response["provider"]),
            status=LocalPaymentStatus(response["status"]),
            sender_name=response.get("sender_name", ""),
            sender_phone=response.get("sender_phone", ""),
            sender_email=response.get("sender_email", ""),
            recipient_name=response.get("recipient_name", ""),
            recipient_phone=response.get("recipient_phone", ""),
            recipient_account=response.get("recipient_account", ""),
            recipient_bank=response.get("recipient_bank", ""),
            description=response.get("description", ""),
            fee=response.get("fee", 0.0),
            exchange_rate=response.get("exchange_rate", 1.0),
            created_at=datetime.fromisoformat(response["created_at"]),
            updated_at=datetime.fromisoformat(response["updated_at"]),
            expires_at=datetime.fromisoformat(response["expires_at"]) if response.get("expires_at") else None,
            metadata=response
        )
    
    async def get_account_balance(self, account_id: str) -> LocalPaymentBalance:
        """Get account balance."""
        response = await asyncio.to_thread(
            self._make_request, "GET", f"accounts/{account_id}/balance"
        )
        
        return LocalPaymentBalance(
            account_id=account_id,
            available_balance=response["available_balance"],
            ledger_balance=response["ledger_balance"],
            currency=LocalPaymentCurrency(response["currency"]),
            last_updated=datetime.fromisoformat(response["last_updated"])
        )
    
    async def create_account(self, account_name: str, phone_number: str = "",
                           email: str = "", account_type: str = "mobile_money") -> LocalPaymentAccount:
        """Create a new payment account."""
        data = {
            "account_name": account_name,
            "phone_number": phone_number,
            "email": email,
            "account_type": account_type,
            "provider": self.config.provider.value
        }
        
        response = await asyncio.to_thread(
            self._make_request, "POST", "accounts", data
        )
        
        return LocalPaymentAccount(
            account_id=response["account_id"],
            account_name=account_name,
            account_number=response.get("account_number", ""),
            phone_number=phone_number,
            email=email,
            provider=self.config.provider,
            account_type=account_type,
            balance=response.get("balance", 0.0),
            currency=LocalPaymentCurrency(response["currency"]),
            is_active=response.get("is_active", True),
            is_verified=response.get("is_verified", False),
            created_at=datetime.fromisoformat(response["created_at"]),
            metadata=response
        )
    
    async def get_account(self, account_id: str) -> LocalPaymentAccount:
        """Get account details."""
        response = await asyncio.to_thread(
            self._make_request, "GET", f"accounts/{account_id}"
        )
        
        return LocalPaymentAccount(
            account_id=response["account_id"],
            account_name=response["account_name"],
            account_number=response.get("account_number", ""),
            phone_number=response.get("phone_number", ""),
            email=response.get("email", ""),
            provider=LocalPaymentProvider(response["provider"]),
            account_type=response["account_type"],
            balance=response.get("balance", 0.0),
            currency=LocalPaymentCurrency(response["currency"]),
            is_active=response.get("is_active", True),
            is_verified=response.get("is_verified", False),
            created_at=datetime.fromisoformat(response["created_at"]),
            metadata=response
        )
    
    async def get_transaction_history(self, account_id: str,
                                     start_date: Optional[datetime] = None,
                                     end_date: Optional[datetime] = None,
                                     limit: int = 100) -> List[LocalPaymentTransaction]:
        """Get transaction history."""
        params = {"limit": limit}
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()
        
        response = await asyncio.to_thread(
            self._make_request, "GET", f"accounts/{account_id}/transactions", params=params
        )
        
        transactions = []
        for tx_data in response["transactions"]:
            transactions.append(LocalPaymentTransaction(
                transaction_id=tx_data["transaction_id"],
                reference=tx_data["reference"],
                amount=tx_data["amount"],
                currency=LocalPaymentCurrency(tx_data["currency"]),
                payment_type=LocalPaymentType(tx_data["payment_type"]),
                provider=LocalPaymentProvider(tx_data["provider"]),
                status=LocalPaymentStatus(tx_data["status"]),
                sender_name=tx_data.get("sender_name", ""),
                sender_phone=tx_data.get("sender_phone", ""),
                sender_email=tx_data.get("sender_email", ""),
                recipient_name=tx_data.get("recipient_name", ""),
                recipient_phone=tx_data.get("recipient_phone", ""),
                recipient_account=tx_data.get("recipient_account", ""),
                recipient_bank=tx_data.get("recipient_bank", ""),
                description=tx_data.get("description", ""),
                fee=tx_data.get("fee", 0.0),
                exchange_rate=tx_data.get("exchange_rate", 1.0),
                created_at=datetime.fromisoformat(tx_data["created_at"]),
                updated_at=datetime.fromisoformat(tx_data["updated_at"]),
                expires_at=datetime.fromisoformat(tx_data["expires_at"]) if tx_data.get("expires_at") else None,
                metadata=tx_data
            ))
        
        return transactions
    
    async def cancel_transaction(self, transaction_id: str, reason: str = "") -> bool:
        """Cancel a pending transaction."""
        data = {"reason": reason} if reason else {}
        
        try:
            await asyncio.to_thread(
                self._make_request, "POST", f"transactions/{transaction_id}/cancel", data
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to cancel transaction {transaction_id}: {e}")
            return False
    
    async def refund_transaction(self, transaction_id: str, amount: Optional[float] = None,
                                reason: str = "") -> bool:
        """Refund a completed transaction."""
        data = {"reason": reason}
        if amount:
            data["amount"] = amount
        
        try:
            await asyncio.to_thread(
                self._make_request, "POST", f"transactions/{transaction_id}/refund", data
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to refund transaction {transaction_id}: {e}")
            return False
    
    async def get_exchange_rate(self, from_currency: LocalPaymentCurrency,
                               to_currency: LocalPaymentCurrency) -> LocalPaymentExchangeRate:
        """Get exchange rate between currencies."""
        params = {
            "from_currency": from_currency.value,
            "to_currency": to_currency.value
        }
        
        response = await asyncio.to_thread(
            self._make_request, "GET", "exchange-rates", params=params
        )
        
        return LocalPaymentExchangeRate(
            from_currency=from_currency,
            to_currency=to_currency,
            rate=response["rate"],
            inverse_rate=response["inverse_rate"],
            last_updated=datetime.fromisoformat(response["last_updated"]),
            source=response.get("source", "local_payment_system")
        )
    
    async def get_provider_info(self, provider: Optional[LocalPaymentProvider] = None) -> LocalPaymentProviderInfo:
        """Get provider information."""
        provider_value = provider.value if provider else self.config.provider.value
        
        response = await asyncio.to_thread(
            self._make_request, "GET", f"providers/{provider_value}"
        )
        
        return LocalPaymentProviderInfo(
            provider=LocalPaymentProvider(response["provider"]),
            name=response["name"],
            country=response["country"],
            supported_currencies=[LocalPaymentCurrency(c) for c in response["supported_currencies"]],
            supported_payment_types=[LocalPaymentType(pt) for pt in response["supported_payment_types"]],
            transaction_limits=response.get("transaction_limits", {}),
            fees=response.get("fees", {}),
            is_active=response.get("is_active", True),
            metadata=response
        )
    
    async def get_available_providers(self, country: Optional[str] = None) -> List[LocalPaymentProviderInfo]:
        """Get available payment providers."""
        params = {}
        if country:
            params["country"] = country
        
        response = await asyncio.to_thread(
            self._make_request, "GET", "providers", params=params
        )
        
        providers = []
        for provider_data in response["providers"]:
            providers.append(LocalPaymentProviderInfo(
                provider=LocalPaymentProvider(provider_data["provider"]),
                name=provider_data["name"],
                country=provider_data["country"],
                supported_currencies=[LocalPaymentCurrency(c) for c in provider_data["supported_currencies"]],
                supported_payment_types=[LocalPaymentType(pt) for pt in provider_data["supported_payment_types"]],
                transaction_limits=provider_data.get("transaction_limits", {}),
                fees=provider_data.get("fees", {}),
                is_active=provider_data.get("is_active", True),
                metadata=provider_data
            ))
        
        return providers
    
    async def validate_recipient(self, recipient_phone: str, provider: Optional[LocalPaymentProvider] = None) -> Dict[str, Any]:
        """Validate recipient phone number."""
        data = {
            "recipient_phone": recipient_phone,
            "provider": provider.value if provider else self.config.provider.value
        }
        
        return await asyncio.to_thread(
            self._make_request, "POST", "validation/recipient", data
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """Test API connectivity and health."""
        try:
            response = await asyncio.to_thread(
                self._make_request, "GET", "health"
            )
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "details": response
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
