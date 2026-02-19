"""
Ghana Interbank Payment Switch Integration Module

This module provides integration with the Ghana Interbank Payment and Settlement System (GhIPSS)
for banking operations, payment processing, and financial transactions with comprehensive REST API support.
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
    GHANA_INTERBANK_AVAILABLE = True
except ImportError:
    GHANA_INTERBANK_AVAILABLE = False
    logging.warning("Ghana Interbank APIs not available. Install requests")

logger = logging.getLogger(__name__)


class GhIPSSTransactionType(Enum):
    """Ghana Interbank Payment Switch transaction types."""
    EFT = "eft"  # Electronic Funds Transfer
    RTGS = "rtgs"  # Real Time Gross Settlement
    ACH = "ach"  # Automated Clearing House
    MOBILE_MONEY = "mobile_money"  # Mobile Money Transfer
    CARD_PAYMENT = "card_payment"  # Card-based Payment
    DIRECT_DEBIT = "direct_debit"  # Direct Debit
    STANDING_ORDER = "standing_order"  # Standing Order


class GhIPSSTransactionStatus(Enum):
    """Ghana Interbank Payment Switch transaction status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REVERSED = "reversed"
    DECLINED = "declined"


class GhIPSSAccountType(Enum):
    """Ghana Interbank Payment Switch account types."""
    SAVINGS = "savings"
    CURRENT = "current"
    FIXED_DEPOSIT = "fixed_deposit"
    CORPORATE = "corporate"
    GOVERNMENT = "government"


class GhIPSSBankCode(Enum):
    """Ghana Interbank Payment Switch bank codes."""
    GCB_BANK = "GCB"
    ECOBANK = "ECO"
    ABSA_BANK = "ABS"
    STANBIC_BANK = "STB"
    FIDELITY_BANK = "FID"
    CAL_BANK = "CAL"
    UBA_BANK = "UBA"
    ZENITH_BANK = "ZEN"
    ACCESS_BANK = "ACC"
    FBN_BANK = "FBN"
    # Add more bank codes as needed


@dataclass
class GhIPSSConfig:
    """Configuration for Ghana Interbank Payment Switch integration."""
    api_key: str
    merchant_id: str
    bank_code: str
    account_number: str
    base_url: str = "https://api.ghipss.com/v1"
    timeout: int = 30
    verify_ssl: bool = True
    api_version: str = "v1"


@dataclass
class GhIPSSTransaction:
    """Ghana Interbank Payment Switch transaction data."""
    transaction_id: str
    reference: str
    amount: float
    currency: str = "GHS"
    transaction_type: GhIPSSTransactionType = GhIPSSTransactionType.EFT
    status: GhIPSSTransactionStatus = GhIPSSTransactionStatus.PENDING
    sender_account: str = ""
    sender_name: str = ""
    sender_bank: str = ""
    recipient_account: str = ""
    recipient_name: str = ""
    recipient_bank: str = ""
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GhIPSSAccount:
    """Ghana Interbank Payment Switch account data."""
    account_number: str
    account_name: str
    bank_code: str
    bank_name: str
    account_type: GhIPSSAccountType = GhIPSSAccountType.CURRENT
    balance: float = 0.0
    currency: str = "GHS"
    status: str = "active"
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GhIPSSBalance:
    """Ghana Interbank Payment Switch balance data."""
    account_number: str
    available_balance: float
    ledger_balance: float
    currency: str = "GHS"
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class GhIPSSStatement:
    """Ghana Interbank Payment Switch statement data."""
    account_number: str
    start_date: datetime
    end_date: datetime
    transactions: List[GhIPSSTransaction] = field(default_factory=list)
    opening_balance: float = 0.0
    closing_balance: float = 0.0
    currency: str = "GHS"


class GhIPSSIntegration:
    """Ghana Interbank Payment Switch integration for banking operations."""
    
    def __init__(self, config: GhIPSSConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        self.session = requests.Session()
        self.session.timeout = config.timeout
        self.session.verify = config.verify_ssl
        
        self.session.headers.update({
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
            "X-Merchant-ID": config.merchant_id,
            "X-Bank-Code": config.bank_code
        })
        
        self.base_url = f"{config.base_url}/{config.api_version}"
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request to Ghana Interbank Payment Switch API."""
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
    
    async def initiate_transfer(self, recipient_account: str, recipient_name: str, 
                               recipient_bank: str, amount: float, description: str = "",
                               transaction_type: GhIPSSTransactionType = GhIPSSTransactionType.EFT) -> GhIPSSTransaction:
        """Initiate a bank transfer."""
        data = {
            "sender_account": self.config.account_number,
            "sender_bank": self.config.bank_code,
            "recipient_account": recipient_account,
            "recipient_name": recipient_name,
            "recipient_bank": recipient_bank,
            "amount": amount,
            "currency": "GHS",
            "transaction_type": transaction_type.value,
            "description": description
        }
        
        response = await asyncio.to_thread(
            self._make_request, "POST", "transfers", data
        )
        
        return GhIPSSTransaction(
            transaction_id=response["transaction_id"],
            reference=response["reference"],
            amount=amount,
            transaction_type=transaction_type,
            sender_account=self.config.account_number,
            sender_bank=self.config.bank_code,
            recipient_account=recipient_account,
            recipient_name=recipient_name,
            recipient_bank=recipient_bank,
            description=description,
            created_at=datetime.fromisoformat(response["created_at"]),
            metadata=response
        )
    
    async def get_transaction_status(self, transaction_id: str) -> GhIPSSTransaction:
        """Get transaction status by ID."""
        response = await asyncio.to_thread(
            self._make_request, "GET", f"transactions/{transaction_id}"
        )
        
        return GhIPSSTransaction(
            transaction_id=response["transaction_id"],
            reference=response["reference"],
            amount=response["amount"],
            currency=response["currency"],
            transaction_type=GhIPSSTransactionType(response["transaction_type"]),
            status=GhIPSSTransactionStatus(response["status"]),
            sender_account=response["sender_account"],
            sender_name=response["sender_name"],
            sender_bank=response["sender_bank"],
            recipient_account=response["recipient_account"],
            recipient_name=response["recipient_name"],
            recipient_bank=response["recipient_bank"],
            description=response.get("description", ""),
            created_at=datetime.fromisoformat(response["created_at"]),
            updated_at=datetime.fromisoformat(response["updated_at"]),
            metadata=response
        )
    
    async def get_account_balance(self, account_number: Optional[str] = None) -> GhIPSSBalance:
        """Get account balance."""
        account = account_number or self.config.account_number
        
        response = await asyncio.to_thread(
            self._make_request, "GET", f"accounts/{account}/balance"
        )
        
        return GhIPSSBalance(
            account_number=account,
            available_balance=response["available_balance"],
            ledger_balance=response["ledger_balance"],
            currency=response["currency"],
            last_updated=datetime.fromisoformat(response["last_updated"])
        )
    
    async def get_account_statement(self, account_number: Optional[str] = None,
                                   start_date: Optional[datetime] = None,
                                   end_date: Optional[datetime] = None) -> GhIPSSStatement:
        """Get account statement."""
        account = account_number or self.config.account_number
        
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        params = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
        
        response = await asyncio.to_thread(
            self._make_request, "GET", f"accounts/{account}/statement", params=params
        )
        
        transactions = []
        for tx_data in response["transactions"]:
            transactions.append(GhIPSSTransaction(
                transaction_id=tx_data["transaction_id"],
                reference=tx_data["reference"],
                amount=tx_data["amount"],
                currency=tx_data["currency"],
                transaction_type=GhIPSSTransactionType(tx_data["transaction_type"]),
                status=GhIPSSTransactionStatus(tx_data["status"]),
                sender_account=tx_data["sender_account"],
                sender_name=tx_data["sender_name"],
                sender_bank=tx_data["sender_bank"],
                recipient_account=tx_data["recipient_account"],
                recipient_name=tx_data["recipient_name"],
                recipient_bank=tx_data["recipient_bank"],
                description=tx_data.get("description", ""),
                created_at=datetime.fromisoformat(tx_data["created_at"]),
                updated_at=datetime.fromisoformat(tx_data["updated_at"]),
                metadata=tx_data
            ))
        
        return GhIPSSStatement(
            account_number=account,
            start_date=start_date,
            end_date=end_date,
            transactions=transactions,
            opening_balance=response["opening_balance"],
            closing_balance=response["closing_balance"],
            currency=response["currency"]
        )
    
    async def validate_account(self, account_number: str, bank_code: str) -> Dict[str, Any]:
        """Validate account number and bank code."""
        data = {
            "account_number": account_number,
            "bank_code": bank_code
        }
        
        return await asyncio.to_thread(
            self._make_request, "POST", "accounts/validate", data
        )
    
    async def get_bank_list(self) -> List[Dict[str, Any]]:
        """Get list of participating banks."""
        response = await asyncio.to_thread(
            self._make_request, "GET", "banks"
        )
        
        return response["banks"]
    
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
    
    async def reverse_transaction(self, transaction_id: str, reason: str = "") -> bool:
        """Reverse a completed transaction."""
        data = {"reason": reason} if reason else {}
        
        try:
            await asyncio.to_thread(
                self._make_request, "POST", f"transactions/{transaction_id}/reverse", data
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to reverse transaction {transaction_id}: {e}")
            return False
    
    async def get_transaction_history(self, account_number: Optional[str] = None,
                                     start_date: Optional[datetime] = None,
                                     end_date: Optional[datetime] = None,
                                     limit: int = 100) -> List[GhIPSSTransaction]:
        """Get transaction history."""
        account = account_number or self.config.account_number
        
        params = {"limit": limit}
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()
        
        response = await asyncio.to_thread(
            self._make_request, "GET", f"accounts/{account}/transactions", params=params
        )
        
        transactions = []
        for tx_data in response["transactions"]:
            transactions.append(GhIPSSTransaction(
                transaction_id=tx_data["transaction_id"],
                reference=tx_data["reference"],
                amount=tx_data["amount"],
                currency=tx_data["currency"],
                transaction_type=GhIPSSTransactionType(tx_data["transaction_type"]),
                status=GhIPSSTransactionStatus(tx_data["status"]),
                sender_account=tx_data["sender_account"],
                sender_name=tx_data["sender_name"],
                sender_bank=tx_data["sender_bank"],
                recipient_account=tx_data["recipient_account"],
                recipient_name=tx_data["recipient_name"],
                recipient_bank=tx_data["recipient_bank"],
                description=tx_data.get("description", ""),
                created_at=datetime.fromisoformat(tx_data["created_at"]),
                updated_at=datetime.fromisoformat(tx_data["updated_at"]),
                metadata=tx_data
            ))
        
        return transactions
    
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
