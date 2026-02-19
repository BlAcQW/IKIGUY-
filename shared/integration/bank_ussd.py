"""
Bank USSD APIs Integration Module

This module provides integration with Bank USSD APIs for mobile banking operations,
USSD-based financial services, and mobile money transactions with comprehensive REST API support.
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
    BANK_USSD_AVAILABLE = True
except ImportError:
    BANK_USSD_AVAILABLE = False
    logging.warning("Bank USSD APIs not available. Install requests")

logger = logging.getLogger(__name__)


class USSDTransactionType(Enum):
    """USSD transaction types."""
    BALANCE_INQUIRY = "balance_inquiry"
    FUND_TRANSFER = "fund_transfer"
    AIRTIME_PURCHASE = "airtime_purchase"
    BILL_PAYMENT = "bill_payment"
    MINI_STATEMENT = "mini_statement"
    ACCOUNT_OPENING = "account_opening"
    LOAN_APPLICATION = "loan_application"
    CARD_MANAGEMENT = "card_management"


class USSDTransactionStatus(Enum):
    """USSD transaction status."""
    INITIATED = "initiated"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    INSUFFICIENT_FUNDS = "insufficient_funds"


class USSDServiceType(Enum):
    """USSD service types."""
    BANKING = "banking"
    MOBILE_MONEY = "mobile_money"
    AIRTIME = "airtime"
    BILL_PAYMENT = "bill_payment"
    LOANS = "loans"
    INSURANCE = "insurance"


class USSDChannel(Enum):
    """USSD channels."""
    MTN = "mtn"
    VODAFONE = "vodafone"
    AIRTEL = "airtel"
    GLO = "glo"
    TIGO = "tigo"


@dataclass
class USSDConfig:
    """Configuration for Bank USSD APIs integration."""
    api_key: str
    bank_code: str
    ussd_code: str
    base_url: str = "https://api.bankussd.com/v1"
    timeout: int = 30
    verify_ssl: bool = True
    api_version: str = "v1"


@dataclass
class USSDTransaction:
    """USSD transaction data."""
    transaction_id: str
    session_id: str
    msisdn: str
    transaction_type: USSDTransactionType
    status: USSDTransactionStatus = USSDTransactionStatus.INITIATED
    amount: float = 0.0
    currency: str = "GHS"
    recipient_msisdn: str = ""
    recipient_name: str = ""
    description: str = ""
    service_type: USSDServiceType = USSDServiceType.BANKING
    channel: USSDChannel = USSDChannel.MTN
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class USSDBalance:
    """USSD balance data."""
    msisdn: str
    account_number: str
    available_balance: float
    ledger_balance: float
    currency: str = "GHS"
    account_type: str = "savings"
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class USSDStatement:
    """USSD statement data."""
    msisdn: str
    account_number: str
    start_date: datetime
    end_date: datetime
    transactions: List[USSDTransaction] = field(default_factory=list)
    opening_balance: float = 0.0
    closing_balance: float = 0.0
    currency: str = "GHS"


@dataclass
class USSDMenu:
    """USSD menu structure."""
    menu_id: str
    title: str
    options: List[Dict[str, str]] = field(default_factory=list)
    parent_menu_id: Optional[str] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class USSDUser:
    """USSD user data."""
    msisdn: str
    account_number: str
    full_name: str
    email: str = ""
    is_registered: bool = False
    is_active: bool = True
    registration_date: Optional[datetime] = None
    last_login: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BankUSSDIntegration:
    """Bank USSD APIs integration for mobile banking operations."""
    
    def __init__(self, config: USSDConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        self.session = requests.Session()
        self.session.timeout = config.timeout
        self.session.verify = config.verify_ssl
        
        self.session.headers.update({
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
            "X-Bank-Code": config.bank_code,
            "X-USSD-Code": config.ussd_code
        })
        
        self.base_url = f"{config.base_url}/{config.api_version}"
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request to Bank USSD APIs."""
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
    
    async def initiate_session(self, msisdn: str, service_type: USSDServiceType = USSDServiceType.BANKING) -> str:
        """Initiate a USSD session."""
        data = {
            "msisdn": msisdn,
            "service_type": service_type.value,
            "ussd_code": self.config.ussd_code
        }
        
        response = await asyncio.to_thread(
            self._make_request, "POST", "sessions/initiate", data
        )
        
        return response["session_id"]
    
    async def send_menu(self, session_id: str, menu_id: str, user_input: str = "") -> Dict[str, Any]:
        """Send USSD menu to user."""
        data = {
            "session_id": session_id,
            "menu_id": menu_id,
            "user_input": user_input
        }
        
        return await asyncio.to_thread(
            self._make_request, "POST", "sessions/menu", data
        )
    
    async def check_balance(self, msisdn: str, account_number: Optional[str] = None) -> USSDBalance:
        """Check account balance via USSD."""
        data = {
            "msisdn": msisdn,
            "account_number": account_number
        }
        
        response = await asyncio.to_thread(
            self._make_request, "POST", "banking/balance", data
        )
        
        return USSDBalance(
            msisdn=msisdn,
            account_number=response["account_number"],
            available_balance=response["available_balance"],
            ledger_balance=response["ledger_balance"],
            currency=response["currency"],
            account_type=response["account_type"],
            last_updated=datetime.fromisoformat(response["last_updated"])
        )
    
    async def transfer_funds(self, session_id: str, recipient_msisdn: str, 
                           recipient_name: str, amount: float, description: str = "") -> USSDTransaction:
        """Transfer funds via USSD."""
        data = {
            "session_id": session_id,
            "recipient_msisdn": recipient_msisdn,
            "recipient_name": recipient_name,
            "amount": amount,
            "currency": "GHS",
            "description": description
        }
        
        response = await asyncio.to_thread(
            self._make_request, "POST", "banking/transfer", data
        )
        
        return USSDTransaction(
            transaction_id=response["transaction_id"],
            session_id=session_id,
            msisdn=response["msisdn"],
            transaction_type=USSDTransactionType.FUND_TRANSFER,
            status=USSDTransactionStatus(response["status"]),
            amount=amount,
            recipient_msisdn=recipient_msisdn,
            recipient_name=recipient_name,
            description=description,
            created_at=datetime.fromisoformat(response["created_at"]),
            metadata=response
        )
    
    async def purchase_airtime(self, session_id: str, recipient_msisdn: str, 
                             amount: float, network: USSDChannel) -> USSDTransaction:
        """Purchase airtime via USSD."""
        data = {
            "session_id": session_id,
            "recipient_msisdn": recipient_msisdn,
            "amount": amount,
            "network": network.value
        }
        
        response = await asyncio.to_thread(
            self._make_request, "POST", "airtime/purchase", data
        )
        
        return USSDTransaction(
            transaction_id=response["transaction_id"],
            session_id=session_id,
            msisdn=response["msisdn"],
            transaction_type=USSDTransactionType.AIRTIME_PURCHASE,
            status=USSDTransactionStatus(response["status"]),
            amount=amount,
            recipient_msisdn=recipient_msisdn,
            service_type=USSDServiceType.AIRTIME,
            channel=network,
            created_at=datetime.fromisoformat(response["created_at"]),
            metadata=response
        )
    
    async def pay_bill(self, session_id: str, bill_type: str, bill_number: str, 
                      amount: float, customer_name: str = "") -> USSDTransaction:
        """Pay bills via USSD."""
        data = {
            "session_id": session_id,
            "bill_type": bill_type,
            "bill_number": bill_number,
            "amount": amount,
            "customer_name": customer_name
        }
        
        response = await asyncio.to_thread(
            self._make_request, "POST", "bills/pay", data
        )
        
        return USSDTransaction(
            transaction_id=response["transaction_id"],
            session_id=session_id,
            msisdn=response["msisdn"],
            transaction_type=USSDTransactionType.BILL_PAYMENT,
            status=USSDTransactionStatus(response["status"]),
            amount=amount,
            service_type=USSDServiceType.BILL_PAYMENT,
            description=f"Bill payment for {bill_type}",
            created_at=datetime.fromisoformat(response["created_at"]),
            metadata=response
        )
    
    async def get_mini_statement(self, msisdn: str, account_number: Optional[str] = None) -> USSDStatement:
        """Get mini statement via USSD."""
        data = {
            "msisdn": msisdn,
            "account_number": account_number
        }
        
        response = await asyncio.to_thread(
            self._make_request, "POST", "banking/statement", data
        )
        
        transactions = []
        for tx_data in response["transactions"]:
            transactions.append(USSDTransaction(
                transaction_id=tx_data["transaction_id"],
                session_id=tx_data.get("session_id", ""),
                msisdn=msisdn,
                transaction_type=USSDTransactionType(tx_data["transaction_type"]),
                status=USSDTransactionStatus(tx_data["status"]),
                amount=tx_data["amount"],
                currency=tx_data["currency"],
                recipient_msisdn=tx_data.get("recipient_msisdn", ""),
                recipient_name=tx_data.get("recipient_name", ""),
                description=tx_data.get("description", ""),
                created_at=datetime.fromisoformat(tx_data["created_at"]),
                metadata=tx_data
            ))
        
        return USSDStatement(
            msisdn=msisdn,
            account_number=response["account_number"],
            start_date=datetime.fromisoformat(response["start_date"]),
            end_date=datetime.fromisoformat(response["end_date"]),
            transactions=transactions,
            opening_balance=response["opening_balance"],
            closing_balance=response["closing_balance"],
            currency=response["currency"]
        )
    
    async def register_user(self, msisdn: str, full_name: str, email: str = "", 
                          account_number: Optional[str] = None) -> USSDUser:
        """Register a new USSD user."""
        data = {
            "msisdn": msisdn,
            "full_name": full_name,
            "email": email,
            "account_number": account_number
        }
        
        response = await asyncio.to_thread(
            self._make_request, "POST", "users/register", data
        )
        
        return USSDUser(
            msisdn=msisdn,
            account_number=response["account_number"],
            full_name=full_name,
            email=email,
            is_registered=True,
            registration_date=datetime.fromisoformat(response["registration_date"]),
            metadata=response
        )
    
    async def get_user_info(self, msisdn: str) -> USSDUser:
        """Get user information."""
        response = await asyncio.to_thread(
            self._make_request, "GET", f"users/{msisdn}"
        )
        
        return USSDUser(
            msisdn=msisdn,
            account_number=response["account_number"],
            full_name=response["full_name"],
            email=response.get("email", ""),
            is_registered=response["is_registered"],
            is_active=response["is_active"],
            registration_date=datetime.fromisoformat(response["registration_date"]) if response.get("registration_date") else None,
            last_login=datetime.fromisoformat(response["last_login"]) if response.get("last_login") else None,
            metadata=response
        )
    
    async def get_transaction_status(self, transaction_id: str) -> USSDTransaction:
        """Get transaction status."""
        response = await asyncio.to_thread(
            self._make_request, "GET", f"transactions/{transaction_id}"
        )
        
        return USSDTransaction(
            transaction_id=response["transaction_id"],
            session_id=response["session_id"],
            msisdn=response["msisdn"],
            transaction_type=USSDTransactionType(response["transaction_type"]),
            status=USSDTransactionStatus(response["status"]),
            amount=response["amount"],
            currency=response["currency"],
            recipient_msisdn=response.get("recipient_msisdn", ""),
            recipient_name=response.get("recipient_name", ""),
            description=response.get("description", ""),
            service_type=USSDServiceType(response["service_type"]),
            channel=USSDChannel(response["channel"]),
            created_at=datetime.fromisoformat(response["created_at"]),
            updated_at=datetime.fromisoformat(response["updated_at"]),
            metadata=response
        )
    
    async def end_session(self, session_id: str) -> bool:
        """End a USSD session."""
        try:
            await asyncio.to_thread(
                self._make_request, "POST", f"sessions/{session_id}/end"
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to end session {session_id}: {e}")
            return False
    
    async def get_available_services(self) -> List[Dict[str, Any]]:
        """Get available USSD services."""
        response = await asyncio.to_thread(
            self._make_request, "GET", "services"
        )
        
        return response["services"]
    
    async def get_bill_types(self) -> List[Dict[str, Any]]:
        """Get available bill types."""
        response = await asyncio.to_thread(
            self._make_request, "GET", "bills/types"
        )
        
        return response["bill_types"]
    
    async def validate_bill(self, bill_type: str, bill_number: str) -> Dict[str, Any]:
        """Validate bill details."""
        data = {
            "bill_type": bill_type,
            "bill_number": bill_number
        }
        
        return await asyncio.to_thread(
            self._make_request, "POST", "bills/validate", data
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
