"""
Payment Service for KasaAI Core Backend.

Handles payment processing, wallet management, and transaction tracking
for multiple payment methods including Mobile Money (MoMo).
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from uuid import UUID
from decimal import Decimal
import httpx
from pydantic import BaseModel

from ..models import EventRecord
from ..events import EventBus, EventType
from ..mcp import get_mcp_manager

logger = logging.getLogger(__name__)

class PaymentMethod(BaseModel):
    """Payment method configuration."""
    id: str
    name: str
    type: str  # "card", "bank_transfer", "mobile_money", "crypto"
    provider: str  # "stripe", "paypal", "momo", "mpesa", etc.
    is_active: bool = True
    config: Dict[str, Any] = {}
    supported_currencies: List[str] = ["USD"]
    min_amount: Decimal = Decimal("0.01")
    max_amount: Decimal = Decimal("10000.00")
    processing_fee_percent: Decimal = Decimal("0.00")
    processing_fee_fixed: Decimal = Decimal("0.00")

class Wallet(BaseModel):
    """User wallet for storing funds."""
    tenant_id: UUID
    balance: Decimal = Decimal("0.00")
    currency: str = "USD"
    last_updated: datetime
    is_active: bool = True

class Transaction(BaseModel):
    """Payment transaction record."""
    id: str
    tenant_id: UUID
    amount: Decimal
    currency: str = "USD"
    payment_method: str
    status: str  # "pending", "processing", "completed", "failed", "refunded"
    transaction_type: str  # "deposit", "withdrawal", "usage_charge"
    reference: Optional[str] = None
    description: Optional[str] = None
    metadata: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

class PaymentService:
    """Service for handling payments and wallet management."""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.mcp_manager = get_mcp_manager()
        
        # Supported payment methods
        self.payment_methods = {
            "stripe_card": PaymentMethod(
                id="stripe_card",
                name="Credit/Debit Card",
                type="card",
                provider="stripe",
                is_active=True,
                config={
                    "publishable_key": "pk_test_...",
                    "secret_key": "sk_test_...",
                },
                supported_currencies=["USD", "EUR", "GBP"],
                processing_fee_percent=Decimal("2.9"),
                processing_fee_fixed=Decimal("0.30")
            ),
            "paypal": PaymentMethod(
                id="paypal",
                name="PayPal",
                type="digital_wallet",
                provider="paypal",
                is_active=True,
                config={
                    "client_id": "client_id_...",
                    "client_secret": "client_secret_...",
                },
                supported_currencies=["USD", "EUR", "GBP"],
                processing_fee_percent=Decimal("2.9"),
                processing_fee_fixed=Decimal("0.30")
            ),
            "momo_ghana": PaymentMethod(
                id="momo_ghana",
                name="Mobile Money (Ghana)",
                type="mobile_money",
                provider="momo",
                is_active=True,
                config={
                    "merchant_id": "merchant_id_...",
                    "api_key": "api_key_...",
                    "environment": "sandbox",  # or "production"
                    "callback_url": "https://api.kasaai.com/webhooks/momo",
                },
                supported_currencies=["GHS"],
                min_amount=Decimal("1.00"),
                max_amount=Decimal("5000.00"),
                processing_fee_percent=Decimal("1.5"),
                processing_fee_fixed=Decimal("0.10")
            ),
            "momo_kenya": PaymentMethod(
                id="momo_kenya",
                name="M-Pesa (Kenya)",
                type="mobile_money",
                provider="mpesa",
                is_active=True,
                config={
                    "consumer_key": "consumer_key_...",
                    "consumer_secret": "consumer_secret_...",
                    "environment": "sandbox",
                    "callback_url": "https://api.kasaai.com/webhooks/mpesa",
                },
                supported_currencies=["KES"],
                min_amount=Decimal("10.00"),
                max_amount=Decimal("70000.00"),
                processing_fee_percent=Decimal("1.0"),
                processing_fee_fixed=Decimal("0.00")
            ),
            "momo_nigeria": PaymentMethod(
                id="momo_nigeria",
                name="Paga (Nigeria)",
                type="mobile_money",
                provider="paga",
                is_active=True,
                config={
                    "api_key": "api_key_...",
                    "merchant_id": "merchant_id_...",
                    "environment": "sandbox",
                    "callback_url": "https://api.kasaai.com/webhooks/paga",
                },
                supported_currencies=["NGN"],
                min_amount=Decimal("100.00"),
                max_amount=Decimal("100000.00"),
                processing_fee_percent=Decimal("2.0"),
                processing_fee_fixed=Decimal("0.00")
            ),
        }
    
    async def get_available_payment_methods(self, tenant_id: UUID, currency: str = "USD") -> List[PaymentMethod]:
        """
        Get available payment methods for a tenant.
        
        Args:
            tenant_id: Tenant ID
            currency: Preferred currency
            
        Returns:
            List of available payment methods
        """
        available_methods = []
        
        for method in self.payment_methods.values():
            if not method.is_active:
                continue
                
            if currency not in method.supported_currencies:
                continue
                
            # Check if tenant has access to this payment method
            # In a real implementation, this would check tenant-specific settings
            available_methods.append(method)
        
        return available_methods
    
    async def create_deposit_transaction(
        self,
        tenant_id: UUID,
        amount: Decimal,
        currency: str,
        payment_method_id: str,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Transaction:
        """
        Create a deposit transaction.
        
        Args:
            tenant_id: Tenant ID
            amount: Amount to deposit
            currency: Currency code
            payment_method_id: Payment method ID
            description: Transaction description
            metadata: Additional metadata
            
        Returns:
            Created transaction
        """
        if payment_method_id not in self.payment_methods:
            raise ValueError(f"Unsupported payment method: {payment_method_id}")
        
        payment_method = self.payment_methods[payment_method_id]
        
        # Validate amount
        if amount < payment_method.min_amount:
            raise ValueError(f"Amount {amount} is below minimum {payment_method.min_amount}")
        if amount > payment_method.max_amount:
            raise ValueError(f"Amount {amount} exceeds maximum {payment_method.max_amount}")
        
        # Calculate fees
        processing_fee = (amount * payment_method.processing_fee_percent / Decimal("100")) + payment_method.processing_fee_fixed
        total_amount = amount + processing_fee
        
        # Create transaction
        transaction_id = f"txn_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hash(str(tenant_id))}"
        
        transaction = Transaction(
            id=transaction_id,
            tenant_id=tenant_id,
            amount=amount,
            currency=currency,
            payment_method=payment_method_id,
            status="pending",
            transaction_type="deposit",
            description=description or f"Wallet deposit via {payment_method.name}",
            metadata={
                "processing_fee": float(processing_fee),
                "total_amount": float(total_amount),
                "payment_method_config": payment_method.config,
                **(metadata or {})
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Emit event
        await self.event_bus.emit(EventType.PAYMENT_INITIATED, {
            "transaction_id": transaction_id,
            "tenant_id": str(tenant_id),
            "amount": float(amount),
            "currency": currency,
            "payment_method": payment_method_id,
            "status": "pending"
        })
        
        logger.info(f"Created deposit transaction {transaction_id} for tenant {tenant_id}")
        return transaction
    
    async def process_mobile_money_payment(
        self,
        transaction: Transaction,
        phone_number: str,
        provider: str
    ) -> Dict[str, Any]:
        """
        Process mobile money payment.
        
        Args:
            transaction: Transaction to process
            phone_number: Customer phone number
            provider: Mobile money provider (momo, mpesa, paga)
            
        Returns:
            Payment processing result
        """
        try:
            # Use MCP to process payment
            payment_result = await self.mcp_manager.process_payment(
                provider=provider,
                amount=float(transaction.amount),
                currency=transaction.currency,
                phone_number=phone_number,
                reference=transaction.id,
                callback_url=transaction.metadata.get("callback_url"),
                metadata={
                    "transaction_id": transaction.id,
                    "tenant_id": str(transaction.tenant_id),
                    "payment_method": transaction.payment_method
                }
            )
            
            # Update transaction status
            transaction.status = "processing"
            transaction.updated_at = datetime.utcnow()
            transaction.metadata.update({
                "payment_provider_response": payment_result,
                "phone_number": phone_number,
                "provider": provider
            })
            
            # Emit event
            await self.event_bus.emit(EventType.PAYMENT_PROCESSED, {
                "transaction_id": transaction.id,
                "tenant_id": str(transaction.tenant_id),
                "amount": float(transaction.amount),
                "currency": transaction.currency,
                "payment_method": transaction.payment_method,
                "status": "processing",
                "provider_response": payment_result
            })
            
            logger.info(f"Processing mobile money payment for transaction {transaction.id}")
            return {
                "success": True,
                "transaction_id": transaction.id,
                "status": "processing",
                "provider_response": payment_result
            }
            
        except Exception as e:
            logger.error(f"Failed to process mobile money payment: {str(e)}")
            transaction.status = "failed"
            transaction.updated_at = datetime.utcnow()
            transaction.metadata["error"] = str(e)
            
            # Emit error event
            await self.event_bus.emit(EventType.PAYMENT_FAILED, {
                "transaction_id": transaction.id,
                "tenant_id": str(transaction.tenant_id),
                "error": str(e)
            })
            
            return {
                "success": False,
                "transaction_id": transaction.id,
                "status": "failed",
                "error": str(e)
            }
    
    async def process_webhook(
        self,
        provider: str,
        payload: Dict[str, Any],
        signature: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process payment webhook from provider.
        
        Args:
            provider: Payment provider
            payload: Webhook payload
            signature: Webhook signature for verification
            
        Returns:
            Processing result
        """
        try:
            # Verify webhook signature if provided
            if signature and not await self._verify_webhook_signature(provider, payload, signature):
                logger.warning(f"Invalid webhook signature from {provider}")
                return {"success": False, "error": "Invalid signature"}
            
            # Extract transaction information
            transaction_id = payload.get("reference") or payload.get("transaction_id")
            if not transaction_id:
                logger.error(f"No transaction ID in {provider} webhook")
                return {"success": False, "error": "No transaction ID"}
            
            status = payload.get("status", "unknown")
            
            # Update transaction status
            # In a real implementation, this would update the database
            if status in ["success", "completed"]:
                await self._complete_transaction(transaction_id, payload)
            elif status in ["failed", "cancelled"]:
                await self._fail_transaction(transaction_id, payload)
            
            # Emit event
            await self.event_bus.emit(EventType.PAYMENT_WEBHOOK_RECEIVED, {
                "provider": provider,
                "transaction_id": transaction_id,
                "status": status,
                "payload": payload
            })
            
            logger.info(f"Processed {provider} webhook for transaction {transaction_id}")
            return {"success": True, "transaction_id": transaction_id}
            
        except Exception as e:
            logger.error(f"Failed to process {provider} webhook: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _complete_transaction(self, transaction_id: str, payload: Dict[str, Any]):
        """Complete a successful transaction."""
        # In a real implementation, this would:
        # 1. Update transaction status in database
        # 2. Add funds to user wallet
        # 3. Send confirmation email/SMS
        
        logger.info(f"Completing transaction {transaction_id}")
        
        # Emit completion event
        await self.event_bus.emit(EventType.PAYMENT_COMPLETED, {
            "transaction_id": transaction_id,
            "payload": payload
        })
    
    async def _fail_transaction(self, transaction_id: str, payload: Dict[str, Any]):
        """Mark a transaction as failed."""
        logger.info(f"Failing transaction {transaction_id}")
        
        # Emit failure event
        await self.event_bus.emit(EventType.PAYMENT_FAILED, {
            "transaction_id": transaction_id,
            "payload": payload
        })
    
    async def _verify_webhook_signature(self, provider: str, payload: Dict[str, Any], signature: str) -> bool:
        """Verify webhook signature."""
        # In a real implementation, this would verify the signature
        # using the provider's public key or secret
        return True  # Placeholder
    
    async def get_wallet_balance(self, tenant_id: UUID) -> Wallet:
        """
        Get wallet balance for a tenant.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            Wallet information
        """
        # In a real implementation, this would query the database
        return Wallet(
            tenant_id=tenant_id,
            balance=Decimal("150.75"),
            currency="USD",
            last_updated=datetime.utcnow(),
            is_active=True
        )
    
    async def charge_wallet(
        self,
        tenant_id: UUID,
        amount: Decimal,
        currency: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Charge wallet for usage.
        
        Args:
            tenant_id: Tenant ID
            amount: Amount to charge
            currency: Currency code
            description: Charge description
            metadata: Additional metadata
            
        Returns:
            True if charge successful, False otherwise
        """
        try:
            # In a real implementation, this would:
            # 1. Check wallet balance
            # 2. Deduct amount if sufficient funds
            # 3. Create transaction record
            # 4. Emit events
            
            logger.info(f"Charging wallet {amount} {currency} for tenant {tenant_id}")
            
            # Emit charge event
            await self.event_bus.emit(EventType.WALLET_CHARGED, {
                "tenant_id": str(tenant_id),
                "amount": float(amount),
                "currency": currency,
                "description": description,
                "metadata": metadata or {}
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to charge wallet: {str(e)}")
            return False 